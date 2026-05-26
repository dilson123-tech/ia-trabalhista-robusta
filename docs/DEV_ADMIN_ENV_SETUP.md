# DEV ADMIN ENV SETUP

## Problema comum

Backend local sobe normalmente, mas rotas administrativas retornam:

- HTTP 500
- "ADMIN_API_KEY(S) não configurada(s) no ambiente."

Isso acontece porque os endpoints admin utilizam:

- ADMIN_API_KEY
ou
- ADMIN_API_KEYS

via variável de ambiente.

## Configuração mínima local

Adicionar no arquivo `.env` na raiz do projeto:

ADMIN_API_KEY="dev-admin-key-local"

Opcionalmente:

ADMIN_API_KEYS="dev-key-1,dev-key-2"

## Header obrigatório

As rotas admin exigem:

X-Admin-Key: dev-admin-key-local

## Exemplo curl

curl -H "X-Admin-Key: dev-admin-key-local" \
  http://127.0.0.1:8099/api/v1/admin/tenants

## Observações

- `settings.py` já carrega `.env` automaticamente via `SettingsConfigDict`.
- O problema normalmente ocorre por ausência da variável no `.env`.
- Não subir produção usando `CHANGE_ME_ADMIN_KEY`.
