# QA Família — Audiência Estratégica V1

## Checkpoint

`QA_FAMILIA_AUDIENCIA_ESTRATEGICA_FLOW_OK`

## Objetivo

Validar o primeiro fluxo E2E da Audiência Estratégica Família dentro da Plataforma IA Jurídica Pro.

Este QA confirma que o tipo documental `AUDIENCIA_ESTRATEGICA`, já validado nos fluxos Cível, Criminal, Trabalhista, Consumidor e Contexto V2, também funciona para contexto de Direito de Família sem criar novo tipo documental e sem quebrar os fluxos anteriores.

## Contexto do produto

A Audiência Estratégica é um recurso transversal premium da plataforma.

Ela não é petição inicial, contestação, manifestação ou peça para protocolo. É roteiro interno de apoio estratégico ao advogado, voltado para preparação de audiência, prova oral, perguntas por pessoa, perguntas perigosas, perguntas condicionais e revisão humana.

Na área de Família, o roteiro precisa apoiar especialmente a preparação de perguntas sobre:

- guarda;
- alimentos;
- convivência;
- divórcio;
- união estável;
- alienação parental;
- renda;
- rotina da criança;
- melhor interesse da criança/adolescente;
- estudo social;
- avaliação psicossocial;
- testemunhas familiares;
- testemunhas escolares;
- despesas;
- vínculos parentais;
- documentos e anexos.

## Escopo validado

O QA automatizado validou:

1. criação de usuário admin via seed controlado;
2. login autenticado;
3. criação de caso família QA;
4. criação de estado de partes;
5. criação de relação familiar entre partes;
6. upload de anexo/prova;
7. geração de análise técnica família;
8. criação de documento `AUDIENCIA_ESTRATEGICA`;
9. geração de roteiro assistido;
10. validação dos blocos esperados;
11. validação dos papéis de família;
12. validação do Contexto V2 no roteiro;
13. validação contra contaminação cível/criminal/trabalhista/consumidor;
14. aprovação de versão;
15. exportação PDF;
16. confirmação de PDF válido.

## Arquivos criados

- `backend/tests/test_familia_audiencia_estrategica_questions.py`
- `backend/tests/test_familia_audiencia_estrategica_flow.py`

## Testes principais

- `test_familia_audiencia_questions_use_family_roles`
- `test_familia_audiencia_estrategica_generates_approves_and_exports_pdf`

## Caso QA usado no teste E2E

O teste cria dinamicamente um caso com:

- Área jurídica: `família`
- Tipo de ação: `guarda_alimentos_convivencia`
- Documento: `audiencia_estrategica`
- Título: `Roteiro de Audiência Estratégica Família — QA`

O cenário simulado inclui:

- guarda;
- alimentos;
- convivência familiar;
- rotina da criança;
- escola;
- saúde;
- renda dos genitores;
- possível alienação parental;
- estudo social;
- avaliação psicossocial;
- mensagens entre genitores;
- testemunhas familiares;
- prova documental.

## Partes e contexto estruturado validados

O teste cadastra e valida no roteiro:

- Maria Genitora QA;
- João Genitor QA;
- Criança QA;
- Coordenadora Escolar QA.

Também valida a relação:

`vinculo_parental_e_cuidado_diario`

E o anexo/prova:

`relatorio_escolar_despesas_crianca.pdf`

Com descrição:

`Relatório escolar e comprovantes de despesas da criança.`

## Blocos de audiência validados

O teste confirmou a presença dos blocos:

- `sintese_tese_audiencia`
- `pontos_provar`
- `perguntas_pessoas_identificadas`
- `perguntas_repetitivas_perigosas`
- `perguntas_condicionais`
- `versao_curta`
- `pontos_confirmar_advogado`

## Papéis de família validados

O roteiro família gerado contém perguntas para:

- genitor / requerente;
- genitor / requerido;
- criança / adolescente, quando houver escuta adequada;
- responsável financeiro / alimentos;
- testemunha familiar;
- testemunha escolar / cuidador / profissional próximo;
- assistente social / equipe técnica;
- psicólogo / perito psicossocial.

