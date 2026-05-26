# QA Criminal V1 — Multi Docs 113, 114 e 115

Data do checkpoint: 2026-05-26  
Tenant: 77  
Usuário de validação: piloto_1776911987  
Escopo: Criminal V1 — habeas corpus, relaxamento de prisão e resposta à acusação

## Objetivo

Validar o fluxo Criminal V1 para três novos tipos de documentos:

- Habeas corpus inicial;
- Relaxamento de prisão;
- Resposta à acusação.

Este ciclo complementa o QA anterior de liberdade provisória no caso 251 / doc 112.

## Casos e documentos

- Case 252 / Doc 113 — Habeas corpus inicial
- Case 253 / Doc 114 — Relaxamento de prisão
- Case 254 / Doc 115 — Resposta à acusação

## Análises

As análises dos casos 252, 253 e 254 foram geradas com sucesso.

Resultado consolidado:

- CRIMINAL_V1_ANALYSES_252_253_254_OK

Guardrails validados:

- presença do tema criminal adequado;
- presença de revisão por advogado;
- ausência de CLT;
- ausência de FGTS;
- ausência de Vara do Trabalho;
- ausência de promessa de resultado;
- ausência de culpa/inocência definitiva;
- ausência de orientação para inventar, adulterar ou ocultar prova.

## Drafts assistidos

Os documentos 113, 114 e 115 tiveram draft assistido gerado como versão v2.

Resultado consolidado:

- CRIMINAL_V1_DRAFTS_252_253_254_OK

Cada documento permaneceu como draft assistido, não aprovado diretamente.

## Revisão e aprovação

Foi aplicada a regra correta do Editor Jurídico Vivo:

- v2: draft assistido;
- v3: versão revisada em QA;
- v4: versão aprovada após revisão.

Resultado:

- Doc 113: status approved, current_version_number 4
- Doc 114: status approved, current_version_number 4
- Doc 115: status approved, current_version_number 4

Resultado consolidado:

- CRIMINAL_V1_DOCS_113_114_115_REVIEW_APPROVAL_OK

## Observação sobre qualidade do doc 115

Durante o QA extra, o doc 115 apresentou termos tematicamente incompatíveis com resposta à acusação criminal, como:

- laudo/relatório médico;
- relatório médico;
- nexo causal;
- perícia técnica;
- quantificação;
- impactos alegados.

Esses termos foram removidos/ajustados na versão revisada antes da aprovação final.

A aprovação final ocorreu somente após limpeza temática.

## Exportação PDF

Os PDFs foram exportados e validados com sucesso.

### Doc 113 — Habeas corpus

Arquivo:

/home/dilsondev/Downloads/ia_trabalhista_criminal_v1_multi/doc_113_habeas_corpus.pdf

Validação:

- SIZE_BYTES: 36022
- MAGIC: %PDF-1.7
- SHA256: fe52f051b3c08cc541ed217775872cf7aeb93299101675855d0f06c3a0084ad9

### Doc 114 — Relaxamento de prisão

Arquivo:

/home/dilsondev/Downloads/ia_trabalhista_criminal_v1_multi/doc_114_relaxamento_prisao.pdf

Validação:

- SIZE_BYTES: 36139
- MAGIC: %PDF-1.7
- SHA256: c0e53f3121e8d002850fa506ee885b6c4b5323c11425450531c231fe692316ad

### Doc 115 — Resposta à acusação

Arquivo:

/home/dilsondev/Downloads/ia_trabalhista_criminal_v1_multi/doc_115_resposta_acusacao.pdf

Validação:

- SIZE_BYTES: 36177
- MAGIC: %PDF-1.7
- SHA256: e3eb748b414b599927464d70fb7b0556486169f98b7227386fbde82a8c7dbf4b

Resultado consolidado:

- QA_EXPORT_PDF_CRIMINAL_DOCS_113_114_115_OK

## Resultado final do ciclo

- QA_CRIMINAL_CASE_252_ANALYSIS_OK
- QA_CRIMINAL_CASE_253_ANALYSIS_OK
- QA_CRIMINAL_CASE_254_ANALYSIS_OK
- QA_CRIMINAL_DOC_113_DRAFT_REVIEW_APPROVAL_PDF_OK
- QA_CRIMINAL_DOC_114_DRAFT_REVIEW_APPROVAL_PDF_OK
- QA_CRIMINAL_DOC_115_DRAFT_REVIEW_APPROVAL_PDF_OK
- CRIMINAL_V1_MULTI_DOCS_113_114_115_OK

## Conclusão

O Criminal V1 agora possui quatro fluxos iniciais validados:

- Liberdade provisória;
- Habeas corpus inicial;
- Relaxamento de prisão;
- Resposta à acusação.

O módulo criminal demonstrou:

- criação de casos;
- análise criminal;
- guardrails por tema;
- geração de minuta assistida;
- bloqueio de aprovação direta de draft;
- revisão intermediária obrigatória;
- aprovação controlada;
- exportação PDF somente após versão aprovada.

Resultado:

CRIMINAL_V1_INITIAL_PACKAGE_OK

## Observações técnicas futuras

Foram identificados pontos de melhoria:

- payload com campo interno slug causou HTTP 500 em criação de caso; deveria retornar 422;
- backend local estava sem ADMIN_API_KEY carregada no processo uvicorn;
- tenant 77 precisou de ajuste controlado de QA para liberar análises após limite do plano;
- texto "Peça pronta gerada a partir da análise do caso" deveria ser refinado para "Minuta assistida gerada a partir da análise do caso".
