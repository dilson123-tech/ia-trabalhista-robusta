# Manual do Painel do Advogado

## Objetivo
Este manual apresenta o uso do painel atual do produto, com foco em demonstração, operação piloto e uso comercial com advogados e escritórios.

## Visão geral
O painel do advogado foi estruturado para oferecer um fluxo simples e prático de operação, cobrindo:
- login
- acesso à carteira principal
- cadastro de casos
- análise jurídica
- executive summary
- executive report
- executive PDF
- arquivamento de casos
- limpeza segura de demonstração

## 1. Acesso ao sistema
O usuário acessa o sistema pela rota dedicada de login.

### Fluxo atual validado
- autenticação funcionando
- sessão funcionando
- redirects funcionando
- proteção de acesso funcionando

## 2. Painel principal
Ao entrar no painel, o advogado visualiza sua carteira de casos com interface em PT-BR.

### Elementos principais
- botão `+ Novo Caso`
- botão `Ocultar formulário`
- botão `Cadastrar caso`
- busca por número/título
- filtro por status
- contador `Exibindo X de Y`

### Status exibidos em PT-BR
- draft → Rascunho
- active → Ativo
- review → Em revisão
- archived → Arquivado

## 3. Cadastro de novo caso
O painel permite cadastrar um novo caso a partir do formulário principal.

### Fluxo
1. abrir o formulário com `+ Novo Caso`
2. preencher os dados do caso
3. clicar em `Cadastrar caso`
4. validar a entrada na carteira

## 4. Análise jurídica
Após a criação do caso, o sistema permite gerar a análise jurídica do caso.

### Resultado esperado
- leitura inicial do cenário
- consolidação da visão do caso
- base para summary, report e PDF

## 5. Executive Summary
O sistema permite gerar um resumo executivo do caso.

### Objetivo
- apresentar visão resumida
- facilitar leitura rápida
- apoiar tomada de decisão

## 6. Executive Report
O sistema permite gerar o relatório executivo.

### Objetivo
- consolidar visão mais ampla do caso
- registrar leitura estruturada
- apoiar operação e apresentação

## 7. Executive PDF
O sistema permite gerar um PDF executivo do caso.

### Objetivo
- material apresentável
- uso em demonstração
- uso em operação piloto
- entrega mais formal ao advogado

## 8. Arquivamento de casos
O painel atual possui ação de arquivamento diretamente no card do caso.

### Comportamento validado
- o caso arquivado sai da `Carteira principal`
- o caso continua acessível via filtro de `Arquivados`
- o usuário recebe feedback visual de sucesso/erro

### Objetivo operacional
Permitir retirar casos antigos da vitrine principal sem apagar histórico útil.

## 9. Limpeza segura de demonstração
O painel atual possui ação de limpeza de demonstração.

### Regra validada
- remove apenas casos com prefixo `DEMO-`
- remove também análises vinculadas aos casos demo
- não remove casos reais fora do padrão
- operação restrita a administrador

### Objetivo operacional
Permitir preparar o ambiente para demos sem afetar dados reais.

## 10. Uso recomendado em demonstração comercial
Fluxo recomendado para apresentação a advogado ou escritório:

1. acessar login
2. entrar no painel do advogado
3. mostrar carteira principal
4. demonstrar busca e filtro
5. cadastrar um novo caso
6. gerar analysis
7. gerar executive summary
8. gerar executive report
9. gerar executive PDF
10. mostrar ação de arquivar
11. mostrar filtro de arquivados
12. explicar limpeza segura de demonstração

## 11. O que já está consolidado
Bloco atual consolidado e validado:
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

## 12. O que não deve ser reaberto sem motivo real
Não reabrir sem bug real ou decisão consciente:
- auth
- sessão
- login
- redirects
- analysis
- executive summary
- executive report
- executive PDF
- painel PT-BR
- filtros atuais
- arquivamento
- cleanup demo

## 13. Próxima evolução do produto
O painel atual representa a vertical trabalhista validada.

A evolução oficial do produto seguirá para:
- plataforma jurídica multiárea
- engines por área jurídica
- motor de criação de processos/peças
- expansão com UX leve
- processamento assíncrono para operações pesadas

## 14. Posicionamento atual
O bloco atual já está apto para:
- demonstração com advogado
- operação piloto
- apresentação comercial inicial

## 15. Resumo executivo
O produto atual já entrega valor real na vertical trabalhista e serve como base validada para a evolução futura da plataforma jurídica robusta.
