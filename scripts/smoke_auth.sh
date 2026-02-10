#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8099}"
SEED_TOKEN="${SEED_TOKEN:-CHANGE_ME_SEED_TOKEN}"
ADMIN_USER="${ADMIN_USER:-admin}"
ADMIN_PASS="${ADMIN_PASS:-admin123}"

req() {
  local method="$1"; shift
  local url="$1"; shift

  local tmp code
  tmp="$(mktemp)"
  code="$(curl -sS -o "$tmp" -w "%{http_code}" -X "$method" "$url" "$@")"

  echo "HTTP $code"
  cat "$tmp"; echo
  rm -f "$tmp"

  [[ "$code" == "200" ]] || return 1
}

seed_payload="$(python - <<'PY'
import os, json
print(json.dumps({
  "username": os.environ.get("ADMIN_USER","admin"),
  "password": os.environ.get("ADMIN_PASS","admin123"),
  "role": "admin"
}))
PY
)"

login_payload="$(python - <<'PY'
import os, json
print(json.dumps({
  "username": os.environ.get("ADMIN_USER","admin"),
  "password": os.environ.get("ADMIN_PASS","admin123"),
}))
PY
)"

echo "== SMOKE AUTH: seed-admin =="
req POST "$BASE_URL/api/v1/auth/seed-admin" \
  -H 'Content-Type: application/json' \
  -H "X-Seed-Token: $SEED_TOKEN" \
  -d "$seed_payload"

echo "== SMOKE AUTH: login =="
login_resp="$(mktemp)"
code="$(curl -sS -o "$login_resp" -w "%{http_code}" -X POST "$BASE_URL/api/v1/auth/login" \
  -H 'Content-Type: application/json' \
  -d "$login_payload")"
echo "HTTP $code"
cat "$login_resp"; echo
[[ "$code" == "200" ]] || exit 1

TOKEN="$(python -c 'import json,sys; print(json.load(sys.stdin)["access_token"])' <"$login_resp")"
rm -f "$login_resp"

echo "TOKEN_LEN=${#TOKEN}"

echo "== SMOKE AUTH: whoami =="
req GET "$BASE_URL/api/v1/auth/whoami" \
  -H "Authorization: Bearer $TOKEN"

echo "== SMOKE AUTH: admin-only =="
req GET "$BASE_URL/api/v1/auth/admin-only" \
  -H "Authorization: Bearer $TOKEN"

echo "✅ SMOKE AUTH PASS"
