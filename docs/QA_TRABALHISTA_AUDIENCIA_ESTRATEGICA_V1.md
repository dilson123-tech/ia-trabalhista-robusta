# QA Trabalhista — Audiência Estratégica V1

## Checkpoint

`QA_TRABALHISTA_AUDIENCIA_ESTRATEGICA_FLOW_OK`

## Objetivo

Validar o primeiro fluxo E2E da Audiência Estratégica Trabalhista dentro da Plataforma IA Jurídica Pro.

Este QA confirma que o tipo documental `AUDIENCIA_ESTRATEGICA`, já validado nos fluxos cível e criminal, também funciona para contexto trabalhista sem criar novo tipo documental e sem quebrar os fluxos anteriores.

## Contexto do produto

A Audiência Estratégica é um recurso transversal premium da plataforma.

Ela não é petição inicial, contestação, manifestação ou peça para protocolo. É roteiro interno de apoio estratégico ao advogado, voltado para preparação de audiência, prova oral, perguntas por pessoa, perguntas perigosas, perguntas condicionais e revisão humana.

Na área trabalhista, o roteiro precisa apoiar especialmente a preparação de perguntas sobre:

- vínculo e função;
- jornada;
- intervalo intrajornada;
- horas extras;
- controle de ponto;
- banco de horas;
- holerites;
- verbas rescisórias;
- FGTS;
- preposto;
- testemunhas;
- gestor/encarregado;
- RH;
- documentos de segurança do trabalho;
- EPI;
- insalubridade/periculosidade quando houver;
- prova pericial.

## Escopo validado

O QA automatizado validou:

1. criação de usuário admin via seed controlado;
2. login autenticado;
3. criação de caso trabalhista QA;
4. geração de análise técnica trabalhista;
5. criação de documento `AUDIENCIA_ESTRATEGICA`;
6. geração de roteiro assistido;
7. validação dos blocos esperados;
8. validação dos papéis trabalhistas;
9. validação contra contaminação criminal/cível;
10. aprovação de versão;
11. exportação PDF;
12. confirmação de PDF válido.

## Arquivos criados

- `backend/tests/test_trabalhista_audiencia_estrategica_questions.py`
- `backend/tests/test_trabalhista_audiencia_estrategica_flow.py`

## Testes principais

- `test_trabalhista_audiencia_questions_use_labor_roles`
- `test_trabalhista_audiencia_estrategica_generates_approves_and_exports_pdf`

## Caso QA usado no teste E2E

O teste cria dinamicamente um caso com:

- Área jurídica: `trabalhista`
- Tipo de ação: `horas_extras`
- Documento: `audiencia_estrategica`
- Título: `Roteiro de Audiência Estratégica Trabalhista — QA`

O cenário simulado inclui:

- reclamação trabalhista;
- jornada superior à registrada;
- supressão parcial de intervalo intrajornada;
- horas extras;
- reflexos em DSR, férias, 13º salário e FGTS;
- verbas rescisórias;
- controles de ponto;
- holerites;
- TRCT;
- extrato analítico do FGTS;
- mensagens com gestor;
- preposto;
- testemunhas;
- RH;
- EPI;
- possível insalubridade;
- documentos de segurança do trabalho.

## Blocos de audiência validados

O teste confirmou a presença dos blocos:

- `sintese_tese_audiencia`
- `pontos_provar`
- `perguntas_pessoas_identificadas`
- `perguntas_repetitivas_perigosas`
- `perguntas_condicionais`
- `versao_curta`
- `pontos_confirmar_advogado`

## Papéis trabalhistas validados

O roteiro trabalhista gerado contém perguntas para:

- reclamante / empregado;
- preposto / representante da reclamada;
- testemunha do reclamante;
- testemunha da reclamada;
- gestor / encarregado;
- RH / responsável por folha, ponto e rescisão;
- técnico de segurança / medicina do trabalho;
- perito / responsável por laudo trabalhista.

Também foram validados termos estratégicos sensíveis como:

- controle de ponto;
- FGTS;
- verbas rescisórias;
- risco ocupacional;
- material de apoio estratégico;
- revisão e decisão final do advogado.

## Blindagem contra contaminação

O teste confirmou ausência de termos indevidos do fluxo criminal/cível, como:

- vítima / ofendido;
- policial militar / agente da abordagem;
- delegado / autoridade policial;
- acusado / réu;
- representante da PRATIC SIDER;
- Edson Estevão;
- Rosangela de Lourdes Siqueira;
- locação da carreta.

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

Teste E2E:

`PYTHONPATH=backend pytest -q backend/tests/test_trabalhista_audiencia_estrategica_flow.py`

Resultado esperado/observado:

`1 passed`

Testes relacionados:

`PYTHONPATH=backend pytest -q backend/tests/test_trabalhista_audiencia_estrategica_questions.py backend/tests/test_trabalhista_audiencia_estrategica_flow.py backend/tests/test_criminal_audiencia_estrategica_questions.py backend/tests/test_criminal_audiencia_estrategica_flow.py backend/tests/test_criminal_assisted_draft_flow.py`

Resultado observado:

`13 passed`

Compilação:

`python3 -m py_compile backend/app/api/v1/routes/editable_documents.py backend/tests/test_trabalhista_audiencia_estrategica_questions.py backend/tests/test_trabalhista_audiencia_estrategica_flow.py backend/tests/test_criminal_audiencia_estrategica_questions.py backend/tests/test_criminal_audiencia_estrategica_flow.py`

Resultado:

`PY_COMPILE_OK`

## Warnings

Foram exibidos warnings já conhecidos do projeto, incluindo `passlib` / `crypt` deprecated, `PydanticDeprecatedSince20` por uso de `class Config` e `datetime.utcnow()` deprecated.

Esses warnings não bloqueiam o QA atual e não foram introduzidos por este ciclo.

## Resultado

`QA_TRABALHISTA_AUDIENCIA_ESTRATEGICA_FLOW_OK`

A Audiência Estratégica Trabalhista V1 está validada em fluxo E2E automatizado com geração, aprovação e exportação PDF.

## Importância comercial

Este marco é especialmente relevante porque o produto nasceu como IA Trabalhista Robusta e agora passa a ter Audiência Estratégica Trabalhista validada no mesmo padrão de qualidade aplicado ao Criminal.

Isso fortalece a Plataforma IA Jurídica Pro como produto multiárea real para escritórios, mantendo a mesma base técnica:

- sem criar tipo documental duplicado;
- sem quebrar Cível;
- sem quebrar Criminal;
- com controle de versão;
- com aprovação;
- com PDF;
- com QA automatizado;
- com linguagem supervisionada.

## Próximo passo recomendado

Após merge e tag deste ciclo, o próximo passo sugerido é escolher entre:

1. expandir Audiência Estratégica para Consumidor, Família, Previdenciário/BPC-LOAS ou Civil/Ambiental;
2. melhorar a detecção de pessoas/anexos/metadados para roteiros mais personalizados em todas as áreas.
