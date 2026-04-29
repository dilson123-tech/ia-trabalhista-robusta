# Handoff Final de Produção — 2026-04-28

## Projeto
IA Trabalhista Robusta

## Natureza do produto
Produto real para venda/comercialização. Não é projeto de estudo.

## Estado atual
- Backend em produção saudável (`/health` OK)
- Painel principal refinado e separado entre Produção e Gestão comercial
- Asaas produção configurado
- Webhook de produção ativo e respondendo 200
- Fluxo interno de billing validado ponta a ponta
- Migration oficial para `validation_test` criada e mergeada
- Banco oficial novo do projeto configurado

## Banco oficial
- Serviço oficial do banco: `Postgres-CLzE - trabalhista`
- Serviço oficial da aplicação: `ia-trabalhista-robusta`

## O que foi validado
1. Conta real do Asaas criada e aprovada
2. Chave de produção configurada no Railway
3. `ASAAS_BASE_URL` ajustado para produção
4. Webhook real configurado e ativado
5. Cobrança real manual validada no Asaas
6. Cobrança real criada pelo próprio sistema validada
7. Pagamento Pix real confirmado
8. Webhook baixando automaticamente a `billing_request`
9. `validation_test` não altera assinatura do tenant
10. Migration da constraint de `billing_reason` aplicada e mergeada

## Fluxo validado
`billing_request -> checkout Asaas -> pagamento Pix -> webhook -> status paid`

## Tenant de teste criado em produção
- `tenant_id = 1`
- plano: `basic`
- status: `trial`

## Billing request de teste validada
- `billing_request.id = 2`
- `billing_reason = validation_test`
- `status = paid`

## PRs recentes relevantes
- #109 — refactor(frontend): separate commercial workspace and refine panel visuals
- #110 — feat(billing): add validation test billing flow
- #111 — fix(billing): add migration for validation_test billing reason

## Pendências controladas
1. Girar a credencial pública do Postgres que apareceu durante o suporte
2. Opcional: limpar tenant e cobrança de teste depois
3. Opcional: consolidar este handoff dentro do runbook principal

## Alertas importantes
- Não voltar a apontar o `DATABASE_URL` para bancos antigos (`Postgres-OWgV` ou `Postgres-Va00`)
- O banco correto do IA Trabalhista é o `Postgres-CLzE - trabalhista`
- Não usar `ASAAS_BASE_URL` de sandbox com chave de produção

## Régua final
- Funcional do ciclo: 100%
- Blindagem operacional final: 98%

## Próximos melhores passos
1. Girar credencial do Postgres
2. Validar `/health` após rotação
3. Limpar dados de teste se necessário
4. Seguir evolução comercial / billing real no painel
