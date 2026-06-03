# QA — Dossiê Interno do Caso V1

Marco técnico: `v0.1.44-case-internal-dossier-v1`

Checkpoint visual: `QA_CASE_INTERNAL_DOSSIER_VISUAL_OK`

## Objetivo

Validar visualmente o Dossiê Interno do Caso V1 no painel da Plataforma IA Jurídica Pro / IA Trabalhista Robusta.

Este recurso consolida informações operacionais do caso em uma visão única para apoio ao advogado.

Importante: o dossiê interno não é peça processual, não substitui revisão jurídica humana e não autoriza protocolo automático.

## Escopo técnico validado

O Dossiê Interno do Caso V1 foi implementado no frontend, sem backend novo e sem migration.

O recurso consolida:

- dados do caso;
- cliente e WhatsApp;
- histórico de contatos;
- testemunhas/depoentes;
- checklist de provas e pendências;
- anexos/provas;
- prontidão do caso;
- próximos passos operacionais.

## Validação técnica anterior

Antes do QA visual, foi validado:

- `cd frontend && npm run build`;
- PR #196 mergeado na main;
- tag `v0.1.44-case-internal-dossier-v1` criada no HEAD.

## Validação visual executada

Ambiente:

- frontend local em `127.0.0.1:5173`;
- card de caso no painel operacional;
- caso com cliente WhatsApp, histórico, testemunha, checklist, anexo e prontidão já cadastrados.

Itens validados no painel:

- bloco `Dossiê interno do caso` visível;
- botão `Atualizar dossiê` visível;
- processo exibido como `WHATSAPP-QA-af127cf3`;
- prontidão exibida como `100% / Pronto para revisão do advogado`;
- contador `Contatos: 2`;
- contador `Pessoas: 1`;
- contador `Checklist: 1/1`;
- contador `Anexos: 1`;
- cliente exibido como `Cliente WhatsApp QA`;
- WhatsApp exibido;
- último contato exibido como `Solicitação de documentos pelo WhatsApp`;
- pessoa-chave exibida como `Cliente WhatsApp QA — testemunha`;
- prova/anexo exibido como `dilsai-pdf-teste.pdf — pdf`;
- próximos passos operacionais exibidos;
- aviso de segurança preservado: `Dossiê interno é apoio operacional supervisionado, não peça processual e não protocolo automático`.

## Persistência / recálculo visual

Após nova atualização visual, o dossiê continuou consistente com os dados do caso.

Resultado:

- score permaneceu correto;
- dados consolidados continuaram visíveis;
- contadores permaneceram coerentes com os cadastros do caso;
- aviso de segurança permaneceu visível.

## Resultado

`QA_CASE_INTERNAL_DOSSIER_VISUAL_OK`

O Dossiê Interno do Caso V1 está aprovado visualmente para o estágio atual do produto.

## Observações de produto

Este marco fortalece a plataforma como esteira operacional real de escritório, porque permite ao advogado enxergar rapidamente:

- situação operacional do caso;
- cliente e contato;
- último contato;
- pessoas-chave;
- provas e anexos;
- pendências;
- prontidão;
- próximos passos.

A visão é de apoio operacional supervisionado, não de decisão jurídica automática.

## Escopo preservado

- sem backend novo;
- sem migration;
- sem nova tabela;
- sem PDF/exportação neste ciclo;
- sem automação jurídica sem advogado;
- sem protocolo automático;
- sem alterar anexos, checklist, contatos, testemunhas ou prontidão.

## Próximo passo recomendado

Avaliar o próximo ciclo da esteira operacional:

1. integração Checklist + WhatsApp;
2. melhoria visual premium dos formulários operacionais;
3. exportação futura do dossiê interno;
4. documentação consolidada da esteira operacional;
5. preparação de demonstração comercial controlada.
