#!/usr/bin/env bash
set -euo pipefail

# Contract: SaaS limits (cases + AI) must enforce 402 when exceeded
# Uses AUTH_ENABLED=false (dev admin tenant_id=1), so it is deterministic.

PORT="${PORT:-18099}"
BASE="http://127.0.0.1:${PORT}"
API="${BASE}/api/v1"
RUN_ID="$(date +%s)"

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_DIR="$(cd "${BACKEND_DIR}/.." && pwd)"
LOG="/tmp/ia_trabalhista_contract_${RUN_ID}.log"

reset_usage_counters() {
  # Determinismo: limpa usage_counters do tenant 1 no mês atual.
  # - Local dev: tenta docker exec no container ia_trabalhista_db
  # - CI: usa psql se disponível
  if [ "${SKIP_DB_RESET:-0}" = "1" ]; then
    echo "[contract] SKIP_DB_RESET=1 -> skipping reset"
    return 0
  fi

  echo "[contract] resetting usage_counters for tenant 1 (current month)..."
  if command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' | grep -Eq '^ia_trabalhista_db$'; then
    docker exec -i ia_trabalhista_db psql -U ia_app_runtime -d ia_trabalhista -v ON_ERROR_STOP=1 -c "SELECT set_config('app.tenant_id','1',false); DELETE FROM usage_counters WHERE tenant_id=1 AND month = date_trunc('month', now())::date;" >/dev/null
    return 0
  fi

  if command -v psql >/dev/null 2>&1; then
    # Usa DATABASE_URL do env se existir, senão tenta localhost padrão
    if [ -n "${DATABASE_URL:-}" ]; then
      # SQLAlchemy URL -> psql precisa de libpq URL. Se já for postgres://, ok. Se for postgresql+psycopg2://, converte.
      PSQL_URL="${DATABASE_URL/postgresql+psycopg2:\/\//postgresql:\/\/}"
      psql "${PSQL_URL}" -v ON_ERROR_STOP=1 -c "SELECT set_config('app.tenant_id','1',false); DELETE FROM usage_counters WHERE tenant_id=1 AND month = date_trunc('month', now())::date;" >/dev/null
    else
      psql "postgresql://ia_trab_user:ia_trab_pass@localhost:5432/ia_trab" -v ON_ERROR_STOP=1 -c "SELECT set_config('app.tenant_id','1',false); DELETE FROM usage_counters WHERE tenant_id=1 AND month = date_trunc('month', now())::date;" >/dev/null
    fi
    return 0
  fi

  echo "[contract] WARN: could not reset usage_counters (no docker/psql)."
}

echo "[contract] repo=${REPO_DIR}"
echo "[contract] backend=${BACKEND_DIR}"
echo "[contract] port=${PORT}"
echo "[contract] log=${LOG}"

# Ensure DB container is running (best-effort)
# Local dev may use docker container ia_trabalhista_db; CI uses postgres service.
if command -v docker >/dev/null 2>&1; then
  if docker ps -a --format '{{.Names}}' | grep -Eq '^ia_trabalhista_db$'; then
    if ! docker ps --format '{{.Names}}' | grep -Eq '^ia_trabalhista_db$'; then
      echo "[contract] starting docker container ia_trabalhista_db..."
      docker start ia_trabalhista_db >/dev/null || true
      sleep 1
    fi
  fi
fi

# Start API
echo "[contract] starting uvicorn..."
cd "${REPO_DIR}"
# shellcheck disable=SC1091
source .venv/bin/activate
cd "${BACKEND_DIR}"

AUTH_ENABLED=false \
PLAN_BASIC_CASES_PER_MONTH=2 \
PLAN_BASIC_AI_ANALYSES_PER_MONTH=1 \
uvicorn app.main:app --port "${PORT}" --log-level warning >"${LOG}" 2>&1 &
PID=$!

