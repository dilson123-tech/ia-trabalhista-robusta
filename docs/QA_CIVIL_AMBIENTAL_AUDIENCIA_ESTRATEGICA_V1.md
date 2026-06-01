# QA Civil/Ambiental — Audiência Estratégica V1

## Checkpoint

`QA_CIVIL_AMBIENTAL_AUDIENCIA_ESTRATEGICA_FLOW_OK`

## Objetivo

Validar o primeiro fluxo E2E da Audiência Estratégica Civil/Ambiental dentro da Plataforma IA Jurídica Pro.

Este QA confirma que o tipo documental `AUDIENCIA_ESTRATEGICA`, já validado nos fluxos Cível, Criminal, Trabalhista, Consumidor, Família, Previdenciário/BPC-LOAS e Contexto V2, também funciona para contexto Civil/Ambiental sem criar novo tipo documental e sem quebrar os fluxos anteriores.

## Contexto do produto

A Audiência Estratégica é um recurso transversal premium da plataforma.

Ela não é petição inicial, contestação, manifestação, parecer definitivo ou peça automática para protocolo. É roteiro interno de apoio estratégico ao advogado, voltado para preparação de audiência, prova oral, perguntas por pessoa, perguntas perigosas, perguntas condicionais e revisão humana.

Na área Civil/Ambiental, o roteiro precisa apoiar especialmente a preparação de perguntas sobre:

- responsabilidade civil;
- dano ambiental;
- dano de vizinhança;
- ruído;
- fumaça;
- odor;
- infiltração;
- descarte irregular;
- obra irregular;
- nexo causal;
- extensão do dano;
- obrigação de fazer;
- obrigação de não fazer;
- reparação;
- indenização;
- perícia;
- laudo técnico;
- fotos;
- vídeos;
- auto de fiscalização;
- órgão público;
- vizinhos e comunidade afetada;
- documentos e anexos de prova.

## Escopo validado

O QA automatizado validou:

1. criação de usuário admin via seed controlado;
2. login autenticado;
3. criação de caso Civil/Ambiental QA;
4. criação de estado de partes;
5. criação de relação entre a parte causadora alegada e a parte prejudicada;
6. upload de anexo/prova técnica e de fiscalização;
7. geração de análise técnica Civil/Ambiental;
8. criação de documento `AUDIENCIA_ESTRATEGICA`;
9. geração de roteiro assistido;
10. validação dos blocos esperados;
11. validação dos papéis Civil/Ambiental;
12. validação do Contexto V2 no roteiro;
13. validação contra contaminação previdenciária, família, consumidor, trabalhista, criminal e cível fallback;
14. aprovação de versão;
15. exportação PDF;
16. confirmação de PDF válido.

## Arquivos criados

- `backend/tests/test_civil_ambiental_audiencia_estrategica_questions.py`
- `backend/tests/test_civil_ambiental_audiencia_estrategica_flow.py`

## Arquivo alterado

- `backend/app/api/v1/routes/editable_documents.py`

## Commits do ciclo

- `210390b` — `feat(legal): add civil environmental strategic hearing questions`
- `82185f0` — `test(legal): validate civil environmental strategic hearing flow`

## Testes principais

- `test_civil_ambiental_questions_include_expected_roles_and_themes`
- `test_civil_ambiental_questions_do_not_contaminate_other_areas`
- `test_civil_ambiental_dispatcher_uses_specific_questions`
- `test_existing_audiencia_flows_are_preserved`
- `test_civil_ambiental_audiencia_estrategica_generates_approves_and_exports_pdf`

## Caso QA usado no teste E2E

O teste cria dinamicamente um caso com:

- Área jurídica: `civil_ambiental`
- Tipo de ação: `responsabilidade_civil_ambiental_dano_vizinhanca`
- Documento: `audiencia_estrategica`
- Título: `Roteiro de Audiência Estratégica Civil/Ambiental — QA`

O cenário simulado inclui:

- responsabilidade civil ambiental;
- dano de vizinhança;
- ruído excessivo;
- fumaça;
- odor;
- infiltração;
- descarte irregular;
- possível dano ambiental causado por empresa vizinha;
- fotos;
- vídeos;
- laudo técnico;
- auto de fiscalização;
- reclamações de moradores;
- registros de órgão público;
- nexo causal;
- extensão do dano;
- prova técnica;
- testemunhas;
- obrigação de fazer;
- obrigação de não fazer;
- reparação;
- indenização;
- medidas para cessar o dano.

