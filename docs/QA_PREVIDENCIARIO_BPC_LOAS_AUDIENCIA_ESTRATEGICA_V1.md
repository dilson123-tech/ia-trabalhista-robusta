# QA Previdenciário/BPC-LOAS — Audiência Estratégica V1

## Checkpoint

`QA_PREVIDENCIARIO_BPC_LOAS_AUDIENCIA_ESTRATEGICA_FLOW_OK`

## Objetivo

Validar o primeiro fluxo E2E da Audiência Estratégica Previdenciário/BPC-LOAS dentro da Plataforma IA Jurídica Pro.

Este QA confirma que o tipo documental `AUDIENCIA_ESTRATEGICA`, já validado nos fluxos Cível, Criminal, Trabalhista, Consumidor, Família e Contexto V2, também funciona para contexto previdenciário/BPC-LOAS sem criar novo tipo documental e sem quebrar os fluxos anteriores.

## Contexto do produto

A Audiência Estratégica é um recurso transversal premium da plataforma.

Ela não é petição inicial, recurso, manifestação, parecer definitivo ou peça automática para protocolo. É roteiro interno de apoio estratégico ao advogado, voltado para preparação de audiência, prova oral, perícia, perguntas por pessoa, perguntas perigosas, perguntas condicionais e revisão humana.

Na área Previdenciário/BPC-LOAS, o roteiro precisa apoiar especialmente a preparação de perguntas sobre:

- BPC/LOAS;
- benefício assistencial;
- benefício por incapacidade;
- deficiência;
- impedimento de longo prazo;
- incapacidade funcional;
- laudos médicos;
- receitas;
- exames;
- prontuários;
- CadÚnico;
- NIS;
- renda familiar;
- grupo familiar;
- cuidador;
- avaliação social;
- perícia médica;
- INSS;
- indeferimento administrativo;
- rotina diária;
- vulnerabilidade;
- despesas essenciais;
- prova testemunhal.

## Escopo validado

O QA automatizado validou:

1. criação de usuário admin via seed controlado;
2. login autenticado;
3. criação de caso previdenciário/BPC-LOAS QA;
4. criação de estado de partes;
5. criação de relação de cuidado/dependência;
6. upload de anexo/prova médica/social;
7. geração de análise técnica previdenciária;
8. criação de documento `AUDIENCIA_ESTRATEGICA`;
9. geração de roteiro assistido;
10. validação dos blocos esperados;
11. validação dos papéis previdenciários/BPC-LOAS;
12. validação do Contexto V2 no roteiro;
13. validação contra contaminação cível/criminal/trabalhista/consumidor/família;
14. aprovação de versão;
15. exportação PDF;
16. confirmação de PDF válido.

## Arquivos criados

- `backend/tests/test_previdenciario_audiencia_estrategica_questions.py`
- `backend/tests/test_previdenciario_audiencia_estrategica_flow.py`

## Testes principais

- `test_previdenciario_audiencia_questions_use_bpc_loas_roles`
- `test_previdenciario_bpc_loas_audiencia_estrategica_generates_approves_and_exports_pdf`

## Caso QA usado no teste E2E

O teste cria dinamicamente um caso com:

- Área jurídica: `previdenciário`
- Tipo de ação: `bpc_loas`
- Documento: `audiencia_estrategica`
- Título: `Roteiro de Audiência Estratégica Previdenciário/BPC-LOAS — QA`

O cenário simulado inclui:

- requerente em situação de vulnerabilidade;
- deficiência ou impedimento de longo prazo;
- renda familiar baixa;
- CadÚnico;
- NIS;
- laudos médicos;
- receitas;
- exames;
- gastos com remédios;
- familiar cuidador;
- avaliação social;
- perícia médica;
- indeferimento administrativo do INSS;
- grupo familiar;
- renda per capita;
- barreiras sociais;
- incapacidade funcional;
- documentos médicos;
- estudo social;
- rotina diária;
- dependência de terceiros;
- prova testemunhal.

## Partes e contexto estruturado validados

O teste cadastra e valida no roteiro:

- Ana Requerente QA;
- Carlos Cuidador QA;
- Dra. Médica Assistente QA;
- INSS QA.

Também valida a relação:

`cuidado_diario_e_dependencia_funcional`

E o anexo/prova:

`laudo_medico_cadunico_renda_bpc_loas.pdf`

Com descrição:

`Laudo médico, CadÚnico e comprovantes de renda familiar para BPC/LOAS.`

## Blocos de audiência validados

O teste confirmou a presença dos blocos:

- `sintese_tese_audiencia`
- `pontos_provar`
- `perguntas_pessoas_identificadas`
- `perguntas_repetitivas_perigosas`
- `perguntas_condicionais`
- `versao_curta`
- `pontos_confirmar_advogado`

