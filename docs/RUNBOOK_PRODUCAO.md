# RUNBOOK DE PRODUÇÃO — IA Trabalhista Robusta

## Objetivo
Este runbook define o procedimento padrão de diagnóstico, contenção, validação e recuperação de incidentes no ambiente do projeto **IA Trabalhista Robusta**.

Princípios:
- agir primeiro no diagnóstico objetivo
- evitar mudanças grandes durante incidente
- registrar evidências antes de alterar comportamento
- separar falha de aplicação, autenticação, banco, infraestrutura e dados
- priorizar rollback seguro sobre correções apressadas em produção

---

## Escopo
Este documento cobre incidentes relacionados a:
- indisponibilidade da API
- falhas de autenticação/autorização
- falhas de conexão com banco
- erros 500
- falhas em geração de executive summary / report / PDF
- degradação operacional após deploy
- necessidade de rollback inicial

---

## Referências do projeto
- Repositório: `~/projetos/ia_trabalhista_robusta`
- Backend: `~/projetos/ia_trabalhista_robusta/backend`
- Documentos relacionados:
  - `README.md`
  - `MVP_VALIDATION_MATRIX.md`
  - `RELEASE_CHECKLIST_MVP.md`
  - `docs/PROJECT_RULES.md`
  - `docs/ROADMAP.md`

---

## Regra de ouro de debug
Ordem obrigatória:
1. capturar request/response/status
2. validar health/readiness
3. verificar autenticação separadamente
4. verificar banco separadamente
5. reproduzir com curl
6. consultar logs
7. só então aplicar micropatch
8. validar imediatamente após a mudança

Nunca começar alterando frontend ou múltiplos arquivos sem isolar a causa.

---

## Sintomas mais comuns e triagem rápida

### 1. API fora do ar
Sinais:
- timeout
- conexão recusada
- health não responde
- 502/503 via proxy

Checagem inicial:
```bash
cd ~/projetos/ia_trabalhista_robusta/backend && curl -i http://127.0.0.1:8099/healthz
```

Interpretação:
- `200`: aplicação respondeu; seguir para auth, banco ou rota específica
- timeout/refused: processo não está rodando ou há problema de bind/porta
- `500`: app subiu, mas internamente está quebrada

### 2. Readiness falhando
Sinais:
- `/healthz` pode responder
- `/ready` falha
- sintomas de dependência indisponível, especialmente banco

Checagem:
```bash
cd ~/projetos/ia_trabalhista_robusta/backend && curl -i http://127.0.0.1:8099/ready
```

Interpretação:
- `200`: dependências críticas ok
- `503` ou `500`: suspeita principal em banco/configuração/variável de ambiente

### 3. Falha de autenticação
Sinais:
- `401 Unauthorized`
- login falhando
- token ausente/inválido
- rota protegida negando acesso

Teste padrão:
```bash
cd ~/projetos/ia_trabalhista_robusta/backend && \
AT="$(curl -sS -X POST http://127.0.0.1:8099/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"dev"}' | python -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')" && \
curl -i -sS http://127.0.0.1:8099/api/v1/auth/me \
  -H "Authorization: Bearer $AT"
```

Interpretação:
- login falha: problema em credenciais seed, schema, auth flow ou usuário
- login ok e `/auth/me` falha: problema em middleware/token/header
- login ok e rota específica falha: problema de permissão, tenant ou guarda de rota

### 4. Falha de banco
Sinais:
- `/ready` falha
- rotas que dependem de leitura/escrita retornam 500
- stack trace de SQLAlchemy, sqlite ou postgres

Checklist:
- confirmar URL/config de banco
- confirmar se banco está de pé
- confirmar se migrations/schema estão compatíveis
- confirmar se credenciais/ambiente mudaram

Checagens locais típicas:
```bash
cd ~/projetos/ia_trabalhista_robusta/backend && env | grep -E 'DATABASE|DB_|POSTGRES'
```