## Partes e contexto estruturado validados

O teste cadastra e valida no roteiro:

- Moradora Prejudicada QA;
- Empresa Vizinha QA;
- Vizinho Testemunha QA;
- Engenheiro Ambiental QA;
- Fiscalização Ambiental QA.

Também valida a relação:

`origem_alegada_do_dano_ambiental_e_vizinhanca`

E o anexo/prova:

`auto_fiscalizacao_laudo_ruido_fumaca.pdf`

Com descrição:

`Laudo técnico, fotos, vídeos e auto de fiscalização sobre ruído, fumaça, odor e infiltração.`

## Blocos de audiência validados

O teste confirmou a presença dos blocos:

- `sintese_tese_audiencia`
- `pontos_provar`
- `perguntas_pessoas_identificadas`
- `perguntas_repetitivas_perigosas`
- `perguntas_condicionais`
- `versao_curta`
- `pontos_confirmar_advogado`

## Papéis Civil/Ambiental validados

O roteiro Civil/Ambiental gerado contém perguntas para:

- autor / prejudicado;
- réu / causador alegado do dano;
- testemunha do autor;
- testemunha da defesa;
- perito / técnico ambiental ou de engenharia;
- fiscalização / órgão público;
- vizinho / comunidade afetada;
- responsável por documentos, fotos, vídeos ou laudos.

Também foram validados termos estratégicos sensíveis como:

- responsabilidade civil;
- dano ambiental;
- dano de vizinhança;
- nexo causal;
- fiscalização;
- perícia;
- laudo;
- obrigação de fazer;
- obrigação de não fazer;
- contexto estruturado adicional identificado no caso;
- material de apoio estratégico;
- revisão e decisão final do advogado.

## Blindagem contra contaminação

O teste confirmou ausência de termos indevidos dos fluxos anteriores, como:

- requerente / segurado;
- familiar cuidador / responsável pela rotina;
- genitor / requerente;
- genitor / requerido;
- consumidor / autor;
- fornecedor / empresa ré;
- reclamante / empregado;
- preposto / representante da reclamada;
- vítima / ofendido;
- policial militar / agente da abordagem;
- representante da PRATIC SIDER;
- Edson Estevão;
- locação da carreta.

## Preservação dos fluxos anteriores

A bateria de regressão confirmou que os fluxos já verdes continuam funcionando:

- Civil/Ambiental;
- Previdenciário/BPC-LOAS;
- Família;
- Consumidor;
- Trabalhista;
- Criminal.

Resultado observado na bateria E2E relacionada:

`6 passed`

Também foi executada bateria unitária/regressiva dos helpers e Contexto V2, preservando os módulos anteriores.

Resultado observado:

`49 passed`

## Aprovação

O teste aprova uma nova versão baseada na versão gerada.

Validação esperada:

- versão gerada: `2`
- versão aprovada: `3`
- status final do documento: `approved`
- versão atual final: `3`

## Exportação PDF

O teste exporta o PDF pelo endpoint:

`GET /api/v1/editable-documents/{document_id}/export/pdf`

Validações realizadas:

- status HTTP 200;
- `content-type = application/pdf`;
- conteúdo inicia com `%PDF`;
- tamanho do PDF maior que 1000 bytes.

## Validações locais executadas

Teste unitário/regressão Civil/Ambiental:

`PYTHONPATH=backend pytest -q backend/tests/test_civil_ambiental_audiencia_estrategica_questions.py`

Resultado observado:

`27 passed`

Bateria unitária/regressiva relacionada:

`PYTHONPATH=backend pytest -q backend/tests/test_civil_ambiental_audiencia_estrategica_questions.py backend/tests/test_previdenciario_audiencia_estrategica_questions.py backend/tests/test_familia_audiencia_estrategica_questions.py backend/tests/test_consumidor_audiencia_estrategica_questions.py backend/tests/test_audiencia_context_snapshot_v2.py backend/tests/test_trabalhista_audiencia_estrategica_questions.py backend/tests/test_criminal_audiencia_estrategica_questions.py`

Resultado observado:

`49 passed`

Teste E2E Civil/Ambiental:

`PYTHONPATH=backend pytest -q backend/tests/test_civil_ambiental_audiencia_estrategica_flow.py`

Resultado observado:

`1 passed`