cleanup() {
  if ps -p "${PID}" >/dev/null 2>&1; then
    kill "${PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

# Wait for server
echo "[contract] waiting for server..."
ok=0
for _ in $(seq 1 80); do
  if curl -fsS "${BASE}/openapi.json" >/dev/null 2>&1; then
    ok=1; break
  fi
  sleep 0.2
done
if [ "${ok}" -ne 1 ]; then
  echo "[contract] server did not start. tail log:"
  tail -n 80 "${LOG}" || true
  exit 1
fi

mk_payload() {
  local n="$1"
  cat <<JSON
{"case_number":"SaaS-${RUN_ID}-${n}","title":"Teste ${n}","description":"Contrato","status":"open"}
JSON
}

echo "[contract] create 2 cases (expect 200)..."

case1_out="/tmp/contract_case1_${RUN_ID}.json"
case2_out="/tmp/contract_case2_${RUN_ID}.json"

CODE1="$(curl -sS -o "${case1_out}" -w "%{http_code}" \
  -X POST "${API}/cases" -H "Content-Type: application/json" -d "$(mk_payload 1)")"
if [ "${CODE1}" != "200" ]; then
  echo "[contract] FAIL: expected 200 on case1, got ${CODE1}"
  cat "${case1_out}" || true
  echo "[contract] tail log:"
  tail -n 120 "${LOG}" || true
  exit 1
fi
ID1="$(jq -r '.id' < "${case1_out}")"

CODE2="$(curl -sS -o "${case2_out}" -w "%{http_code}" \
  -X POST "${API}/cases" -H "Content-Type: application/json" -d "$(mk_payload 2)")"
if [ "${CODE2}" != "200" ]; then
  echo "[contract] FAIL: expected 200 on case2, got ${CODE2}"
  cat "${case2_out}" || true
  echo "[contract] tail log:"
  tail -n 120 "${LOG}" || true
  exit 1
fi
ID2="$(jq -r '.id' < "${case2_out}")"

echo "[contract] ids: ${ID1}, ${ID2}"

echo "[contract] create 3rd case (expect 402)..."
CODE3="$(curl -sS -o /tmp/contract_case3_${RUN_ID}.json -w "%{http_code}" \
  -X POST "${API}/cases" -H "Content-Type: application/json" -d "$(mk_payload 3)")"
if [ "${CODE3}" != "402" ]; then
  echo "[contract] FAIL: expected 402 on 3rd case, got ${CODE3}"
  cat /tmp/contract_case3_${RUN_ID}.json || true
  exit 1
fi

echo "[contract] executive-pdf for case1 (expect 200)..."
CODE_PDF1="$(curl -sS -o /dev/null -w "%{http_code}" "${API}/cases/${ID1}/executive-pdf")"
if [ "${CODE_PDF1}" != "200" ]; then
  echo "[contract] FAIL: expected 200 on executive-pdf case1, got ${CODE_PDF1}"
  tail -n 80 "${LOG}" || true
  exit 1
fi

echo "[contract] executive-pdf for case2 (expect 402 due AI limit)..."
CODE_PDF2="$(curl -sS -o /dev/null -w "%{http_code}" "${API}/cases/${ID2}/executive-pdf")"
if [ "${CODE_PDF2}" != "402" ]; then
  echo "[contract] FAIL: expected 402 on executive-pdf case2, got ${CODE_PDF2}"
  tail -n 80 "${LOG}" || true
  exit 1
fi

echo "[contract] usage summary v2 checks..."
S="$(curl -fsS "${API}/usage/summary-v2")"

# Assertions
jq -e '.limits.cases_per_month == 2' >/dev/null <<<"${S}"
jq -e '.limits.ai_analyses_per_month == 1' >/dev/null <<<"${S}"
jq -e '.used.cases_created == 2' >/dev/null <<<"${S}"
jq -e '.used.ai_analyses_generated == 1' >/dev/null <<<"${S}"
jq -e '.remaining.cases == 0' >/dev/null <<<"${S}"
jq -e '.remaining.ai_analyses == 0' >/dev/null <<<"${S}"

echo "[contract] ✅ PASS (cases+AI limits enforced, summary ok)"
