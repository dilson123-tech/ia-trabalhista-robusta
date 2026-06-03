# QA — Painel Operacional em Abas V1

Marco técnico: `v0.1.47-operational-panel-tabs-v1`

Checkpoint visual: `QA_OPERATIONAL_PANEL_TABS_VISUAL_OK`

## Objetivo

Validar visualmente o Painel Operacional em Abas V1 da Plataforma IA Jurídica Pro / IA Trabalhista Robusta.

Este ajuste prepara o painel para uso com caso real supervisionado por advogado, reduzindo poluição visual e evitando que múltiplos casos e módulos fiquem empilhados na mesma tela.

## Escopo técnico validado

O ciclo `v0.1.47-operational-panel-tabs-v1` adicionou:

- abas principais no painel:
  - Casos;
  - Editor e Provas;
  - Análise;
- lista compacta de casos;
- busca no topo da lista compacta;
- abertura de apenas um caso completo por vez;
- contagem como registros técnicos;
- uso de `case_number` como número/código visível do caso;
- `id` técnico exibido apenas como registro interno;
- módulos de expansão abrindo um módulo por vez;
- botão `Voltar aos módulos`.

## Validação visual executada

Itens validados:

- aba `Casos` visível;
- busca no topo da lista compacta;
- lista compacta exibindo casos sem empilhar todos os cards completos;
- abertura de apenas um caso completo por vez;
- troca de caso funcionando pela lista compacta;
- card completo mantendo prontidão, dossiê, WhatsApp, testemunhas e ações;
- `Caso: {case_number}` exibido na lista compacta;
- `Registro interno: #id` exibido discretamente no card completo;
- aba `Editor e Provas` visível;
- módulos de expansão visíveis;
- ao clicar em um módulo, abre somente o módulo selecionado;
- botão `Voltar aos módulos` funcionando;
- aba `Análise` acessível;
- caso selecionado preservado ao navegar entre abas;
- sem tela branca;
- sem erro visual crítico observado.

## Validação técnica

Executado com sucesso:

- `cd frontend && npm run build`

## Resultado

`QA_OPERATIONAL_PANEL_TABS_VISUAL_OK`

O painel operacional em abas está aprovado visualmente para o estágio atual do produto.

## Observações de produto

Este marco é necessário para uso com caso real, porque evita que a plataforma vire uma tela longa com vários casos e módulos empilhados.

O padrão correto passa a ser:

1. buscar caso;
2. abrir um caso por vez;
3. trabalhar no caso aberto;
4. trocar de aba conforme a etapa;
5. abrir um módulo por vez.

## Escopo preservado

- sem backend novo;
- sem migration;
- sem nova tabela;
- sem alteração de APIs;
- sem alterar checklist;
- sem alterar dossiê;
- sem alterar prontidão;
- sem alterar anexos;
- sem alterar testemunhas;
- sem alterar WhatsApp;
- sem alterar Editor Jurídico Vivo.

## Próximo passo recomendado

Preparar ambiente/tenant limpo para uso com caso real supervisionado, começando com `case_number` operacional `001`, sem expor registros de QA/teste no ambiente de demonstração ou escritório.
