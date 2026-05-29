# QA Audiência Estratégica — Pessoas e Contexto V2

## Checkpoint

`QA_AUDIENCIA_PESSOAS_CONTEXTO_V2_OK`

## Objetivo

Validar a evolução da Audiência Estratégica para usar contexto estruturado do caso além da descrição textual.

Este QA confirma que o roteiro de audiência passa a considerar:

- partes cadastradas;
- papéis das partes;
- pessoas ativas e históricas;
- representantes;
- relações entre pessoas/partes;
- eventos relevantes;
- anexos/provas cadastrados;
- metadados estruturados do caso.

## Contexto do produto

A Audiência Estratégica já estava validada em três frentes:

- Cível com perguntas por pessoa no caso PRATIC SIDER;
- Criminal com geração, aprovação e PDF;
- Trabalhista com geração, aprovação e PDF.

O problema estratégico era que o roteiro ainda dependia muito da descrição do caso e da análise técnica.

Com o Contexto V2, a Audiência Estratégica começa a usar dados estruturados do próprio sistema, tornando o roteiro mais próximo de um caso real de escritório.

## Escopo técnico implementado

Foi criado o helper:

`_build_audiencia_context_snapshot(db, case, tenant_id)`

Esse helper consolida informações de:

- `CasePartyStateModel`;
- `CasePartyModel`;
- `CasePartyRepresentativeModel`;
- `CasePartyRelationshipModel`;
- `CasePartyEventModel`;
- `CaseAttachment`.

O contexto estruturado passa a ser incluído em:

- `combined_context_text`, usado para detectar nomes e gerar perguntas;
- `base_context`, exibido no roteiro de audiência como contexto adicional identificado no caso.

## Arquivos alterados/criados

- `backend/app/api/v1/routes/editable_documents.py`
- `backend/tests/test_audiencia_context_snapshot_v2.py`

## Teste principal

`test_audiencia_estrategica_uses_party_state_and_attachment_context`

## Fluxo validado no teste

O teste E2E cria:

1. usuário admin via seed controlado;
2. login autenticado;
3. caso cível QA;
4. estado de partes do caso;
5. partes/pessoas estruturadas;
6. relação entre partes;
7. anexo/prova PDF;
8. documento `AUDIENCIA_ESTRATEGICA`;
9. geração de roteiro assistido;
10. validação de que o contexto estruturado entrou no roteiro.

## Pessoas/partes validadas

O teste cadastra e valida no roteiro:

- PRATIC SIDER;
- Dilson Pereira;
- Edson Estevão;
- Rosangela de Lourdes Siqueira.

## Relação validada

O teste cadastra a relação:

`locacao_em_interesse_de_terceiro`

E valida que ela aparece no roteiro.

## Anexo/prova validado

O teste sobe o anexo:

`boletim_ocorrencia_furto_carreta.pdf`

Com descrição:

`Boletim de ocorrência sobre furto/desaparecimento da carreta.`

E valida que o anexo e a descrição aparecem no roteiro.

## Blocos/contextos validados

O teste confirma que o roteiro contém:

- `contexto estruturado adicional identificado no caso`;
- `partes/pessoas ativas cadastradas no caso`;
- `relações entre partes/pessoas`;
- `anexos/provas cadastrados no caso`.

## Regressões protegidas

O teste também confirma que o roteiro cível com contexto V2 não recebe contaminação de:

- Criminal:
  - `policial militar / agente da abordagem`;
- Trabalhista:
  - `reclamante / empregado`.

Além disso, a bateria relacionada manteve os testes de Audiência Estratégica Criminal e Trabalhista passando.

## Validações locais executadas

Teste V2:

`PYTHONPATH=backend pytest -q backend/tests/test_audiencia_context_snapshot_v2.py`

Bateria relacionada:

`PYTHONPATH=backend pytest -q backend/tests/test_audiencia_context_snapshot_v2.py backend/tests/test_trabalhista_audiencia_estrategica_questions.py backend/tests/test_trabalhista_audiencia_estrategica_flow.py backend/tests/test_criminal_audiencia_estrategica_questions.py backend/tests/test_criminal_audiencia_estrategica_flow.py`

Resultado observado:

`12 passed`

Compilação:

`python3 -m py_compile backend/app/api/v1/routes/editable_documents.py backend/tests/test_audiencia_context_snapshot_v2.py backend/tests/test_trabalhista_audiencia_estrategica_questions.py backend/tests/test_trabalhista_audiencia_estrategica_flow.py backend/tests/test_criminal_audiencia_estrategica_questions.py backend/tests/test_criminal_audiencia_estrategica_flow.py`

Resultado:

`PY_COMPILE_OK`

## Warnings

Foram exibidos warnings já conhecidos do projeto, como:

- `passlib` / `crypt` deprecated;
- `PydanticDeprecatedSince20`;
- `datetime.utcnow()` deprecated.

Esses warnings não bloqueiam o QA e não foram introduzidos por este ciclo.

## Resultado

`QA_AUDIENCIA_PESSOAS_CONTEXTO_V2_OK`

A Audiência Estratégica agora usa contexto estruturado de partes, relações, eventos e anexos/provas do caso.

## Importância comercial

Este marco aumenta muito o valor prático do produto.

Antes, a audiência dependia principalmente de descrição textual e análise. Agora, o sistema começa a aproveitar dados reais do próprio caso estruturado no painel.

Isso aproxima a Plataforma IA Jurídica Pro de um uso real de escritório, porque o advogado poderá organizar partes, testemunhas, relações e provas, e o roteiro de audiência passa a refletir esse contexto.

## Próximo passo recomendado

Após merge e tag deste ciclo, os próximos caminhos possíveis são:

1. expandir Audiência Estratégica para Consumidor;
2. criar extração/normalização mais inteligente de pessoas a partir de anexos e metadados;
3. melhorar a interface para cadastro guiado de partes, testemunhas e provas antes de gerar o roteiro.
