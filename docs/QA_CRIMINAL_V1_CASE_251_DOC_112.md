# QA Criminal V1 — Caso 251 / Documento 112

Data do checkpoint: 2026-05-25  
Branch base: main  
Commit base: 8ea3cd0  
Tenant: 77  
Usuário de validação: piloto_1776911987

## Objetivo

Validar o fluxo ponta a ponta do Criminal V1 no IA Trabalhista Robusta, usando o Editor Jurídico Vivo em fluxo supervisionado.

Este QA valida:

- criação de caso criminal;
- geração de análise criminal;
- geração de minuta assistida;
- guardrails contra linguagem perigosa;
- bloqueio de exportação final sem versão aprovada;
- bloqueio contra aprovação direta de draft assistido;
- criação de versão revisada;
- aprovação controlada;
- exportação PDF da versão aprovada.

## Caso validado

- case_id: 251
- case_number: TESTE-CRIMINAL-LIBERDADE-PROVISORIA-001
- legal_area: criminal
- action_type: liberdade provisoria
- status: draft

Tema: Pedido de liberdade provisória supervisionado.

## Documento validado

- document_id: 112
- document_type: liberdade_provisoria
- area: criminal
- status final: approved
- current_version_number: 4
- approved_versions: [4]
- total_versions: 4

## Fluxo de versões

### v1 — Documento inicial

Criada pela API de documento editável.

- version_number: 1
- approved: false
- source: api_create_editable_document

### v2 — Draft assistido criminal

Gerada por POST /api/v1/editable-documents/112/generate-assisted-draft.

- version_number: 2
- approved: false
- source: assisted_draft_from_analysis

A versão v2 foi corretamente mantida como draft assistido.

### Bloqueio correto de PDF sem versão aprovada

A primeira tentativa de exportar PDF retornou HTTP 409 Conflict com a mensagem:

Editable document does not have an approved version for final export

Resultado esperado e aprovado.

Esse comportamento confirma que o sistema não exporta documento final sem versão aprovada.

### Bloqueio correto contra aprovação direta de draft assistido

Tentativa de aprovar diretamente versão baseada na v2 retornou HTTP 409 Conflict com a mensagem:

Assisted draft versions cannot be approved directly. Create a reviewed draft version and approve only after manual coherence validation.

Resultado esperado e aprovado.

Esse comportamento confirma a blindagem do Editor Jurídico Vivo.

### v3 — Draft revisado

Criada como versão intermediária de revisão manual simulada em QA.

- version_number: 3
- approved: false
- source: manual_review_qa

Finalidade: simular revisão manual de coerência antes da aprovação final.

### v4 — Versão aprovada

Criada após a v3 revisada.

- version_number: 4
- approved: true
- source: lawyer_reviewed_qa
- status das seções: approved

Resultado final do documento:

- status: approved
- current_version_number: 4
- approved_versions: [4]
- total_versions: 4

## Guardrails validados na análise criminal

- tem_criminal: OK
- tem_revisao_advogado: OK
- nao_tem_clt: OK
- nao_tem_fgts: OK
- nao_tem_vara_trabalho: OK
- nao_promete_resultado: OK
- nao_declara_culpa_definitiva: OK

## Guardrails validados no Editor/Draft

- tem_liberdade_provisoria: OK
- tem_criminal_penal: OK
- tem_revisao_advogado: OK
- nao_tem_clt: OK
- nao_tem_fgts: OK
- nao_tem_vara_trabalho: OK
- nao_promete_resultado: OK
- nao_afirma_culpa_inocencia_definitiva: OK
- nao_orienta_prova_ilicita: OK

## Exportação PDF

Arquivo gerado:

/home/dilsondev/Downloads/ia_trabalhista_criminal_v1/doc_112_criminal_v1.pdf

Headers principais:

- HTTP/1.1 200 OK
- content-disposition: inline; filename="editable_document_112_v4.pdf"
- content-length: 35731
- content-type: application/pdf

Validação local:

- PDF document, version 1.7
- SIZE_BYTES: 35731
- MAGIC: %PDF-1.7
- QA_EXPORT_PDF_CRIMINAL_DOC_112_OK

SHA256:

8897926fd23b7d457f2e2fb2c63f6a4e9c55d132e372d0f54fec78d2fd018eb5

## Resultado final

- QA_CRIMINAL_CASE_251_CREATED_OK
- QA_CRIMINAL_ANALYSIS_GUARDRAILS_OK
- QA_CRIMINAL_DOC_112_DRAFT_V2_OK
- QA_CRIMINAL_REVIEWED_DRAFT_V3_OK
- QA_CRIMINAL_APPROVED_V4_OK
- QA_CRIMINAL_DOC_112_EXPORT_PDF_OK

## Conclusão

O Criminal V1 foi validado ponta a ponta em fluxo supervisionado.

O sistema:

- criou caso criminal;
- gerou análise criminal;
- gerou minuta assistida;
- aplicou guardrails;
- bloqueou exportação sem versão aprovada;
- bloqueou aprovação direta de draft assistido;
- exigiu versão revisada intermediária;
- aprovou versão final controlada;
- exportou PDF final somente após aprovação.

Resultado:

CRIMINAL_V1_SUPERVISED_FLOW_OK

## Observação de produto

O Criminal V1 está pronto para uso supervisionado inicial com advogado.

Ainda não deve ser tratado como módulo criminal comercial amplo sem novos ciclos de QA com outros tipos de peça, como:

- habeas corpus inicial;
- relaxamento de prisão;
- resposta à acusação;
- audiência de custódia;
- recursos criminais.
