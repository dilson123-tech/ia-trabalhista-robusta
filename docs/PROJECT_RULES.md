# IA Trabalhista Robusta — Regras do Projeto (permanentes)

## Objetivo
Ferramenta robusta para suporte real em advocacia trabalhista: intake, dossiê, checklist de provas, templates e auditoria.
IA ajuda a organizar e rascunhar; advogado revisa e assina.

## Regras (não negociáveis)
1. Tudo versionado (git): nada “solto”.
2. Documentação obrigatória: decisões e padrões ficam escritos.
3. Segurança/LGPD: não usar dado real de cliente em DEV; logs com redaction.
4. Auditoria: request_id, logs estruturados e audit trail em banco.
5. Mudanças pequenas e testadas: smoke antes/depois.
6. Templates padronizados do escritório; saída sempre “rascunho”.
7. Backups e restore testado.
8. Fonte dos fatos: tudo tem origem (relato/doc/testemunha). Sem inventar.

## Qualidade mínima
- Rotas críticas com smoke tests.
- Erros retornam JSON e geram log com request_id.
- Controle de acesso (RBAC) consistente.

## Semântica oficial do campo `source` em `parties_succession_service`

### Regra oficial
O comportamento atual do campo `source` no fluxo de `case_party_states` / `parties_succession_service` é considerado **contrato arquitetural válido** e **não caracteriza bug funcional**.

### Interpretação por camada
1. **Metadata persistida do vínculo**
   - representa a origem do dado enviado no payload ou da operação persistida

2. **Eventos e snapshots**
   - representam a origem da camada de domínio/processamento
   - portanto, `source = "parties_succession_service"` em events e snapshots é comportamento intencional

### Decisão operacional
- não reabrir backend estável por cosmética semântica
- não tratar essa diferença de significado como regressão funcional
- qualquer redesign futuro de nomenclatura/contrato deve ser tratado em microciclo separado, com decisão explícita de arquitetura

### Status
Regra documentada para encerramento da auditoria final do bloco backend de `case_party_states`.
