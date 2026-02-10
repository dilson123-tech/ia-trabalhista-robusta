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
