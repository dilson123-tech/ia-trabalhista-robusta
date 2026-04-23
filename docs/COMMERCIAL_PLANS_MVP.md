# PLANOS COMERCIAIS — MVP VENDÁVEL

## Objetivo
Este documento formaliza os planos operacionais/comerciais do MVP do **IA Trabalhista Robusta** com base no comportamento real já implementado no backend e refletido no painel.

Não inventa regra paralela.
Não promete automação que o produto ainda não entrega.
Define o que já está valendo de verdade para operação, trial, upgrade e limite.

---

## Planos oficiais do MVP

### 1. Basic
- até **50 casos ativos**
- até **200 registros no acervo**
- até **20 análises de IA por mês**

### 2. Pro
- até **200 casos ativos**
- até **1000 registros no acervo**
- até **100 análises de IA por mês**

### 3. Office
- até **1000 casos ativos**
- até **10000 registros no acervo**
- até **500 análises de IA por mês**

---

## Status comerciais oficiais

### trial
Uso em período de teste, com limites efetivos do plano aplicado ao tenant.

### active
Assinatura operacional ativa.

### canceled
Tenant continua operando com **limites efetivos do plano basic** até regularização comercial.

---

## Regras operacionais que valem para venda

### 1. Casos ativos
Casos ativos pressionam a operação diária do escritório e são o primeiro gatilho de upgrade.

### 2. Acervo
Casos arquivados preservam histórico, mas continuam consumindo capacidade do acervo.

### 3. Criação de caso
Ao criar um novo caso, o sistema consome:
- **1 vaga de caso ativo**
- **1 vaga de acervo**

### 4. Restauração de caso arquivado
Ao restaurar um caso:
- o sistema consome **1 vaga de ativo**
- não cria novo registro de acervo, porque o caso já existia

### 5. Arquivamento
Ao arquivar um caso:
- a pressão operacional sobre ativos diminui
- o histórico continua guardado e segue contando no acervo

### 6. Análises de IA
As análises de IA possuem teto mensal por plano.

### 7. Upgrade
Upgrade amplia teto operacional e teto de acervo **sem apagar histórico**.

---

## Comportamento ao atingir limite

### Limite de casos ativos
Se o tenant atingir o teto de ativos, o comportamento oficial é:
- arquivar um caso para liberar capacidade operacional
- ou fazer upgrade de plano

Mensagem operacional atual:
> Limite de casos ativos do plano atingido. Arquive um caso ou faça upgrade.

### Limite de acervo
Se o tenant atingir o teto do acervo, o comportamento oficial é:
- fazer upgrade para continuar armazenando mais casos

Mensagem operacional atual:
> Limite de acervo do plano atingido. Faça upgrade para armazenar mais casos.

### Limite de análises de IA
Se o tenant atingir o teto mensal de análises:
- a geração adicional é bloqueada até renovação do ciclo ou upgrade

Mensagem operacional atual:
> Limite do plano atingido. Faça upgrade.

---

## Regra de trial
Na ausência de subscription válida, o produto opera com comportamento efetivo de **basic/trial**.

Isso permite:
- onboarding controlado
- piloto limitado
- uso inicial sem abrir a porteira operacional do plano superior

---

## Regra de expiração/cancelamento
Quando a assinatura não estiver mais operacional, o enforcement efetivo recai para o nível **basic** até regularização comercial.

No caso de `canceled`, isso é regra explícita.
A operação comercial deve tratar esse estado como tenant sem benefício do plano superior.

---

## O que este documento NÃO promete
Este documento não fixa preço público final em reais.
Ele fixa a **estrutura oficial de planos do produto**, os limites reais já implementados e a regra comercial/operacional usada no MVP vendável.

A precificação final pode ser negociada em proposta comercial, piloto assistido ou contrato, sem quebrar esta estrutura.

---

## Uso no painel
O painel deve continuar refletindo esta lógica:
- plano atual
- status do plano
- ocupação de ativos
- ocupação do acervo
- mensagem operacional de capacidade
- gatilho claro para arquivamento ou upgrade

---

## Revisão obrigatória
Revisar este documento sempre que houver mudança em:
- limites do plano
- regra de trial
- comportamento de upgrade
- política de cancelamento
- capacidade de IA por plano
- forma como ativos e arquivados entram no cálculo comercial
