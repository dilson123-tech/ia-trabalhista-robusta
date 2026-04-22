# MVP VALIDATION MATRIX — IA Trabalhista Robusta

Legenda:
- [ ] Não validado
- [~] Parcial
- [x] Validado

## 1) Health / readiness / operação
- [x] GET /health -> 200
- [x] GET /ready -> 200 com banco ok
- [x] smoke principal executando sem falhas graves
- [x] comportamento validado quando banco estiver indisponível

## 2) Auth
- [x] login válido -> 200
- [x] whoami com token válido -> 200
- [x] whoami sem token -> 401/403 validado
- [x] login inválido -> erro validado
- [x] seed-admin desabilitado em ambiente sem flag -> validado
- [x] create_user admin-only -> permissão validada
- [x] activate/deactivate respeitando tenant -> validado

## 3) Tenant isolation
- [x] case por tenant no fluxo principal
- [x] case_analysis por tenant no fluxo principal
- [x] acesso cruzado entre tenants bloqueado em GET /cases/{id}
- [x] acesso cruzado bloqueado em /analysis
- [x] acesso cruzado bloqueado em /executive-report
- [x] acesso cruzado bloqueado em /executive-pdf

## 4) Casos
- [x] criar caso -> 200
- [x] listar casos -> 200
- [x] obter caso por id -> 200
- [x] obter case inexistente -> 404
- [x] idempotência por case_number validada formalmente

## 5) Análise
- [x] gerar análise -> 200
- [x] persistir análise -> validado
- [x] reexecução idempotente -> validada formalmente
- [x] case inexistente -> 404
- [x] tenant errado -> bloqueado

## 6) Executive summary / report / PDF
- [x] executive-summary -> 200
- [x] executive-report -> 200
- [x] executive-pdf -> 200
- [x] PDF reconhecido como application/pdf
- [x] risco exibido como Baixo/Médio/Alto
- [x] case inexistente -> 404
- [x] tenant errado -> bloqueado
- [x] sem análise prévia -> comportamento validado
- [x] erro interno de geração PDF -> comportamento validado/documentado

## 7) Usage / limits / plans
- [x] usage summary -> 200
- [x] usage summary v2 -> 200
- [x] limite de case_create estourado -> comportamento validado
- [x] limite de ai_analysis_create estourado -> comportamento validado
- [x] plano trial -> comportamento validado
- [x] plano canceled -> comportamento validado

## 8) Admin global
- [x] admin audit logs -> funcional
- [x] admin dashboard summary -> funcional
- [x] admin subscription upsert -> funcional
- [x] admin sem X-Admin-Key -> bloqueado corretamente
- [x] admin com key inválida -> bloqueado corretamente
- [x] reset de contexto tenant após operação admin -> validado formalmente

## 9) Release gate
- [ ] todos os fluxos críticos validados
- [ ] todos os cenários críticos de erro validados
- [ ] sem falhas abertas graves
- [x] CORS por ambiente validado em production-like
- [x] docs/openapi fechados em production-like
- [x] fail-fast de configuração production-like validado