```bash
cd ~/projetos/ia_trabalhista_robusta/backend && curl -i http://127.0.0.1:8099/ready
```

### 5. Erro 500 em casos / análises / relatórios
Sinais:
- rota específica quebra
- health pode estar ok
- auth pode estar ok
- falha de regra de negócio, serialização ou serviço interno

Procedimento:
1. reproduzir a chamada com curl
2. capturar status e corpo da resposta
3. identificar entidade/ID afetado
4. consultar logs do backend
5. isolar se o problema é:
   - payload
   - regra de negócio
   - banco
   - serviço de PDF
   - contexto tenant

### 6. Falha de PDF / executive report
Sinais:
- geração de relatório falha
- summary funciona, PDF falha
- retorno 500 ou erro de renderização

Procedimento:
1. validar login
2. validar rota de summary
3. validar rota de executive report
4. validar rota de PDF
5. comparar onde quebra

Exemplo de sequência:
```bash
cd ~/projetos/ia_trabalhista_robusta/backend && \
LOGIN_JSON='{"username":"admin","password":"dev"}' && \
LOGIN_RESP="$(curl -sS -X POST http://127.0.0.1:8099/api/v1/auth/login -H 'Content-Type: application/json' -d "$LOGIN_JSON")" && \
TOKEN="$(printf '%s' "$LOGIN_RESP" | python -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')" && \
curl -i -sS http://127.0.0.1:8099/api/v1/cases/1/executive-summary -H "Authorization: Bearer $TOKEN"
```

Depois repetir com:
- `/executive-report`
- rota de PDF correspondente

Se summary funciona e PDF falha, o incidente tende a estar no pipeline de renderização/geração de arquivo.

---

## Fluxo oficial de resposta a incidente

### Etapa 1 — confirmar escopo
Perguntas obrigatórias:
- o problema é geral ou em uma rota específica?
- afeta todos os usuários ou um tenant?
- começou após deploy, seed, migration ou mudança de env?
- existe erro reproduzível por curl?

Registrar:
- horário
- ambiente
- rota afetada
- usuário/tenant afetado
- status code
- payload usado
- resposta recebida

### Etapa 2 — coletar evidências mínimas
Coletar antes de mexer:
- resultado de `/healthz`
- resultado de `/ready`
- request curl exato
- response body
- logs do backend
- commit atual
- branch atual
- variáveis relevantes sem expor segredos completos

Comandos úteis:
```bash
cd ~/projetos/ia_trabalhista_robusta && git status -sb && git log --oneline -n 5
```

```bash
cd ~/projetos/ia_trabalhista_robusta/backend && curl -i http://127.0.0.1:8099/healthz && echo && curl -i http://127.0.0.1:8099/ready
```

### Etapa 3 — classificar incidente
Classificar em um destes grupos:
- aplicação indisponível
- banco indisponível
- autenticação quebrada
- autorização/tenant quebrado
- regressão após deploy
- erro de relatório/PDF
- corrupção de configuração/ambiente
- incidente de dados

### Etapa 4 — conter impacto
Medidas possíveis:
- pausar deploys
- congelar mudanças não relacionadas
- desabilitar rota problemática temporariamente, se existir mecanismo seguro
- operar manualmente apenas o fluxo afetado
- preparar rollback do último deploy/última mudança

Nunca executar correções amplas sem isolar o incidente.

### Etapa 5 — corrigir por micropatch
Regras:
- uma causa por vez
- mudança mínima
- sem refatoração oportunista durante incidente
- validar logo após aplicar

Validação mínima após correção:
- `/healthz`
- `/ready`
- login
- rota afetada
- teste automatizado relacionado, se existir

### Etapa 6 — decidir rollback
Fazer rollback quando:
- regressão começou logo após deploy
- causa não foi isolada com segurança
- correção em quente aumenta risco
- há impacto em autenticação, banco ou tenant isolation
- produção ficou instável e precisa voltar ao último estado confiável

---