Bateria E2E relacionada:

`PYTHONPATH=backend pytest -q backend/tests/test_civil_ambiental_audiencia_estrategica_flow.py backend/tests/test_previdenciario_audiencia_estrategica_flow.py backend/tests/test_familia_audiencia_estrategica_flow.py backend/tests/test_consumidor_audiencia_estrategica_flow.py backend/tests/test_trabalhista_audiencia_estrategica_flow.py backend/tests/test_criminal_audiencia_estrategica_flow.py`

Resultado observado:

`6 passed`

Compilação dos helpers e testes de perguntas:

`python3 -m py_compile backend/app/api/v1/routes/editable_documents.py backend/tests/test_civil_ambiental_audiencia_estrategica_questions.py backend/tests/test_previdenciario_audiencia_estrategica_questions.py backend/tests/test_familia_audiencia_estrategica_questions.py backend/tests/test_consumidor_audiencia_estrategica_questions.py backend/tests/test_audiencia_context_snapshot_v2.py backend/tests/test_trabalhista_audiencia_estrategica_questions.py backend/tests/test_criminal_audiencia_estrategica_questions.py`

Resultado:

`PY_COMPILE_OK`

Compilação dos testes E2E:

`python3 -m py_compile backend/tests/test_civil_ambiental_audiencia_estrategica_flow.py backend/tests/test_previdenciario_audiencia_estrategica_flow.py backend/tests/test_familia_audiencia_estrategica_flow.py backend/tests/test_consumidor_audiencia_estrategica_flow.py backend/tests/test_trabalhista_audiencia_estrategica_flow.py backend/tests/test_criminal_audiencia_estrategica_flow.py`

Resultado:

`PY_COMPILE_OK`

## Warnings

Foram exibidos warnings já conhecidos do projeto, incluindo:

- `passlib` / `crypt` deprecated;
- `PydanticDeprecatedSince20` por uso de `class Config`;
- `datetime.utcnow()` deprecated.

Esses warnings não bloqueiam o QA atual e não foram introduzidos por este ciclo.

## Resultado

`QA_CIVIL_AMBIENTAL_AUDIENCIA_ESTRATEGICA_FLOW_OK`

A Audiência Estratégica Civil/Ambiental V1 está validada em fluxo E2E automatizado com Contexto V2, geração assistida, aprovação e exportação PDF.

## Importância comercial

Este marco tira Civil/Ambiental do estado AMARELO operacional e cria evidência técnica para elevar o módulo a VERDE na matriz oficial de cobertura após atualização documental.

Civil/Ambiental é estratégico para escritórios porque envolve prova técnica, laudos, fiscalização, fotos, vídeos, vizinhos, nexo causal, obrigações de fazer/não fazer, cessação de dano, indenização e revisão humana cuidadosa.

O ciclo mantém a arquitetura correta:

- sem criar tipo documental duplicado;
- sem quebrar Cível fallback;
- sem quebrar Criminal;
- sem quebrar Trabalhista;
- sem quebrar Consumidor;
- sem quebrar Família;
- sem quebrar Previdenciário/BPC-LOAS;
- usando Contexto V2;
- usando `AUDIENCIA_ESTRATEGICA`;
- mantendo revisão e decisão final do advogado.

## Limites e responsabilidade

A plataforma organiza, estrutura, analisa, gera roteiros e controla documentos/provas.

A IA não substitui advogado, não assina, não protocola e não promete resultado jurídico.

O roteiro gerado é material de apoio estratégico para uso jurídico supervisionado.

## Próximo passo recomendado

Após merge do PR deste ciclo, atualizar:

- `docs/LEGAL_MODULE_COVERAGE_MATRIX_V1.md`
- `docs/AUDIENCIA_ESTRATEGICA_RELATORIO_COMERCIAL_TECNICO_V1.md`

Objetivo:

- mover Civil/Ambiental de AMARELO para VERDE;
- incluir Civil/Ambiental no relatório comercial/técnico da Audiência Estratégica;
- criar a tag documental posterior `v0.1.32-coverage-and-report-update-civil-ambiental-v1`.

## Status final do ciclo

Civil/Ambiental — Audiência Estratégica V1:

- helper específico: OK;
- detector de área: OK;
- perguntas por pessoa: OK;
- regressão dos módulos verdes: OK;
- E2E com geração/aprovação/PDF: OK;
- relatório QA: OK;
- pronto para PR.