Também foram validados termos estratégicos sensíveis como:

- guarda;
- alimentos;
- convivência;
- melhor interesse da criança;
- contexto estruturado adicional identificado no caso;
- material de apoio estratégico;
- revisão e decisão final do advogado.

## Blindagem contra contaminação

O teste confirmou ausência de termos indevidos dos fluxos anteriores, como:

- consumidor / autor;
- fornecedor / empresa ré;
- reclamante / empregado;
- preposto / representante da reclamada;
- vítima / ofendido;
- policial militar / agente da abordagem;
- representante da PRATIC SIDER;
- Edson Estevão;
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

`PYTHONPATH=backend pytest -q backend/tests/test_familia_audiencia_estrategica_flow.py`

Resultado observado:

`1 passed`

Bateria relacionada:

`PYTHONPATH=backend pytest -q backend/tests/test_familia_audiencia_estrategica_questions.py backend/tests/test_familia_audiencia_estrategica_flow.py backend/tests/test_consumidor_audiencia_estrategica_questions.py backend/tests/test_consumidor_audiencia_estrategica_flow.py backend/tests/test_audiencia_context_snapshot_v2.py backend/tests/test_trabalhista_audiencia_estrategica_questions.py backend/tests/test_trabalhista_audiencia_estrategica_flow.py backend/tests/test_criminal_audiencia_estrategica_questions.py backend/tests/test_criminal_audiencia_estrategica_flow.py`

Resultado observado:

`22 passed`

Compilação:

`python3 -m py_compile backend/app/api/v1/routes/editable_documents.py backend/tests/test_familia_audiencia_estrategica_questions.py backend/tests/test_familia_audiencia_estrategica_flow.py backend/tests/test_consumidor_audiencia_estrategica_questions.py backend/tests/test_consumidor_audiencia_estrategica_flow.py backend/tests/test_audiencia_context_snapshot_v2.py backend/tests/test_trabalhista_audiencia_estrategica_questions.py backend/tests/test_trabalhista_audiencia_estrategica_flow.py backend/tests/test_criminal_audiencia_estrategica_questions.py backend/tests/test_criminal_audiencia_estrategica_flow.py`

Resultado:

`PY_COMPILE_OK`

## Warnings

Foram exibidos warnings já conhecidos do projeto, incluindo `passlib` / `crypt` deprecated, `PydanticDeprecatedSince20` por uso de `class Config` e `datetime.utcnow()` deprecated.

Esses warnings não bloqueiam o QA atual e não foram introduzidos por este ciclo.

## Resultado

`QA_FAMILIA_AUDIENCIA_ESTRATEGICA_FLOW_OK`

A Audiência Estratégica Família V1 está validada em fluxo E2E automatizado com contexto estruturado, geração, aprovação e exportação PDF.

## Importância comercial

Este marco amplia a Plataforma IA Jurídica Pro para uma área de alto valor humano e jurídico.

Família é estratégica para escritórios porque envolve casos sensíveis de guarda, alimentos, convivência, divórcio, união estável, alienação parental, estudo social, renda, rotina da criança e provas testemunhais/documentais.

O ciclo mantém a arquitetura correta:

- sem criar tipo documental duplicado;
- sem quebrar Cível;
- sem quebrar Criminal;
- sem quebrar Trabalhista;
- sem quebrar Consumidor;
- usando Contexto V2;
- com controle de versão;
- com aprovação;
- com PDF;
- com QA automatizado;
- com linguagem supervisionada.

## Próximo passo recomendado

Após merge e tag deste ciclo, os próximos caminhos sugeridos são:

1. expandir Audiência Estratégica para Previdenciário/BPC-LOAS;
2. expandir Audiência Estratégica para Civil/Ambiental;
3. melhorar interface/cadastro guiado de partes, testemunhas e provas antes da geração do roteiro;
4. atualizar o relatório comercial/técnico da Audiência Estratégica para incluir Família.
