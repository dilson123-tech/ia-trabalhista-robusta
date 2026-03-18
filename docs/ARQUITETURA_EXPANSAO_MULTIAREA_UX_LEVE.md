# Arquitetura de Expansão Multiárea com UX Leve

## Objetivo
Expandir a IA Trabalhista Robusta para uma plataforma jurídica multiárea sem transformar o painel em uma experiência pesada, confusa ou travada para o advogado.

## Princípio central
A complexidade deve ficar no bastidor.
Na frente, o advogado deve enxergar:
- poucos botões
- fluxo guiado
- ações claras
- respostas rápidas
- contexto carregado sob demanda

## Separação macro da arquitetura

### Camada 1 — Núcleo comum da plataforma
Essa camada concentra o que é transversal:
- autenticação
- sessão
- multi-tenant
- escritórios e usuários
- clientes
- partes
- casos/processos
- documentos/anexos
- timeline/histórico
- artefatos
- auditoria
- billing/planos
- dashboards

### Camada 2 — Engines por área jurídica
Cada área jurídica deve existir como engine própria:
- trabalhista
- cível
- criminal
- família
- consumidor
- previdenciário
- futuras áreas

Cada engine deve definir:
- intake
- schema
- validações
- análise
- teses/fundamentos
- peças
- checklists
- critérios de risco/viabilidade

### Camada 3 — Motor de criação de processos/peças
Camada dedicada à produção jurídica operacional:
- intake guiado
- fatos
- partes
- documentos
- pedidos
- fundamentos
- geração de peça
- exportação
- revisão humana assistida

### Camada 4 — Orquestração assíncrona
Toda operação pesada deve ser preparada para processamento desacoplado:
- geração de análise
- geração de summary
- geração de report
- geração de PDF
- geração de peça
- processamento de anexos
- futuras tarefas de alto custo

## Regra de UX leve

### 1. Home principal sempre leve
A home do advogado não deve concentrar tudo.
Ela deve focar em:
- carteira principal
- busca
- filtro
- ações rápidas
- status de geração
- últimos artefatos

### 2. Entrada modular por área
Nada de misturar várias áreas na mesma tela.
Fluxo correto:
1. usuário escolhe a área
2. sistema carrega apenas aquele contexto
3. interface mostra apenas os campos relevantes

### 3. Carregamento sob demanda
Carregar de imediato apenas:
- dados básicos do caso
- status
- metadados
- ações primárias

Carregar sob demanda:
- texto completo de análise
- conteúdo completo de report
- preview de PDF
- formulários extensos de peça
- anexos pesados

### 4. Separação entre operações leves e pesadas

#### Operações leves
- listar casos
- filtrar
- buscar
- abrir detalhes
- alterar status
- arquivar
- navegar

#### Operações pesadas
- gerar análise
- gerar relatório
- gerar PDF
- gerar peça
- processar anexos
- consolidar artefatos

Operações pesadas não devem bloquear a navegação.

### 5. Fluxo assíncrono recomendado
Fluxo ideal:
1. usuário solicita ação pesada
2. sistema cria job
3. UI mostra status "gerando"
4. usuário continua navegando
5. artefato é disponibilizado quando concluído

### 6. Separação visual obrigatória dentro do caso
Dentro de cada caso, a navegação deve ser separada em blocos:
- Visão geral
- Avaliação
- Peças
- Documentos
- Histórico

Não misturar avaliação e criação de peça no mesmo bloco visual.

### 7. Evitar monólito visual
Evitar:
- cards gigantes
- excesso de dados no card
- múltiplas áreas misturadas na mesma listagem sem contexto
- excesso de botões simultâneos
- dependência de chamadas pesadas a cada clique

## Estratégia de escalabilidade técnica

### Backend
Evoluir para módulos:
- core
- platform
- engines
- document_factory
- jobs

### Frontend
Evoluir para:
- dashboard principal leve
- contextos por área
- telas específicas por operação
- carregamento lazy
- estados claros de loading, success e error

## Regras de produto
- o advogado não deve precisar entender a arquitetura interna
- o painel principal deve continuar simples
- a complexidade multiárea deve ficar encapsulada
- o crescimento funcional não pode degradar a percepção de velocidade
- a geração de valor precisa aumentar sem sacrificar usabilidade

## Primeira expansão prática recomendada
Primeira implementação concreta:
- criação de processo/peça trabalhista

Primeira peça recomendada:
- petição inicial trabalhista

## Objetivo final
Construir uma plataforma jurídica robusta, escalável e modular, mantendo experiência de uso simples e rápida para o advogado, mesmo com crescimento funcional e expansão multiárea.
