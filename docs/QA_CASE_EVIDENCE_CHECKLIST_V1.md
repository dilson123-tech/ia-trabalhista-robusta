# QA — Checklist de Provas e Pendências V1

Marco técnico: `v0.1.40-case-evidence-checklist-v1`

Checkpoint visual: `QA_CASE_EVIDENCE_CHECKLIST_VISUAL_OK`

## Objetivo

Validar visualmente o Checklist de Provas e Pendências V1 no painel da Plataforma IA Jurídica Pro / IA Trabalhista Robusta.

Este recurso organiza pendências operacionais do caso, separando corretamente:

- arquivos/anexos reais;
- provas já recebidas;
- itens pendentes;
- itens solicitados;
- itens recebidos;
- itens validados;
- itens dispensados;
- itens que precisam de revisão.

## Escopo técnico validado

O ciclo técnico anterior adicionou:

- tabela `case_evidence_checklist_items`;
- migration `f19c0e1a2b33_add_case_evidence_checklist_items.py`;
- model `CaseEvidenceChecklistItem`;
- schemas de criação, atualização e saída;
- rota `/api/v1/cases/{case_id}/evidence-checklist`;
- integração no `EvidenceModulePanel`;
- testes backend;
- build frontend.

## Validações técnicas anteriores

Foram executados com sucesso:

- `python3 -m py_compile`;
- `alembic upgrade head`;
- `PYTHONPATH=backend pytest -q backend/tests/test_case_evidence_checklist_flow.py backend/tests/test_case_attachments_flow.py`;
- `cd frontend && npm run build`;
- CI do PR #192 com 2/2 checks verdes.

## Validação visual executada

Ambiente:

- frontend local em `127.0.0.1:5173`;
- painel operacional de casos;
- módulo `Provas e Anexos`.

Itens validados:

- bloco `Checklist de provas e pendências` visível;
- badges superiores visíveis;
- criação do item `solicitar BO`;
- alteração de status até `Validado`;
- persistência após F5/reload;
- badge superior refletindo `1 item(ns) no checklist`;
- badge superior refletindo `0 pendente(s)`;
- badge superior refletindo `1 validado(s)`.

## Validação de anexos preservados

Também foi validado que o fluxo antigo de anexos/provas continuou funcionando após a nova feature.

Arquivo usado no QA:

- `dilsai-pdf-teste.pdf`

Resultado visual:

- arquivo exibido em `Arquivos anexados`;
- categoria exibida como `PDF`;
- tamanho exibido como `770 B`;
- descrição exibida;
- botões `Baixar` e `Excluir` visíveis.

Descrição usada:

`Arquivo QA para confirmar que anexos continuam funcionando`

## Resultado

`QA_CASE_EVIDENCE_CHECKLIST_VISUAL_OK`

O Checklist de Provas e Pendências V1 está aprovado visualmente para o estágio atual do produto.

## Observações de produto

Este marco fortalece a plataforma como esteira operacional real de escritório, porque permite ao advogado controlar:

- o que falta pedir ao cliente;
- o que já foi solicitado;
- o que foi recebido;
- o que foi validado;
- o que pode ser dispensado;
- quais provas ainda exigem revisão.

O recurso não substitui a avaliação jurídica do advogado. Ele organiza a preparação do caso.

## Escopo preservado

- sem automação jurídica sem advogado;
- sem alteração no fluxo de upload/download/delete de anexos;
- sem misturar arquivo anexado com pendência operacional;
- sem nova área jurídica;
- sem IA automática neste ciclo;
- mantendo rastreabilidade por caso e tenant.

## Próximo passo recomendado

Avaliar o próximo ciclo da esteira operacional:

1. integração do checklist com mensagens prontas/WhatsApp;
2. prontidão do caso;
3. dossiê interno do caso;
4. melhoria visual do formulário do checklist.
