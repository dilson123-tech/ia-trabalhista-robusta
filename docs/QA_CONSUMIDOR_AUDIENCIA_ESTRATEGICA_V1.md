# QA Consumidor — Audiência Estratégica V1

## Checkpoint

`QA_CONSUMIDOR_AUDIENCIA_ESTRATEGICA_FLOW_OK`

## Objetivo

Validar o primeiro fluxo E2E da Audiência Estratégica Consumidor dentro da Plataforma IA Jurídica Pro.

Este QA confirma que o tipo documental `AUDIENCIA_ESTRATEGICA`, já validado nos fluxos Cível, Criminal, Trabalhista e Contexto V2, também funciona para contexto de Direito do Consumidor sem criar novo tipo documental e sem quebrar os fluxos anteriores.

## Contexto do produto

A Audiência Estratégica é um recurso transversal premium da plataforma.

Ela não é petição inicial, contestação, manifestação ou peça para protocolo. É roteiro interno de apoio estratégico ao advogado, voltado para preparação de audiência, prova oral, perguntas por pessoa, perguntas perigosas, perguntas condicionais e revisão humana.

Na área de Consumidor, o roteiro precisa apoiar especialmente a preparação de perguntas sobre:

- relação de consumo;
- contratação;
- cobrança indevida;
- negativação;
- falha de atendimento;
- protocolos;
- SAC;
- ouvidoria;
- banco/fornecedor;
- oferta/publicidade;
- produto ou serviço;
- dano material;
- dano moral;
- obrigação de fazer/não fazer;
- baixa de restrição;
- restituição;
- prova documental;
- contexto estruturado de partes e anexos.

## Escopo validado

O QA automatizado validou:

1. criação de usuário admin via seed controlado;
2. login autenticado;
3. criação de caso consumidor QA;
4. criação de estado de partes;
5. criação de relação de consumo entre partes;
6. upload de anexo/prova;
7. geração de análise técnica consumidor;
8. criação de documento `AUDIENCIA_ESTRATEGICA`;
9. geração de roteiro assistido;
10. validação dos blocos esperados;
11. validação dos papéis de consumidor;
12. validação do Contexto V2 no roteiro;
13. validação contra contaminação cível/criminal/trabalhista;
14. aprovação de versão;
15. exportação PDF;
16. confirmação de PDF válido.

## Arquivos criados

- `backend/tests/test_consumidor_audiencia_estrategica_questions.py`
- `backend/tests/test_consumidor_audiencia_estrategica_flow.py`

## Testes principais

- `test_consumidor_audiencia_questions_use_consumer_roles`
- `test_consumidor_audiencia_estrategica_generates_approves_and_exports_pdf`

## Caso QA usado no teste E2E

O teste cria dinamicamente um caso com:

- Área jurídica: `consumidor`
- Tipo de ação: `cobranca_indevida_negativacao`
- Documento: `audiencia_estrategica`
- Título: `Roteiro de Audiência Estratégica Consumidor — QA`

O cenário simulado inclui:

- banco/fornecedor;
- cobrança indevida;
- negativação;
- contrato contestado;
- faturas;
- protocolos de SAC;
- reclamação em ouvidoria;
- prints de aplicativo;
- comprovantes de pagamento;
- inscrição em cadastro restritivo;
- pedido de baixa da negativação;
- tentativa administrativa de solução;
- dano material;
- dano moral.

## Partes e contexto estruturado validados

O teste cadastra e valida no roteiro:

- Cliente Consumidor QA;
- Banco Alfa QA;
- Atendente SAC QA.

Também valida a relação:

`relacao_de_consumo_bancaria`

E o anexo/prova:

`protocolo_sac_negativacao_consumidor.pdf`

Com descrição:

`Comprovante de negativação e protocolos de atendimento do consumidor.`

## Blocos de audiência validados

O teste confirmou a presença dos blocos:

