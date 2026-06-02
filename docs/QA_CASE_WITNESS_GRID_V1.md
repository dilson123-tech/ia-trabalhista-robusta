# QA — Grade de Testemunhas/Depoentes V1

Marco técnico: `v0.1.38-case-witness-grid-v1`

Checkpoint visual: `QA_CASE_WITNESS_GRID_VISUAL_OK`

## Objetivo

Validar visualmente a Grade de Testemunhas/Depoentes V1 no painel da Plataforma IA Jurídica Pro / IA Trabalhista Robusta, como parte da esteira operacional real de escritório.

Este recurso não substitui a análise do advogado. Ele organiza pessoas relevantes para prova oral, audiência e preparação estratégica supervisionada.

## Escopo validado

A Grade de Testemunhas/Depoentes V1 foi implementada usando a fundação já existente:

- `case_party_states`;
- `case_parties`;
- `party_metadata`.

Não foi criada tabela nova.

Não houve migration neste ciclo.

## Validação técnica anterior

Antes do QA visual, foram validados:

- `python3 -m py_compile backend/app/api/v1/routes/case_party_states.py backend/app/schemas/case_party_state.py backend/tests/test_case_party_states_flow.py`;
- `PYTHONPATH=backend pytest -q backend/tests/test_case_party_states_flow.py`;
- `cd frontend && npm run build`.

Resultado técnico:

- backend OK;
- testes da grade OK;
- frontend build OK.

## Validação visual executada

Ambiente visual:

- frontend local em `127.0.0.1:5173`;
- painel operacional de casos;
- card de caso ativo com cliente WhatsApp e histórico.

Itens validados no card do caso:

- bloco `Testemunhas/depoentes` visível;
- botão `Atualizar` visível;
- botão `Adicionar V1` visível;
- testemunha/depoente cadastrado aparece no card;
- papel/status exibido como `testemunha / pendente`;
- campo `O que sabe` exibido;
- campo `Confirma` exibido;
- campo `Risco` exibido;
- campo `Pontos sensíveis` exibido;
- histórico de contatos continua abaixo, separado e sem quebra visual.

## Persistência validada

Foi realizado reload da página e, em seguida, clique em `Atualizar` na Grade de Testemunhas/Depoentes.

Resultado:

- a testemunha `Cliente WhatsApp QA` continuou aparecendo;
- os dados persistiram no estado estruturado do caso;
- a grade continuou funcional após recarregar a página.

## Resultado

`QA_CASE_WITNESS_GRID_VISUAL_OK`

A Grade de Testemunhas/Depoentes V1 está aprovada visualmente para o estágio atual do produto.

## Observações de produto

Este marco aproxima a plataforma de uma esteira real de escritório, porque permite organizar:

- testemunhas;
- depoentes;
- prepostos;
- representantes;
- peritos;
- fiscais;
- cuidadores;
- vizinhos/comunidade;
- pessoas relevantes para prova oral.

A integração futura natural é alimentar a Audiência Estratégica com pessoas já cadastradas no caso.

## Escopo preservado

- sem automação jurídica sem advogado;
- sem promessa de viabilidade jurídica automática;
- sem instrução de testemunha a mentir;
- sem sugestão de resposta pronta;
- sem nova área jurídica neste ciclo;
- sem duplicar estrutura de pessoas;
- sem migration;
- sem reconstruir arquitetura.

## Próximo passo recomendado

Iniciar a Prioridade 2 do handoff:

`Checklist de Provas e Pendências V1`

Esse próximo recurso deve organizar o que já foi recebido, o que falta pedir ao cliente e o que precisa ser validado pelo advogado antes de o caso ficar operacionalmente pronto.
