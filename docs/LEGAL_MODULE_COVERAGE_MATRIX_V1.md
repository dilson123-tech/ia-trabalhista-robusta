# Matriz Oficial de Cobertura Jurídica V1

## Plataforma IA Jurídica Pro

Este documento define a matriz oficial de cobertura funcional da Plataforma IA Jurídica Pro.

A matriz serve para separar, com clareza, o que já está validado para uso supervisionado, o que funciona com base geral e revisão reforçada, e o que ainda não deve ser vendido como pronto.

Este documento evita dois erros perigosos:

1. vender como pronto algo que ainda não foi validado;
2. tratar como inexistente algo que já possui base funcional aproveitável.

---

## 1. Regra central

A plataforma não precisa ter um fluxo específico para cada processo possível antes de ser usada.

Porém, para vender com segurança e qualidade premium, cada tipo de caso deve estar classificado em uma das faixas abaixo.

---

## 2. Classificação oficial

### VERDE — Validado

Pode ser apresentado como funcional e validado para uso supervisionado.

Critérios:

- possui fluxo implementado;
- possui testes automatizados ou QA documentado;
- possui comportamento esperado conhecido;
- preserva áreas anteriores;
- pode gerar documento, roteiro ou análise com segurança operacional;
- exige revisão do advogado, mas não depende de improviso total.

### AMARELO — Coberto por base geral

Pode ser usado com revisão técnica reforçada, mas não deve ser vendido como fluxo especializado completo.

Critérios:

- a área jurídica existe;
- o sistema consegue organizar o caso;
- pode usar análise geral, partes, anexos e contexto;
- ainda não possui checklist/QA específico para aquele subtipo;
- exige cautela comercial e revisão forte do advogado.

### VERMELHO — Pendente / não vender como pronto

Não deve ser vendido como pronto.

Critérios:

- sem fluxo específico;
- sem QA;
- sem checklist;
- sem validação de geração;
- risco alto de saída genérica ou incompleta;
- exige implementação antes de promessa comercial.

---

## 3. Cobertura por área — visão atual

## 3.1 Audiência Estratégica

| Área | Status | Observação |
|---|---:|---|
| Cível base com pessoas/contexto | VERDE | Validado com perguntas por pessoa e Contexto V2 |
| Criminal | VERDE | Validado com E2E, aprovação e PDF |
| Trabalhista | VERDE | Validado com E2E, aprovação e PDF |
| Consumidor | VERDE | Validado com E2E, Contexto V2, aprovação e PDF |
| Família | VERDE | Validado com E2E, Contexto V2, aprovação e PDF |
| Previdenciário/BPC-LOAS | VERDE | Validado com E2E, Contexto V2, aprovação e PDF |
| Civil/Ambiental | VERDE | Validado com E2E, Contexto V2, aprovação e PDF |
| Empresarial/Contratos/Cobrança | VERMELHO | Planejado para etapa posterior |

---

## 3.2 Trabalhista

| Tipo de caso | Status | Observação |
|---|---:|---|
| Audiência estratégica trabalhista | VERDE | Validada em E2E/PDF |
| Horas extras / jornada / ponto | VERDE | Forte cobertura no fluxo de audiência |
| FGTS / verbas / rescisão | AMARELO | Base forte, mas pode exigir QA específico por documento |
| Insalubridade / periculosidade / EPI | AMARELO | Coberto no roteiro, mas pede cuidado técnico/pericial |
| Dano moral trabalhista | AMARELO | Pode usar base geral, mas ainda sem QA dedicado |
| Acidente/doença ocupacional | VERMELHO | Sensível, precisa fluxo específico antes de vender como pronto |

---

## 3.3 Criminal

| Tipo de caso | Status | Observação |
|---|---:|---|
| Audiência estratégica criminal | VERDE | Validada em E2E/PDF |
| Liberdade provisória | VERDE | Fluxo inicial já validado |
| Habeas corpus inicial | VERDE | Fluxo inicial já validado |
| Relaxamento de prisão | VERDE | Fluxo inicial já validado |
| Resposta à acusação | VERDE | Validada e blindada contra contaminação |
| Cadeia de custódia / prova pericial | AMARELO | Aparece no roteiro, mas pode exigir especialização por caso |
| Júri / crimes dolosos contra vida | VERMELHO | Não vender como pronto sem módulo próprio |
| Execução penal | VERMELHO | Pendente |

---

## 3.4 Consumidor

| Tipo de caso | Status | Observação |
|---|---:|---|
| Audiência estratégica consumidor | VERDE | Validada em E2E/PDF |
| Cobrança indevida | VERDE | Coberta no fluxo validado |
| Negativação indevida | VERDE | Coberta no fluxo validado |
| Banco / fornecedor / SAC / ouvidoria | VERDE | Coberto no fluxo validado |
| Produto com defeito | AMARELO | Roteiro contempla técnico/perito, mas pede QA específico |
| Telecom / energia / serviços essenciais | AMARELO | Coberto por base geral de consumo |
| Fraude bancária / golpe financeiro | AMARELO | Alto valor, mas precisa fluxo próprio antes de vender como verde |
| Superendividamento | VERMELHO | Pendente |

---

