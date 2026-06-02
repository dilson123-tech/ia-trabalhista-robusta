# QA — Prontidão do Caso V1

Marco técnico: `v0.1.42-case-readiness-v1`

Checkpoint visual: `QA_CASE_READINESS_VISUAL_OK`

## Objetivo

Validar visualmente a Prontidão do Caso V1 no painel da Plataforma IA Jurídica Pro / IA Trabalhista Robusta.

Este recurso consolida informações operacionais do caso para indicar se ele está pronto para revisão humana do advogado.

Importante: `Pronto para revisão do advogado` não significa pronto para protocolo automático.

## Escopo técnico validado

A Prontidão do Caso V1 foi implementada no frontend, sem backend novo e sem migration.

O recurso consolida:

- cliente/contato;
- WhatsApp;
- consentimento de contato;
- histórico de contato;
- testemunhas/depoentes;
- checklist de provas e pendências;
- anexos/provas.

## Validação técnica anterior

Antes do QA visual, foi validado:

- `cd frontend && npm run build`;
- CI do PR #194 com 2/2 checks verdes.

## Validação visual executada

Ambiente:

- frontend local em `127.0.0.1:5173`;
- card de caso no painel operacional;
- caso com cliente WhatsApp, histórico, testemunha, checklist e anexo já cadastrados.

Itens validados no painel:

- bloco `Prontidão do caso` visível;
- botão `Atualizar prontidão` visível;
- score exibido como `100%`;
- status exibido como `Pronto para revisão do advogado`;
- contador `Contatos: 2`;
- contador `Testemunhas: 1`;
- contador `Checklist: 1/1`;
- contador `Pendências: 0`;
- contador `Anexos: 1`;
- mensagem `Caso sem pendências operacionais principais na régua V1`;
- aviso de segurança preservado: `Pronto significa pronto para revisão humana do advogado, não protocolo automático`.

## Resultado

`QA_CASE_READINESS_VISUAL_OK`

A Prontidão do Caso V1 está aprovada visualmente para o estágio atual do produto.

## Observações de produto

Este marco fecha uma régua operacional útil para escritório, permitindo ao advogado identificar rapidamente se o caso está:

- crítico;
- em preparação;
- quase pronto;
- pronto para revisão humana.

A régua não decide estratégia jurídica, não substitui advogado e não autoriza protocolo automático.

## Escopo preservado

- sem backend novo;
- sem migration;
- sem nova tabela;
- sem automação jurídica sem advogado;
- sem protocolo automático;
- sem alterar anexos, checklist, contatos ou testemunhas;
- sem nova área jurídica.

## Próximo passo recomendado

Avaliar o próximo ciclo da esteira operacional:

1. integração Checklist + WhatsApp;
2. Dossiê interno do caso;
3. melhoria visual premium dos formulários operacionais;
4. pacote de QA/documentação consolidada da esteira operacional.