## Papéis previdenciários/BPC-LOAS validados

O roteiro previdenciário/BPC-LOAS gerado contém perguntas para:

- requerente / segurado;
- familiar cuidador / responsável pela rotina;
- representante legal / procurador;
- médico assistente / profissional de saúde;
- perito médico;
- assistente social / avaliador social;
- servidor / representante do INSS;
- testemunha sobre rotina, incapacidade e vulnerabilidade.

Também foram validados termos estratégicos sensíveis como:

- BPC/LOAS;
- CadÚnico;
- renda familiar;
- laudos médicos;
- perícia médica;
- avaliação social;
- benefício assistencial;
- contexto estruturado adicional identificado no caso;
- material de apoio estratégico;
- revisão e decisão final do advogado.

## Blindagem contra contaminação

O teste confirmou ausência de termos indevidos dos fluxos anteriores, como:

- genitor / requerente;
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

`PYTHONPATH=backend pytest -q backend/tests/test_previdenciario_audiencia_estrategica_flow.py`

Resultado observado:

`1 passed`

Bateria relacionada:

`PYTHONPATH=backend pytest -q backend/tests/test_previdenciario_audiencia_estrategica_questions.py backend/tests/test_previdenciario_audiencia_estrategica_flow.py backend/tests/test_familia_audiencia_estrategica_questions.py backend/tests/test_familia_audiencia_estrategica_flow.py backend/tests/test_consumidor_audiencia_estrategica_questions.py backend/tests/test_consumidor_audiencia_estrategica_flow.py backend/tests/test_audiencia_context_snapshot_v2.py backend/tests/test_trabalhista_audiencia_estrategica_questions.py backend/tests/test_trabalhista_audiencia_estrategica_flow.py backend/tests/test_criminal_audiencia_estrategica_questions.py backend/tests/test_criminal_audiencia_estrategica_flow.py`

Resultado observado:

`27 passed`

Compilação:

`python3 -m py_compile backend/app/api/v1/routes/editable_documents.py backend/tests/test_previdenciario_audiencia_estrategica_questions.py backend/tests/test_previdenciario_audiencia_estrategica_flow.py backend/tests/test_familia_audiencia_estrategica_questions.py backend/tests/test_familia_audiencia_estrategica_flow.py backend/tests/test_consumidor_audiencia_estrategica_questions.py backend/tests/test_consumidor_audiencia_estrategica_flow.py backend/tests/test_audiencia_context_snapshot_v2.py backend/tests/test_trabalhista_audiencia_estrategica_questions.py backend/tests/test_trabalhista_audiencia_estrategica_flow.py backend/tests/test_criminal_audiencia_estrategica_questions.py backend/tests/test_criminal_audiencia_estrategica_flow.py`

Resultado:

`PY_COMPILE_OK`

## Warnings

Foram exibidos warnings já conhecidos do projeto, incluindo `passlib` / `crypt` deprecated, `PydanticDeprecatedSince20` por uso de `class Config` e `datetime.utcnow()` deprecated.

Esses warnings não bloqueiam o QA atual e não foram introduzidos por este ciclo.

## Resultado

`QA_PREVIDENCIARIO_BPC_LOAS_AUDIENCIA_ESTRATEGICA_FLOW_OK`

A Audiência Estratégica Previdenciário/BPC-LOAS V1 está validada em fluxo E2E automatizado com contexto estruturado, geração, aprovação e exportação PDF.

## Importância comercial

Este marco tira Previdenciário/BPC-LOAS do estado pendente na matriz de cobertura e leva o módulo para uma área de alto valor prático.

Previdenciário/BPC-LOAS é estratégico para escritórios porque envolve muitos documentos, prova médica, prova social, renda familiar, CadÚnico, perícia, INSS, cuidador, vulnerabilidade e revisão humana cuidadosa.

O ciclo mantém a arquitetura correta:

- sem criar tipo documental duplicado;
- sem quebrar Cível;
- sem quebrar Criminal;
- sem quebrar Trabalhista;
- sem quebrar Consumidor;
- sem quebrar Família;
- usando Contexto V2;
- com controle de versão;
- com aprovação;
- com PDF;
- com QA automatizado;
- com linguagem supervisionada.

## Próximo passo recomendado

Após merge e tag deste ciclo, os próximos caminhos sugeridos são:

1. atualizar a matriz de cobertura para mudar Previdenciário/BPC-LOAS de VERMELHO para VERDE;
2. atualizar o relatório comercial/técnico da Audiência Estratégica para incluir Previdenciário/BPC-LOAS;
3. expandir Audiência Estratégica para Civil/Ambiental;
4. melhorar interface/cadastro guiado de partes, testemunhas e provas antes da geração do roteiro.