## 3.5 Família

| Tipo de caso | Status | Observação |
|---|---:|---|
| Audiência estratégica família | VERDE | Validada em E2E/PDF |
| Guarda | VERDE | Coberta no fluxo validado |
| Alimentos | VERDE | Coberta no fluxo validado |
| Convivência / visitas | VERDE | Coberta no fluxo validado |
| Rotina da criança / escola / saúde | VERDE | Coberta no Contexto V2 |
| Alienação parental | AMARELO | Mencionada, mas exige cuidado técnico e QA específico |
| Divórcio / união estável | AMARELO | Base contemplada, mas sem E2E próprio |
| Partilha de bens | VERMELHO | Não vender como pronto ainda |
| Adoção / destituição familiar | VERMELHO | Sensível, exige módulo próprio |

---

## 3.6 Cível

| Tipo de caso | Status | Observação |
|---|---:|---|
| Cível base com partes/pessoas/anexos | VERDE | Validado com Contexto V2 |
| Caso PRATIC SIDER / carreta / BO | VERDE | Cenário específico validado |
| Responsabilidade civil genérica | AMARELO | Base funcional, precisa especialização |
| Cobrança contratual | AMARELO | Pode usar base geral, mas sem QA específico |
| Obrigação de fazer/não fazer | AMARELO | Pode usar base geral, mas sem QA específico |
| Posse/propriedade | AMARELO | Precisa fluxo mais próprio |
| Contratos complexos | VERMELHO | Pendente |
| Imobiliário avançado | VERMELHO | Pendente |

---

## 3.7 Previdenciário / BPC-LOAS

| Tipo de caso | Status | Observação |
|---|---:|---|
| Audiência estratégica previdenciária | VERDE | Validada em E2E/PDF para BPC/LOAS |
| BPC/LOAS | VERDE | Coberto no fluxo validado com prova médica/social, CadÚnico, renda familiar e INSS |
| Auxílio-doença / benefício por incapacidade | VERMELHO | Pendente |
| Aposentadoria por invalidez | VERMELHO | Pendente |
| Aposentadoria por idade | VERMELHO | Pendente |
| Revisão de benefício | VERMELHO | Pendente |
| Perícia médica / social | VERDE | Coberta no roteiro validado com perito médico e assistente social/avaliador social |

---

## 4. Regra comercial

A comunicação comercial deve seguir esta regra:

- itens VERDES podem ser apresentados como fluxos validados para uso supervisionado;
- itens AMARELOS podem ser usados, mas com aviso de revisão reforçada e sem promessa de especialização completa;
- itens VERMELHOS não devem ser vendidos como prontos.

Frase recomendada:

> A plataforma já possui fluxos validados em áreas específicas e também oferece base geral supervisionada para outros casos. Casos ainda não mapeados exigem revisão técnica ampliada do advogado e não devem ser tratados como automação especializada pronta.

---

## Civil/Ambiental

| Item | Status | Observação |
| --- | --- | --- |
| Audiência estratégica Civil/Ambiental | VERDE | Validada em E2E/PDF |
| Responsabilidade civil ambiental | VERDE | Coberta no fluxo validado com prova técnica, laudo, fiscalização e nexo causal |
| Dano ambiental | VERDE | Coberto no fluxo validado |
| Dano de vizinhança | VERDE | Coberto no fluxo validado |
| Ruído / fumaça / odor / infiltração | VERDE | Coberto no cenário QA |
| Descarte irregular / dano causado por empresa vizinha | VERDE | Coberto no cenário QA |
| Fotos / vídeos / laudo / auto de fiscalização | VERDE | Coberto pelo Contexto V2 e anexos/provas |
| Obrigação de fazer/não fazer | VERDE | Coberta no roteiro validado |
| Perícia / técnico ambiental ou engenharia | VERDE | Coberto no roteiro validado |
| Fiscalização / órgão público | VERDE | Coberto no roteiro validado |

## 5. Regra técnica

Antes de transformar um item AMARELO em VERDE, deve existir pelo menos:

1. helper/checklist específico ou regra de área;
2. teste unitário/regressão;
3. teste E2E quando envolver geração/documento/PDF;
4. relatório QA;
5. PR com checks verdes;
6. tag oficial.

---

## 6. Próxima prioridade recomendada

Com Civil/Ambiental validado tecnicamente em `v0.1.31-civil-ambiental-audiencia-estrategica-v1`, a próxima prioridade recomendada é comercial/documental:

`Atualizar apresentação comercial da Audiência Estratégica multiárea para advogado/escritório`

Justificativa:

- a Audiência Estratégica agora tem cobertura validada em Cível base/contexto, Criminal, Trabalhista, Consumidor, Família, Previdenciário/BPC-LOAS e Civil/Ambiental;
- Civil/Ambiental saiu do estado AMARELO e passou a ter E2E, Contexto V2, aprovação e PDF;
- a plataforma já tem evidência técnica suficiente para montar material comercial mais forte;
- novos módulos, como Empresarial/Contratos/Cobrança, devem entrar depois, sem atropelar o pacote comercial atual;
- itens ainda AMARELOS continuam exigindo revisão reforçada e não devem ser vendidos como especialização completa.