- `sintese_tese_audiencia`
- `pontos_provar`
- `perguntas_pessoas_identificadas`
- `perguntas_repetitivas_perigosas`
- `perguntas_condicionais`
- `versao_curta`
- `pontos_confirmar_advogado`

## Papéis de consumidor validados

O roteiro consumidor gerado contém perguntas para:

- consumidor / autor;
- fornecedor / empresa ré;
- atendente / suporte / SAC / ouvidoria;
- representante comercial / vendedor / loja;
- testemunha do consumidor;
- testemunha do fornecedor;
- responsável financeiro / cobrança / negativação;
- técnico / assistência / perito do produto ou serviço.

Também foram validados termos estratégicos sensíveis como:

- cobrança indevida;
- negativação;
- protocolo;
- relação de consumo;
- contexto estruturado adicional identificado no caso;
- material de apoio estratégico;
- revisão e decisão final do advogado.

## Blindagem contra contaminação

O teste confirmou ausência de termos indevidos dos fluxos anteriores, como:

- reclamante / empregado;
- preposto / representante da reclamada;
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

`PYTHONPATH=backend pytest -q backend/tests/test_consumidor_audiencia_estrategica_flow.py`

Resultado observado:

`1 passed`

Bateria relacionada:

`PYTHONPATH=backend pytest -q backend/tests/test_consumidor_audiencia_estrategica_questions.py backend/tests/test_consumidor_audiencia_estrategica_flow.py backend/tests/test_audiencia_context_snapshot_v2.py backend/tests/test_trabalhista_audiencia_estrategica_questions.py backend/tests/test_trabalhista_audiencia_estrategica_flow.py backend/tests/test_criminal_audiencia_estrategica_questions.py backend/tests/test_criminal_audiencia_estrategica_flow.py`

Resultado observado:

`17 passed`

Compilação:

`python3 -m py_compile backend/app/api/v1/routes/editable_documents.py backend/tests/test_consumidor_audiencia_estrategica_questions.py backend/tests/test_consumidor_audiencia_estrategica_flow.py backend/tests/test_audiencia_context_snapshot_v2.py backend/tests/test_trabalhista_audiencia_estrategica_questions.py backend/tests/test_trabalhista_audiencia_estrategica_flow.py backend/tests/test_criminal_audiencia_estrategica_questions.py backend/tests/test_criminal_audiencia_estrategica_flow.py`

Resultado:

`PY_COMPILE_OK`

## Warnings

Foram exibidos warnings já conhecidos do projeto, incluindo `passlib` / `crypt` deprecated, `PydanticDeprecatedSince20` por uso de `class Config` e `datetime.utcnow()` deprecated.

Esses warnings não bloqueiam o QA atual e não foram introduzidos por este ciclo.

## Resultado

`QA_CONSUMIDOR_AUDIENCIA_ESTRATEGICA_FLOW_OK`

A Audiência Estratégica Consumidor V1 está validada em fluxo E2E automatizado com contexto estruturado, geração, aprovação e exportação PDF.

## Importância comercial

Este marco amplia a Plataforma IA Jurídica Pro para uma área de alto volume comercial.

Consumidor é estratégico para escritórios porque envolve casos recorrentes de cobrança indevida, negativação, falha bancária, telecom, energia, produto/serviço, contrato, atendimento e dano moral.

O ciclo mantém a arquitetura correta:

- sem criar tipo documental duplicado;
- sem quebrar Cível;
- sem quebrar Criminal;
- sem quebrar Trabalhista;
- usando Contexto V2;
- com controle de versão;
- com aprovação;
- com PDF;
- com QA automatizado;
- com linguagem supervisionada.

## Próximo passo recomendado

Após merge e tag deste ciclo, os próximos caminhos sugeridos são:

1. expandir Audiência Estratégica para Família;
2. expandir Audiência Estratégica para Previdenciário/BPC-LOAS;
3. melhorar interface/cadastro guiado de partes, testemunhas e provas antes da geração do roteiro;
4. criar um relatório consolidado da evolução do módulo Audiência Estratégica para apresentação comercial.
