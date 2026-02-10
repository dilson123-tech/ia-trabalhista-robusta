#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8099}"

curl_json () {
  curl -fsS \
    --connect-timeout 2 --max-time 6 \
    --retry 3 --retry-connrefused --retry-delay 0 \
    "$1"
}

assert_json () {
  local label="$1"
  local url="$2"

  echo "== SMOKE: $label =="
  local resp
  resp="$(curl_json "$url")" || { echo "ERRO ❌ curl falhou em: $url"; exit 2; }

  # considera vazio/whitespace como erro
  if [[ -z "${resp//[[:space:]]/}" ]]; then
    echo "ERRO ❌ resposta vazia/whitespace em: $url"
    exit 3
  fi

  printf '%s' "$resp" | python -c '
import json,sys
raw=sys.stdin.read()
try:
    d=json.loads(raw)
except Exception as e:
    print("ERRO ❌ JSON inválido:", e)
    print("RAW:", raw[:500])
    raise
assert d.get("ok") is True, d
assert d.get("service")=="ia_trabalhista_robusta", d
print("OK ✅", d)
'
}

assert_json "root health" "$BASE_URL/health"
echo
assert_json "v1 health" "$BASE_URL/api/v1/health"
echo
echo "✅ SMOKE PASS"
