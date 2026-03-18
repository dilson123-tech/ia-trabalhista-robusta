# Evolução Oficial — IA Trabalhista Robusta para Plataforma Jurídica Robusta

## Natureza do produto
Este produto é real, voltado para venda/comercialização, e não um projeto de estudo.

## Estado atual consolidado
A vertical trabalhista atual está validada operacionalmente e não deve ser reaberta sem bug real ou decisão consciente de redesign.

### Bloco atual consolidado
- autenticação
- sessão
- login dedicado
- redirects
- painel do advogado
- criação de caso
- analysis
- executive summary
- executive report
- executive PDF
- painel PT-BR
- filtros de carteira
- arquivamento
- cleanup demo
- documentação comercial base

## Decisão estratégica oficial
O produto deixa de ser pensado apenas como uma IA trabalhista de avaliação e passa a ser pensado como uma plataforma jurídica robusta, multiárea, com dois modos centrais de operação:

1. Avaliação jurídica
2. Criação de processos/peças

## Vertical atual validada
- Trabalhista

## Áreas futuras previstas
- Cível
- Criminal
- Família
- Consumidor
- Previdenciário
- Outras áreas futuras

## Nova visão de arquitetura
A evolução do produto será dividida em quatro camadas.

### 1. Núcleo comum da plataforma
Responsável por elementos transversais a qualquer área jurídica:
- auth
- sessão
- multi-tenant
- escritórios e usuários
- clientes e partes
- casos/processos
- documentos e anexos
- timeline e histórico
- artefatos
- auditoria
- billing e planos
- dashboards

### 2. Engines por área jurídica
Cada área jurídica terá seu próprio módulo, com:
- intake próprio
- campos específicos
- regras específicas
- análise específica
- teses e fundamentos específicos
- peças específicas
- checklists específicos
- avaliação de risco/viabilidade específica

### 3. Motor de criação de processos/peças
Camada responsável por:
- intake guiado
- cadastro estruturado de fatos
- qualificação das partes
- organização de documentos
- estruturação de pedidos
- organização de fundamentos
- geração de peça
- exportação utilizável
- revisão humana assistida

### 4. Orquestração assíncrona
Toda operação pesada deve evoluir para fluxo assíncrono, especialmente:
- geração de análise
- geração de relatório
- geração de PDF
- geração de peças
- processamento de anexos
- tarefas futuras de alto custo

## Regra obrigatória de UX
A expansão deve acontecer sem deixar a UX pesada.

### Princípios obrigatórios
- interface simples na frente
- complexidade no bastidor
- carregamento sob demanda
- separação entre ações leves e pesadas
- modularização por área
- preparação para processamento assíncrono
- clareza visual
- navegação leve para uso real do advogado

## O que não reabrir sem motivo real
Não reabrir sem bug real ou decisão consciente:
- auth
- sessão
- login
- redirects
- analysis
- executive summary
- executive report
- executive PDF
- painel atual PT-BR
- filtros atuais
- archive
- cleanup demo
- documentação comercial base

## Ordem oficial de evolução
### Fase A — Fechamento do bloco atual
- manual do painel para advogados
- documento oficial da evolução do produto
- congelamento formal do que já está pronto

### Fase B — Arquitetura da expansão
- mapear acoplamentos do domínio trabalhista
- definir núcleo neutro
- definir engines por área
- definir motor de criação de peças
- definir arquitetura anti-UX-pesada

### Fase C — Primeira expansão prática
Primeira frente recomendada:
- criação de processo/peça trabalhista

Primeira peça recomendada:
- petição inicial trabalhista

### Fase D — Escala multiárea
- Cível
- Criminal
- demais áreas

## Objetivo de posicionamento
O objetivo é posicionar o produto como uma plataforma jurídica robusta, modular, escalável e utilizável no mundo real, capaz não apenas de avaliar casos, mas também de apoiar a produção jurídica operacional com qualidade e leveza de uso.
