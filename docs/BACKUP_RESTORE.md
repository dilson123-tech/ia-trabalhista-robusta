# BACKUP E RESTORE — IA Trabalhista Robusta

## Objetivo
Este documento define o procedimento mínimo de backup e restore para o projeto **IA Trabalhista Robusta**, com foco em recuperação segura, previsível e validável.

Princípios:
- backup sem teste de restore não conta como backup confiável
- restore deve ser validado em ambiente controlado antes de uso em produção
- o procedimento deve priorizar integridade dos dados e rastreabilidade
- alterações de banco e aplicação devem ser avaliadas em conjunto

---

## Escopo
Este documento cobre:
- backup lógico do banco usado pela aplicação
- cópia de variáveis e configuração não sensível de referência
- restore controlado para validação
- critérios mínimos para considerar o procedimento confiável

---

## Tipos de backup considerados

### 1. Backup lógico de banco
Preferencial para o MVP atual.
Objetivo:
- preservar estrutura e dados
- permitir restore em ambiente separado
- validar recuperação após incidente ou mudança crítica

### 2. Snapshot/copias de ambiente
Pode complementar o processo, mas não substitui restore validado.

---

## Regra de validade
Um backup só será considerado válido quando:
- o arquivo tiver sido gerado com sucesso
- houver registro de data/hora
- o restore tiver sido executado em ambiente controlado
- a aplicação responder health/ready após o restore
- ao menos uma rota autenticada crítica tiver sido validada

---

## O que deve ser preservado
- banco de dados da aplicação
- migrations/alembic em vigor
- arquivo `.env.example` como referência estrutural
- checklist/release docs relacionados à versão
- identificação do commit ativo no momento do backup

Observação:
- segredos reais não devem ser versionados em documentação operacional
- valores sensíveis devem ser armazenados apenas no gerenciador seguro adotado no ambiente

---

## Fluxo mínimo de backup

### Etapa 1 — identificar contexto
Registrar antes do backup:
- data e hora
- ambiente
- banco alvo
- commit atual
- motivo do backup: rotina, pré-release, pré-migration, incidente ou hotfix

Comando de referência:
```bash
cd ~/projetos/ia_trabalhista_robusta && git status -sb && git log --oneline -n 3
```

### Etapa 2 — gerar backup lógico
O método exato depende do banco ativo no ambiente.

Para SQLite, preservar cópia íntegra do arquivo de banco antes de mudanças críticas.

Exemplo de referência:
```bash
cd ~/projetos/ia_trabalhista_robusta/backend && cp app.db "app.db.bak.$(date +%Y%m%d_%H%M%S)"
```

Para Postgres, gerar dump lógico com ferramenta apropriada do ambiente.

Exemplo de referência:
```bash
pg_dump "$DATABASE_URL" > "backup_$(date +%Y%m%d_%H%M%S).sql"
```

### Etapa 3 — registrar evidência
Registrar:
- nome do arquivo gerado
- tamanho do arquivo
- horário
- commit relacionado
- responsável pela operação

---

## Fluxo mínimo de restore validado

### Etapa 1 — preparar ambiente controlado
O restore deve ocorrer primeiro em ambiente separado do fluxo principal sempre que possível.

Validar antes:
- banco de destino correto
- isolamento do ambiente de teste
- compatibilidade entre dump/cópia e versão da aplicação
- disponibilidade de migrations correspondentes

### Etapa 2 — restaurar o banco
Para SQLite, restaurar a cópia para um arquivo de teste e apontar a aplicação para esse banco restaurado.

Exemplo de referência:
```bash
cd ~/projetos/ia_trabalhista_robusta/backend && cp "app.db.bak.YYYYMMDD_HHMMSS" restore_test.db
```

Para Postgres, restaurar o dump em base controlada e separada da produção.

Exemplo de referência:
```bash
psql "$DATABASE_URL_DESTINO" < backup_YYYYMMDD_HHMMSS.sql
```

### Etapa 3 — validar aplicação após restore
Checklist mínimo:
- `/healthz` responde 200
- `/ready` responde 200
- login funciona
- uma rota autenticada crítica funciona
- um caso existente pode ser lido sem erro

Comandos de referência:
```bash
cd ~/projetos/ia_trabalhista_robusta/backend && curl -i http://127.0.0.1:8099/healthz && echo && curl -i http://127.0.0.1:8099/ready
```

```bash
cd ~/projetos/ia_trabalhista_robusta/backend && curl -sS -X POST http://127.0.0.1:8099/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"dev"}'
```

### Etapa 4 — registrar resultado do restore
Registrar:
- backup usado
- ambiente de restore
- horário de início e fim
- resultado das validações
- falhas encontradas
- decisão final: aprovado ou reprovado

---

## Critérios mínimos de sucesso
O procedimento será considerado aprovado quando:
- o backup for gerado sem erro
- o restore for concluído sem corrupção aparente
- health e ready responderem corretamente
- o login funcionar
- ao menos uma rota autenticada crítica responder com sucesso
- o processo estiver documentado com evidência mínima

---

## O que invalida um backup
Um backup não deve ser considerado confiável quando:
- o arquivo foi gerado sem validação posterior
- o restore nunca foi testado
- não existe vínculo com data/hora/commit
- o arquivo está incompleto, corrompido ou sem rastreabilidade
- depende de conhecimento informal não documentado para ser restaurado

## Riscos e cuidados
- nunca sobrescrever a base principal sem validação prévia
- nunca testar restore diretamente em produção
- validar compatibilidade entre schema, migrations e versão da aplicação
- preservar evidências da operação antes de qualquer ação corretiva
- proteger arquivos de backup contra acesso indevido

## Rotina mínima recomendada
- realizar backup antes de migrations, releases e mudanças críticas
- validar restore periodicamente em ambiente controlado
- registrar resultado da última validação de restore
- revisar este documento sempre que a arquitetura de banco mudar

## Dono operacional
Este documento deve ser mantido vivo e atualizado a cada mudança relevante de banco, estratégia de deploy, migration crítica ou incidente que afete integridade e recuperação de dados.
