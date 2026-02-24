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

echo "[contract] repo=${REPO_DIR}"
echo "[contract] backend=${BACKEND_DIR}"
echo "[contract] port=${PORT}"
echo "[contract] log=${LOG}"

# Ensure DB container is running (best-effort)
if command -v docker >/dev/null 2>&1; then
  if ! docker ps --format '{{.Names}}' | rg -q '^ia_trabalhista_db$'; then
    echo "[contract] starting docker container ia_trabalhista_db..."
    docker start ia_trabalhista_db >/dev/null
    sleep 1
    echo "[contract] resetting usage_counters for tenant 1 (current month)..."
    docker exec -i ia_trabalhista_db psql -U ia_app_runtime -d ia_trabalhista -v ON_ERROR_STOP=1 -c "SELECT set_config('app.tenant_id','1',false); DELETE FROM usage_counters WHERE tenant_id=1 AND month = date_trunc('month', now())::date;" >/dev/null
  fi
fi


# Reset usage_counters for deterministic runs (tenant 1 / current month)
echo "[contract] resetting usage_counters for tenant 1 (current month)..."
docker exec -i ia_trabalhista_db psql -U ia_app_runtime -d ia_trabalhista -v ON_ERROR_STOP=1 -c "SELECT set_config('app.tenant_id','1',false); DELETE FROM usage_counters WHERE tenant_id=1 AND month = date_trunc('month', now())::date;" >/dev/null

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
R1="$(curl -fsS -X POST "${API}/cases" -H "Content-Type: application/json" -d "$(mk_payload 1)")"
ID1="$(jq -r '.id' <<<"${R1}")"
R2="$(curl -fsS -X POST "${API}/cases" -H "Content-Type: application/json" -d "$(mk_payload 2)")"
ID2="$(jq -r '.id' <<<"${R2}")"
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