## Critérios de rollback
Rollback é preferível quando houver:
- aumento de 500 em rota crítica
- quebra de login
- quebra de isolamento por tenant
- falha sistêmica de relatórios/PDF pós-release
- falha de readiness ligada a mudança recente
- dúvida técnica relevante sobre integridade dos dados

## Procedimento inicial de rollback
1. identificar último commit estável
2. confirmar se houve migration
3. avaliar se rollback é só de aplicação ou também de banco
4. registrar motivo
5. executar rollback controlado
6. validar health, ready, login e rota crítica
7. comunicar retorno ao estado estável

Comandos base de referência:
```bash
cd ~/projetos/ia_trabalhista_robusta && git log --oneline -n 10
```

```bash
cd ~/projetos/ia_trabalhista_robusta && git status -sb
```

Observação:
- rollback de código sem pensar em migration pode virar armadilha clássica
- se houver alteração de schema, validar compatibilidade antes de retroceder aplicação

---

## Checklist por tipo de erro

### HTTP 401
Verificar:
- login funciona?
- token foi enviado?
- prefixo `Bearer` está presente?
- rota exige usuário ativo?
- seed/credenciais mudaram?

### HTTP 403
Verificar:
- permissão/role
- contexto admin
- acesso entre tenants
- guarda específica da rota

### HTTP 404
Verificar:
- endpoint correto
- prefixo `/api/v1`
- rota registrada
- ID realmente existe

### HTTP 422
Verificar:
- schema do payload
- campos obrigatórios
- tipos corretos
- enums/contratos aceitos

### HTTP 500
Verificar:
- logs do backend
- banco
- contexto tenant
- serialização
- serviço interno do relatório/PDF

---

## Comandos de diagnóstico base

### Saúde
```bash
cd ~/projetos/ia_trabalhista_robusta/backend && curl -i http://127.0.0.1:8099/healthz
```

### Prontidão
```bash
cd ~/projetos/ia_trabalhista_robusta/backend && curl -i http://127.0.0.1:8099/ready
```

### Login
```bash
cd ~/projetos/ia_trabalhista_robusta/backend && curl -sS -X POST http://127.0.0.1:8099/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"dev"}'
```

### Teste autenticado
```bash
cd ~/projetos/ia_trabalhista_robusta/backend && \
AT="$(curl -sS -X POST http://127.0.0.1:8099/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"dev"}' | python -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')" && \
curl -i -sS http://127.0.0.1:8099/api/v1/auth/me \
  -H "Authorization: Bearer $AT"
```

### Rodar testes rápidos
```bash
cd ~/projetos/ia_trabalhista_robusta/backend && source .venv/bin/activate && pytest -q
```

---

## Evidências mínimas para fechar incidente
Antes de considerar resolvido, registrar:
- causa raiz conhecida ou hipótese mais provável
- evidência objetiva da falha
- ação aplicada
- validação pós-correção
- impacto percebido
- necessidade ou não de ação preventiva

## Pós-incidente
Após estabilizar:
1. criar ou ajustar teste automatizado
2. atualizar documentação afetada
3. registrar no daily log
4. avaliar necessidade de hardening adicional
5. avaliar se o incidente exige melhoria em backup, observabilidade, LGPD ou break-glass

## O que não fazer
- alterar frontend antes de validar backend
- mexer em vários arquivos sem evidência
- aplicar refactor durante incidente
- esconder stack trace sem capturar evidência antes
- fazer rollback sem avaliar banco/schema
- declarar “resolvido” sem repetir o fluxo afetado

## Estado esperado para considerar produção estável
Produção é considerada estável quando:
- `/healthz` responde 200
- `/ready` responde 200
- login responde corretamente
- rota crítica do fluxo principal responde
- rota de relatório principal responde
- não há vazamento entre tenants
- erro reproduzido deixou de ocorrer

## Dono operacional deste runbook
Este documento deve ser mantido vivo e atualizado a cada incidente relevante, nova rota crítica, mudança de deploy ou alteração estrutural do backend.
