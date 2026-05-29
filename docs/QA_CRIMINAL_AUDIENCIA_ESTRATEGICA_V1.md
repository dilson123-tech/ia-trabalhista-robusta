# QA Criminal — Audiência Estratégica V1

## Checkpoint

`QA_CRIMINAL_AUDIENCIA_ESTRATEGICA_FLOW_OK`

## Objetivo

Validar o primeiro fluxo E2E da Audiência Estratégica Criminal dentro da Plataforma IA Jurídica Pro.

Este QA confirma que o tipo documental `AUDIENCIA_ESTRATEGICA`, já existente e validado no fluxo cível, também funciona para contexto criminal/penal sem criar novo tipo documental e sem quebrar o fluxo cível anterior.

## Contexto do produto

A Audiência Estratégica é um recurso transversal premium da plataforma.

Ela não é petição, contestação, manifestação ou peça para protocolo. É roteiro interno de apoio estratégico ao advogado, voltado para preparação de audiência, prova oral, perguntas por pessoa, perguntas perigosas, perguntas condicionais e revisão humana.

Na área criminal, o material exige cautela reforçada, pois não pode prometer resultado, afirmar culpa ou inocência definitiva, inventar prova, inventar fatos, orientar estratégia ilegal, estimular autoincriminação ou substituir a decisão técnica do advogado.

## Escopo validado

O QA automatizado validou:

1. criação de usuário admin via seed controlado;
2. login autenticado;
3. criação de caso criminal QA;
4. geração de análise técnica criminal;
5. criação de documento `AUDIENCIA_ESTRATEGICA`;
6. geração de roteiro assistido;
7. validação dos blocos esperados;
8. validação dos papéis criminais;
9. validação contra contaminação cível/trabalhista;
10. aprovação de versão;
11. exportação PDF;
12. confirmação de PDF válido.

## Arquivo de teste criado

`backend/tests/test_criminal_audiencia_estrategica_flow.py`

## Teste principal

`test_criminal_audiencia_estrategica_generates_approves_and_exports_pdf`

## Caso QA usado no teste automatizado

O teste cria dinamicamente um caso com:

- Área jurídica: `criminal`
- Tipo de ação: `resposta_acusacao`
- Documento: `audiencia_estrategica`
- Título: `Roteiro de Audiência Estratégica Criminal — QA`

O cenário simulado inclui denúncia, decisão de recebimento, mandado de citação, boletim de ocorrência, depoimentos policiais, vítima/ofendido, testemunhas de acusação, testemunhas de defesa, laudo pericial, conversas digitais, cadeia de custódia, risco de autoincriminação, contraditório e ampla defesa.

## Blocos de audiência validados

O teste confirmou a presença dos blocos:

- `sintese_tese_audiencia`
- `pontos_provar`
- `perguntas_pessoas_identificadas`
- `perguntas_repetitivas_perigosas`
- `perguntas_condicionais`
- `versao_curta`
- `pontos_confirmar_advogado`

## Papéis criminais validados

O roteiro criminal gerado contém perguntas para:

- vítima / ofendido;
- policial militar / agente da abordagem;
- policial civil / investigador;
- delegado / autoridade policial;
- testemunha de acusação;
- testemunha de defesa;
- acusado / réu;
- perito / responsável por laudo.

Também foram validados termos estratégicos sensíveis como cadeia de custódia, risco de autoincriminação, material de apoio estratégico e revisão/decisão final do advogado.

## Blindagem contra contaminação

O teste confirmou ausência de termos indevidos do fluxo cível/trabalhista, como:

- representante da PRATIC SIDER;
- Edson Estevão;
- Rosangela de Lourdes Siqueira;
- locação da carreta;
- FGTS;
- CLT;
- verbas rescisórias;
- vara do trabalho;
- obrigação de fazer;
- direito de vizinhança.

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

`PYTHONPATH=backend pytest -q backend/tests/test_criminal_audiencia_estrategica_flow.py`

Resultado:

`1 passed`

Testes relacionados:

`PYTHONPATH=backend pytest -q backend/tests/test_criminal_audiencia_estrategica_questions.py backend/tests/test_criminal_audiencia_estrategica_flow.py backend/tests/test_criminal_assisted_draft_flow.py`

Resultado:

`7 passed`

Compilação:

`python3 -m py_compile backend/tests/test_criminal_audiencia_estrategica_flow.py backend/tests/test_criminal_audiencia_estrategica_questions.py backend/app/api/v1/routes/editable_documents.py`

Resultado:

`PY_COMPILE_OK`

## Warnings

Foram exibidos warnings já conhecidos do projeto, incluindo `passlib` / `crypt` deprecated, `PydanticDeprecatedSince20` por uso de `class Config` e `datetime.utcnow()` deprecated.

Esses warnings não bloqueiam o QA atual e não foram introduzidos por este ciclo.

## Resultado

`QA_CRIMINAL_AUDIENCIA_ESTRATEGICA_FLOW_OK`

A Audiência Estratégica Criminal V1 está validada em fluxo E2E automatizado com geração, aprovação e exportação PDF.

## Importância comercial

Este marco prova que a Audiência Estratégica deixou de ser apenas um recurso cível validado e passou a funcionar também no contexto criminal.

Isso fortalece a Plataforma IA Jurídica Pro como produto multiárea real para escritórios, mantendo a mesma base técnica:

- sem criar tipo documental duplicado;
- sem quebrar o Cível;
- com controle de versão;
- com aprovação;
- com PDF;
- com QA automatizado;
- com linguagem supervisionada.

## Próximo passo recomendado

Após merge e tag deste QA, o próximo ciclo sugerido é expandir a Audiência Estratégica para outra área prioritária ou melhorar a detecção de pessoas/anexos/metadados para roteiros mais personalizados.
