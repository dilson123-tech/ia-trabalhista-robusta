# Matriz de Cobertura Jurídica V1

## Plataforma Jurídica Pro

**Fase oficial:** Matriz de Cobertura Jurídica
**Base técnica:** estado posterior à `v0.2.34-editor-all-blocks-consumer-universal-action-scope-router-v1`
**Natureza:** documento oficial de cobertura, priorização e controle de evolução jurídica

---

## 1. Finalidade

Este documento passa a ser o mapa oficial de cobertura jurídica da Plataforma Jurídica Pro.

Sua função é registrar, de forma verificável:

- as áreas jurídicas reconhecidas pela plataforma;
- os principais tipos de ação ou medida;
- o nível atual de especialização;
- as entregas que sustentam cada cobertura;
- as lacunas ainda existentes;
- a próxima evolução necessária para cada item.

A matriz não mede apenas se a plataforma consegue produzir algum texto.

Ela mede se existe cobertura jurídica específica, prudente, coerente e protegida contra regressões.

---

## 2. Natureza permanente do produto

A Plataforma Jurídica Pro não é um gerador automático de petições.

Ela é um assistente jurídico profissional destinado à produção de minutas preliminares:

- organizadas;
- prudentes;
- coerentes;
- revisáveis;
- vinculadas aos fatos relatados;
- vinculadas aos documentos disponíveis;
- sujeitas à decisão final do advogado responsável.

A plataforma não deve:

- inventar fatos;
- inventar documentos;
- inventar pedidos;
- inventar provas;
- presumir competência;
- presumir rito;
- presumir urgência;
- presumir tese jurídica;
- prometer resultado;
- substituir análise profissional;
- produzir peça tratada como pronta para protocolo sem revisão.

Quando houver dúvida entre aumentar o conteúdo e preservar a precisão, a precisão prevalece.

---

## 3. Trilhas de cobertura

A plataforma possui capacidades diferentes que não devem ser confundidas.

### 3.1 Cobertura operacional

Inclui recursos como:

- cadastro e organização do caso;
- audiência estratégica;
- análise assistida;
- checklists;
- anexos e provas;
- documentos editáveis;
- exportação;
- fluxos QA históricos.

Uma área pode possuir cobertura operacional e ainda não possuir especialização completa no Editor de minutas.

### 3.2 Cobertura do Editor de minutas

Mede se o Editor consegue produzir os sete blocos com especialização compatível com o tipo de ação:

1. endereçamento;
2. qualificação das partes;
3. resumo fático;
4. fundamentação preliminar;
5. pedidos;
6. provas e requerimentos;
7. fechamento e conferência final.

### 3.3 Cobertura jurídica completa

Um item somente pode ser tratado como completamente pronto quando possuir, de forma compatível:

- detecção do tipo de ação;
- fundamentação específica;
- pedidos específicos;
- provas específicas;
- cautelas permanentes;
- testes automatizados;
- regressão completa;
- teste real no navegador;
- merge;
- tag;
- registro atualizado nesta matriz.

A validação de uma audiência estratégica, checklist ou PDF não transforma automaticamente o Editor em especializado.

---

## 4. Classificação oficial

### ✅ PRONTO

Cobertura específica validada para uso supervisionado.

Critérios esperados:

- tipo de ação detectado;
- blocos essenciais especializados;
- fundamentação compatível;
- pedidos compatíveis;
- provas compatíveis;
- cautelas preservadas;
- testes automatizados;
- regressão aprovada;
- teste real documentado quando aplicável;
- merge e tag oficiais.

O status pronto não elimina a revisão obrigatória do advogado.

### 🟡 PARCIAL

Existe cobertura aproveitável, mas ainda incompleta.

Pode ocorrer quando:

- existe checklist ou fluxo operacional;
- existe roteamento de fundamentação e pedidos;
- apenas alguns blocos estão especializados;
- o bloco de provas ainda é genérico;
- o endereçamento ou a qualificação ainda são genéricos;
- existem marcadores, mas não testes dedicados;
- existe validação antiga fora do Editor;
- o caso depende de revisão técnica reforçada.

Itens parciais não devem ser apresentados como especialização completa.

### 🔴 INEXISTENTE

Não existe cobertura específica suficiente para tratar o item como funcionalmente mapeado.

Pode existir fallback prudente, mas isso não equivale a especialização jurídica.

O item deve passar pelo ciclo completo antes de ser apresentado como pronto.

---

## 5. Hierarquia das evidências

A classificação deve considerar, nesta ordem:

1. implementação atual do Editor;
2. testes automatizados atuais;
3. teste real no navegador;
4. tag oficial;
5. relatórios QA;
6. checklists documentados;
7. fluxos operacionais históricos;
8. fallback genérico.

Documentação antiga não pode superar o comportamento real do código atual.

---

## 6. Cobertura transversal do Editor

| Capacidade transversal | Status | Evidência principal | Pendência |
|---|---:|---|---|
| Geração dos sete blocos oficiais | ✅ | Suíte estrutural da série `v0.2.22` a `v0.2.24` | Preservar em toda regressão |
| Separação entre blocos | ✅ | Regressão estrutural e golden fixture | Não permitir contaminação entre blocos |
| Sincronização do prompt do frontend | ✅ | `v0.2.24-editor-all-blocks-frontend-prompt-golden-sync-v1` | Manter contrato sincronizado |
| Roteador universal de especialização | ✅ | `v0.2.26-editor-all-blocks-universal-action-specialization-router-v1` | Ampliar somente por itens da matriz |
| Cautela sobre fatos e documentos | ✅ | Regras permanentes do Editor | Não remover |
| Cautela sobre competência e rito | ✅ | Regras permanentes do Editor | Não assumir automaticamente |
| Cautela sobre pedidos finais | ✅ | Fechamento e limites do bloco de pedidos | Não transformar sugestão em decisão final |
| Fallback genérico prudente | ✅ | `generic_prudent` | Não confundir fallback com cobertura específica |
| Provas específicas para todas as ações | 🟡 | Família e risco laboral possuem especialização | Consumidor, horas e cível ainda usam base genérica em parte |
| Endereçamento específico para todas as áreas | 🟡 | Família e Trabalhista especializado possuem tratamento próprio | Consumidor, Cível, Previdenciário, Criminal e Ambiental pendentes |
| Qualificação específica para todas as áreas | 🟡 | Família e Trabalhista especializado possuem tratamento próprio | Demais áreas pendentes |
| Teste real por tipo de ação | 🟡 | Existem casos reais e QAs em áreas selecionadas | Criar evidência individual conforme expansão |

---

## 7. Matriz por área jurídica

### 7.1 Trabalhista

#### Estado geral

Área madura, com especialização relevante no Editor.

A maturidade não é uniforme entre todos os tipos de ação.

| Tipo de ação ou tema | Operacional / checklist | Editor especializado | Status geral | Entregas principais | Lacuna atual |
|---|---:|---:|---:|---|---|
| Endereçamento e qualificação trabalhista | ✅ | ✅ | ✅ | `v0.2.30` | Ampliar somente quando novos tipos exigirem partes diferentes |
| Horas extras | ✅ | 🟡 | 🟡 | `v0.2.27` | Criar provas específicas e teste real próprio |
| Intervalo intrajornada | ✅ | 🟡 | 🟡 | `v0.2.27` | Criar provas específicas e teste real próprio |
| Divergência de controles de jornada | ✅ | 🟡 | 🟡 | `v0.2.27` | Especializar bloco probatório |
| Insalubridade por calor ou ambiente de fusão | ✅ | ✅ | ✅ | `v0.2.28`, `v0.2.29`, `v0.2.30` | Preservar regressão e ampliar com novos agentes somente por caso real |
| Periculosidade vinculada a risco técnico comprovável | ✅ | 🟡 | 🟡 | `v0.2.28`, `v0.2.29` | A rota atual trata a periculosidade com cautela e de forma subsidiária; faltam cenários próprios |
| PPP, LTCAT, PGR, PCMSO e EPI | ✅ | ✅ | ✅ | `v0.2.29` | Preservar a especificidade técnica |
| FGTS como reflexo ou documento | ✅ | 🟡 | 🟡 | Cobertura transversal nos fluxos trabalhistas | Criar ação própria quando FGTS for o núcleo do caso |
| Verbas rescisórias | ✅ | 🟡 | 🟡 | Checklist trabalhista e fallback | Criar detecção, fundamentação, pedidos e provas específicos |
| Reconhecimento de vínculo | ✅ | 🟡 | 🟡 | Checklist trabalhista | Criar especialização completa |
| Anotação ou retificação de CTPS | ✅ | 🟡 | 🟡 | Checklist trabalhista | Criar especialização completa |
| Rescisão indireta | ✅ | 🟡 | 🟡 | Checklist trabalhista | Criar especialização completa |
| Dano moral trabalhista | ✅ | 🟡 | 🟡 | Checklist e cautelas gerais | Criar critérios específicos de conduta, nexo e prova |
| Atraso salarial | ✅ | 🟡 | 🟡 | Checklist trabalhista | Criar especialização completa |
| Acúmulo ou desvio de função | ✅ | 🟡 | 🟡 | Checklist trabalhista | Criar especialização completa |
| Equiparação salarial | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar caso real e ciclo completo |
| Acidente de trabalho | 🔴 | 🔴 | 🔴 | Sem entrega específica atual | Criar rota com prova médica, técnica e nexo causal |
| Doença ocupacional | 🔴 | 🔴 | 🔴 | Sem entrega específica atual | Criar rota com documentos médicos e ocupacionais |
| Assédio moral ou sexual | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar tratamento sensível, probatório e cauteloso |
| Estabilidade provisória | 🔴 | 🔴 | 🔴 | Sem entrega específica | Mapear gestante, acidentária, sindical e demais hipóteses |
| Trabalho sem registro com múltiplos pedidos | 🟡 | 🔴 | 🟡 | Base geral trabalhista | Criar combinação controlada de vínculo, CTPS, verbas e FGTS |

#### Próximos pacotes recomendados

1. Completar provas específicas de horas extras e intervalo.
2. Criar especialização de acidente/doença ocupacional como pacote único.
3. Criar especialização de vínculo, CTPS, verbas e FGTS como família coerente.
4. Criar rescisão indireta somente após caso real e prova mínima.
5. Tratar assédio e estabilidade como pacotes sensíveis separados.

---

### 7.2 Família

#### Estado geral

Área muito madura para alimentos, guarda e convivência.

| Tipo de ação ou tema | Operacional / checklist | Editor especializado | Status geral | Entregas principais | Lacuna atual |
|---|---:|---:|---:|---|---|
| Alimentos | ✅ | ✅ | ✅ | `v0.2.31`, `v0.2.32`, `v0.2.33` | Preservar escopo e impedir mistura com guarda ou visitas |
| Guarda | ✅ | ✅ | ✅ | `v0.2.31`, `v0.2.32`, `v0.2.33` | Preservar escopo isolado |
| Convivência | ✅ | ✅ | ✅ | `v0.2.31`, `v0.2.32`, `v0.2.33` | Preservar escopo isolado |
| Regulamentação de visitas | ✅ | ✅ | ✅ | `v0.2.31`, `v0.2.32`, `v0.2.33` | Preservar escopo isolado |
| Alimentos + guarda | ✅ | ✅ | ✅ | Série `v0.2.31` a `v0.2.33` | Manter combinação somente quando os dois temas existirem |
| Guarda + convivência | ✅ | ✅ | ✅ | Série `v0.2.31` a `v0.2.33` | Manter combinação somente quando os dois temas existirem |
| Alimentos + guarda + convivência | ✅ | ✅ | ✅ | Série `v0.2.31` a `v0.2.33` | Preservar pedidos compatíveis |
| Provas familiares | ✅ | ✅ | ✅ | `v0.2.32` | Preservar certidões, renda, despesas, escola, saúde e rotina |
| Revisão de alimentos | ✅ | 🟡 | 🟡 | Marcadores existentes e checklist | Criar teste específico e ajustar pedidos próprios |
| Exoneração de alimentos | ✅ | 🟡 | 🟡 | Marcadores existentes e checklist | Criar teste específico e evitar pedido genérico de fixação |
| Divórcio consensual | ✅ | 🔴 | 🟡 | Checklist de Família | Criar especialização do Editor |
| Divórcio litigioso | ✅ | 🔴 | 🟡 | Checklist de Família | Criar especialização do Editor |
| Reconhecimento ou dissolução de união estável | ✅ | 🔴 | 🟡 | Checklist de Família | Criar especialização do Editor |
| Partilha de bens | ✅ | 🔴 | 🟡 | Checklist de Família | Criar especialização patrimonial e documental |
| Cumprimento de acordo ou decisão familiar | ✅ | 🔴 | 🟡 | Checklist de Família | Criar especialização processual própria |
| Investigação de paternidade | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar ciclo completo com prova genética e cautelas |
| Adoção | 🔴 | 🔴 | 🔴 | Sem entrega específica | Exige módulo sensível próprio |
| Curatela | 🔴 | 🔴 | 🔴 | Sem entrega específica | Exige tratamento de capacidade e prova médica |
| Tutela | 🔴 | 🔴 | 🔴 | Sem entrega específica | Exige módulo sensível próprio |
| Alienação parental | 🟡 | 🔴 | 🔴 | Apenas cautela documental | Não criar acusação automática; exige base técnica e caso real |

#### Próximos pacotes recomendados

1. Separar revisão e exoneração de alimentos.
2. Criar pacote divórcio e união estável.
3. Criar pacote patrimonial de partilha.
4. Tratar investigação de paternidade, adoção, curatela e tutela somente como módulos sensíveis completos.

---

### 7.3 Consumidor

#### Estado geral

A `v0.2.34` criou o roteador universal de escopos consumeristas.

A `v0.2.36` especializou o Bloco 6 — Provas e requerimentos para fraude bancária/Pix, cobrança indevida, negativação, produto, serviço, plano de saúde, veículo e contrato consumerista geral.

A `v0.2.37` especializou o Bloco 1 — Endereçamento e o Bloco 2 — Qualificação das partes para as rotas consumeristas universais e de veículo, preservando dados reais informados e mantendo a definição de competência, rito, partes e documentos sob confirmação profissional. A implementação foi validada em navegador no cenário combinado de fraude por Pix, cobrança indevida e negativação.

A área agora possui especialização transversal de endereçamento, qualificação, fundamentação, pedidos e provas nos escopos prioritários. As rotas permanecem parciais até a validação real adicional e o aprofundamento dos subtipos ainda genéricos.

| Tipo de ação ou tema | Operacional / checklist | Editor especializado | Status geral | Entregas principais | Lacuna atual |
|---|---:|---:|---:|---|---|
| Veículo, contrato, retenção ou restituição do bem | ✅ | 🟡 | 🟡 | `v0.2.26`, `v0.2.36`, `v0.2.37` | Endereçamento, partes e provas especializados; falta validação real desta rota |
| Fraude bancária | ✅ | 🟡 | 🟡 | `v0.2.34`, `v0.2.36`, `v0.2.37` | Endereçamento, qualificação e provas especializados; ampliar validação real isolada |
| Pix não reconhecido | ✅ | 🟡 | 🟡 | `v0.2.34`, `v0.2.36`, `v0.2.37` | Estrutura completa dos blocos prioritários e validação combinada concluídas |
| Cobrança indevida | ✅ | 🟡 | 🟡 | `v0.2.34`, `v0.2.36`, `v0.2.37` | Estrutura especializada concluída; critérios finais permanecem sob revisão profissional |
| Negativação indevida | ✅ | 🟡 | 🟡 | `v0.2.34`, `v0.2.36`, `v0.2.37` | Endereçamento, partes, documentos do débito e cadastro restritivo especializados |
| Fraude + cobrança + negativação | ✅ | 🟡 | 🟡 | `v0.2.34`, `v0.2.36`, `v0.2.37` | Sete blocos, incluindo endereçamento e qualificação, validados em navegador; manter revisão profissional |
| Produto defeituoso | ✅ | 🟡 | 🟡 | `v0.2.34`, `v0.2.36`, `v0.2.37` | Blocos prioritários especializados; falta validação real específica |
| Vício do produto | ✅ | 🟡 | 🟡 | `v0.2.34`, `v0.2.36`, `v0.2.37` | Estrutura especializada; aprofundar distinção jurídica quando caso real exigir |
| Serviço defeituoso ou incompleto | ✅ | 🟡 | 🟡 | `v0.2.34`, `v0.2.36`, `v0.2.37` | Blocos prioritários especializados; falta validação real específica |
| Serviço não prestado | ✅ | 🟡 | 🟡 | Checklist, `v0.2.34`, `v0.2.36`, `v0.2.37` | Coberto pela rota de serviço; criar caso real específico |
| Plano de saúde e negativa de cobertura | ✅ | 🟡 | 🟡 | `v0.2.34`, `v0.2.36`, `v0.2.37` | Blocos prioritários especializados; falta validação real específica |
| Contrato consumerista geral | ✅ | 🟡 | 🟡 | `v0.2.34`, `v0.2.36`, `v0.2.37` | Estrutura especializada; reduzir generalidade por subtipos prioritários |
| Oferta ou publicidade | ✅ | 🟡 | 🟡 | Fallback contratual consumerista | Criar ação específica quando houver caso real |
| Cancelamento não respeitado | ✅ | 🟡 | 🟡 | Checklist e contrato geral | Criar teste próprio |
| Atraso na entrega | ✅ | 🟡 | 🟡 | Checklist e contrato geral | Criar teste próprio |
| Falha de garantia | ✅ | 🟡 | 🟡 | Checklist e produto | Criar teste próprio |
| Telefonia | 🟡 | 🔴 | 🟡 | Base geral de consumo | Criar especialização quando priorizada |
| Energia elétrica | 🟡 | 🔴 | 🟡 | Base geral de consumo | Criar especialização quando priorizada |
| Seguro | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar cobertura contratual própria |
| Turismo, companhia aérea ou hospedagem | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar pacote próprio |
| Superendividamento | 🔴 | 🔴 | 🔴 | Sem entrega específica | Exige fluxo próprio e cautelas específicas |
| Vazamento ou uso indevido de dados | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar pacote consumidor/LGPD |
| Marketplace e intermediação digital | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar definição de fornecedores e responsabilidades |

#### Próximo pacote recomendado

Executar testes reais adicionais no navegador para:

- produto defeituoso ou com vício;
- serviço defeituoso, incompleto ou não prestado;
- plano de saúde;
- veículo;
- contrato consumerista geral.

Após essas validações, priorizar especializações próprias para oferta/publicidade, cancelamento, atraso na entrega e falha de garantia.

A `v0.2.37` concluiu a especialização transversal dos Blocos 1 e 2 nas rotas consumeristas prioritárias e validou em navegador o cenário combinado de fraude por Pix, cobrança indevida e negativação. As rotas permanecem 🟡 até que os demais escopos passem por validação real e os subtipos ainda genéricos recebam cobertura própria.

---

### 7.4 Cível

#### Estado geral

Existe base geral e algumas rotas específicas.

O Cível puro ainda precisa de estrutura semelhante à criada em Família e Consumidor.

| Tipo de ação ou tema | Operacional / checklist | Editor especializado | Status geral | Entregas principais | Lacuna atual |
|---|---:|---:|---:|---|---|
| Cobrança contratual sem dano moral | ✅ | 🟡 | 🟡 | `v0.2.25` | Especializar provas, endereçamento e qualificação |
| Obrigação de fazer | ✅ | 🟡 | 🟡 | Rota `obligation_to_do_or_not_do` | Criar provas e testes dedicados |
| Obrigação de não fazer | ✅ | 🟡 | 🟡 | Rota `obligation_to_do_or_not_do` | Criar provas e testes dedicados |
| Indenização por dano material | ✅ | 🟡 | 🟡 | Rota `civil_damages_claim` | Especializar documentos e critérios de quantificação |
| Indenização por dano moral | ✅ | 🟡 | 🟡 | Rota `civil_damages_claim` | Evitar dano automático e criar testes próprios |
| Responsabilidade civil geral | ✅ | 🟡 | 🟡 | Base cível e fallback | Criar detecção por causa |
| Prestação de contas | 🟡 | 🟡 | 🟡 | Fallback prudente menciona prestação de contas | Criar ação própria |
| Exibição de documentos | 🟡 | 🟡 | 🟡 | Presente em rotas e fallback | Criar ação própria quando for pedido principal |
| Posse ou propriedade | 🟡 | 🔴 | 🔴 | Apenas referência histórica | Criar cobertura específica |
| Usucapião | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar módulo documental e registral |
| Contratos complexos | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar análise contratual própria |
| Imobiliário | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar pacote próprio |
| Inventário e sucessões | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar área ou submódulo próprio |
| Produção antecipada de provas | 🔴 | 🔴 | 🔴 | Sem rota cível específica | Criar ciclo completo |
| Tutela antecedente ou cautelar autônoma | 🔴 | 🔴 | 🔴 | Sem entrega específica | Exige tratamento processual próprio |

#### Próximos pacotes recomendados

1. Completar cobrança contratual.
2. Completar obrigação de fazer ou não fazer.
3. Completar responsabilidade civil e danos.
4. Depois escolher um novo núcleo: possessório, imobiliário ou sucessões.

---

### 7.5 Previdenciário / BPC-LOAS

#### Estado geral

Existe módulo, checklist e fluxo QA para BPC/LOAS.

O Editor de sete blocos ainda não possui especialização previdenciária própria.

| Tipo de ação ou tema | Operacional / checklist | Editor especializado | Status geral | Evidência atual | Lacuna |
|---|---:|---:|---:|---|---|
| BPC/LOAS da pessoa idosa | ✅ | 🔴 | 🟡 | Checklist e QA previdenciário | Criar Editor específico |
| BPC/LOAS da pessoa com deficiência | ✅ | 🔴 | 🟡 | Checklist e QA previdenciário | Criar Editor específico |
| Vulnerabilidade e composição familiar | ✅ | 🔴 | 🟡 | Checklist BPC/LOAS | Criar fundamentação e provas específicas |
| CadÚnico e renda familiar | ✅ | 🔴 | 🟡 | Checklist BPC/LOAS | Criar bloco probatório específico |
| Benefício por incapacidade temporária | ✅ | 🔴 | 🟡 | Checklist previdenciário | Criar Editor específico |
| Aposentadoria por incapacidade permanente | ✅ | 🔴 | 🟡 | Checklist previdenciário | Criar Editor específico |
| Aposentadoria por idade | ✅ | 🔴 | 🟡 | Checklist previdenciário | Criar Editor específico |
| Aposentadoria por tempo de contribuição | ✅ | 🔴 | 🟡 | Checklist previdenciário | Criar Editor específico |
| Revisão de benefício | ✅ | 🔴 | 🟡 | Checklist previdenciário | Criar Editor específico |
| Restabelecimento de benefício | ✅ | 🔴 | 🟡 | Checklist previdenciário | Criar Editor específico |
| Recurso administrativo | ✅ | 🔴 | 🟡 | Checklist previdenciário | Criar fluxo próprio |
| Cumprimento de exigência | ✅ | 🔴 | 🟡 | Checklist previdenciário | Criar fluxo documental próprio |
| Aposentadoria rural | 🔴 | 🔴 | 🔴 | Sem entrega específica atual | Criar módulo probatório próprio |
| Aposentadoria especial | 🔴 | 🔴 | 🔴 | Sem entrega específica atual | Criar integração com PPP/LTCAT previdenciário |
| Pensão por morte | 🔴 | 🔴 | 🔴 | Sem entrega específica atual | Criar módulo próprio |
| Salário-maternidade | 🔴 | 🔴 | 🔴 | Sem entrega específica atual | Criar módulo próprio |

#### Próximo pacote recomendado

Criar o primeiro Editor previdenciário com foco restrito em:

- BPC/LOAS;
- pessoa idosa;
- pessoa com deficiência;
- renda;
- composição familiar;
- CadÚnico;
- prova social;
- prova médica;
- requerimento e indeferimento administrativo.

Não misturar BPC/LOAS com benefícios contributivos.

---

### 7.6 Criminal

#### Estado geral

Existe pacote operacional inicial validado e hardenizado.

Essa validação não representa especialização atual do Editor de sete blocos.

| Tipo de medida ou ação | Operacional / checklist | Editor especializado | Status geral | Evidência atual | Lacuna |
|---|---:|---:|---:|---|---|
| Liberdade provisória | ✅ | 🔴 | 🟡 | Pacote criminal inicial | Criar Editor específico |
| Habeas corpus inicial | ✅ | 🔴 | 🟡 | Pacote criminal inicial | Criar estrutura própria, sem forçar sete blocos cíveis |
| Relaxamento de prisão | ✅ | 🔴 | 🟡 | Pacote criminal inicial | Criar Editor específico |
| Resposta à acusação | ✅ | 🔴 | 🟡 | Pacote criminal inicial e hardening | Criar Editor específico |
| Revogação de prisão preventiva | ✅ | 🔴 | 🟡 | Checklist criminal | Criar especialização |
| Medidas cautelares diversas da prisão | ✅ | 🔴 | 🟡 | Checklist criminal | Criar especialização |
| Pedido de audiência de custódia | ✅ | 🔴 | 🟡 | Checklist criminal | Criar fluxo próprio |
| Pedido de diligência | ✅ | 🔴 | 🟡 | Checklist criminal | Criar fluxo próprio |
| Cadeia de custódia | 🟡 | 🔴 | 🔴 | Referência operacional | Criar módulo de prova específico |
| Tribunal do Júri | 🔴 | 🔴 | 🔴 | Sem entrega específica | Exige módulo próprio |
| Execução penal | 🔴 | 🔴 | 🔴 | Sem entrega específica | Exige módulo próprio |
| Recurso criminal | 🔴 | 🔴 | 🔴 | Sem entrega específica | Exige módulo próprio |
| Queixa-crime | 🔴 | 🔴 | 🔴 | Sem entrega específica | Exige módulo próprio |
| Medidas protetivas | 🔴 | 🔴 | 🔴 | Sem entrega específica | Exige tratamento sensível próprio |

#### Próxima regra

O Criminal não deve ser encaixado à força no mesmo formato das ações cíveis.

Antes de especializar, deve ser definido o contrato estrutural adequado para cada medida criminal.

---

### 7.7 Civil/Ambiental

#### Estado geral

Existe audiência estratégica, checklist e QA documentado.

O Editor atual ainda não possui roteador específico para Civil/Ambiental.

| Tipo de ação ou tema | Operacional / checklist | Editor especializado | Status geral | Evidência atual | Lacuna |
|---|---:|---:|---:|---|---|
| Direito de vizinhança | ✅ | 🔴 | 🟡 | Checklist e QA Civil/Ambiental | Criar Editor específico |
| Ruído excessivo | ✅ | 🔴 | 🟡 | Checklist e QA Civil/Ambiental | Criar prova técnica e pedidos próprios |
| Poeira ou partículas | ✅ | 🔴 | 🟡 | Checklist e QA Civil/Ambiental | Criar prova técnica e pedidos próprios |
| Vibração | ✅ | 🔴 | 🟡 | Checklist e QA Civil/Ambiental | Criar prova técnica e pedidos próprios |
| Poluição ou dano ambiental local | ✅ | 🔴 | 🟡 | Checklist e QA Civil/Ambiental | Criar Editor específico |
| Obrigação de cessar atividade nociva | ✅ | 🟡 | 🟡 | Rota cível geral de obrigação | Especializar nexo, urgência e prova técnica |
| Indenização material ambiental ou de vizinhança | ✅ | 🟡 | 🟡 | Rota cível geral de danos | Especializar nexo e quantificação |
| Indenização moral em contexto ambiental | ✅ | 🟡 | 🟡 | Rota cível geral de danos | Evitar presunção e especializar prova |
| Perícia ambiental, acústica ou de engenharia | ✅ | 🔴 | 🟡 | Checklist e QA | Criar bloco probatório específico |
| Produção antecipada de prova ambiental | ✅ | 🔴 | 🟡 | Checklist | Criar ação específica |
| Licenciamento ambiental | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar módulo administrativo ambiental |
| Auto de infração ambiental | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar módulo administrativo e sancionatório |
| Ação civil pública ambiental | 🔴 | 🔴 | 🔴 | Sem entrega específica | Exige módulo coletivo próprio |

#### Próximo pacote recomendado

Criar pacote único de conflito de vizinhança e impacto local:

- ruído;
- poeira;
- vibração;
- atividade nociva;
- obrigação de fazer ou não fazer;
- tutela baseada em risco concreto;
- perícia;
- laudo;
- fiscalização;
- nexo causal.

---

### 7.8 Empresarial / Contratos / Cobrança

#### Estado geral

A área ainda não está formalmente consolidada como módulo completo.

Existe uma entrega específica de cobrança contratual no núcleo cível.

| Tipo de ação ou tema | Operacional / checklist | Editor especializado | Status geral | Evidência atual | Lacuna |
|---|---:|---:|---:|---|---|
| Cobrança contratual simples sem dano moral | 🟡 | 🟡 | 🟡 | `v0.2.25` | Completar provas, partes e enquadramento |
| Prestação de serviço inadimplida | 🟡 | 🔴 | 🟡 | Planejamento antigo | Criar especialização |
| Rescisão contratual | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar especialização |
| Notificação extrajudicial | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar fluxo documental próprio |
| Confissão de dívida | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar fluxo próprio |
| Acordo extrajudicial | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar fluxo próprio |
| Ação monitória | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar especialização |
| Execução de título extrajudicial | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar especialização |
| Análise de cláusulas | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar assistente contratual separado |
| Contrato de prestação de serviços | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar fluxo próprio |
| Dissolução societária | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar módulo societário |
| Recuperação de crédito empresarial | 🔴 | 🔴 | 🔴 | Sem entrega específica | Criar módulo próprio |

#### Trava

Não criar um grande módulo empresarial genérico.

A evolução deve começar por um tipo de ação real, com documentos e resultado esperado claramente definidos.

---

## 8. Resumo executivo por área

| Área | Estado geral atual | Leitura correta |
|---|---:|---|
| Trabalhista | 🟡 Parcial avançado | Forte em risco laboral; horas e demais ações ainda incompletas |
| Família | ✅ Pronto no núcleo atual | Alimentos, guarda e convivência especializados e testados |
| Consumidor | 🟡 Parcial avançado | Fundamentação e pedidos fortes; provas e partes ainda pendentes |
| Cível | 🟡 Parcial | Algumas rotas específicas, sem arquitetura completa por ação |
| Previdenciário | 🟡 Operacional, Editor pendente | BPC/LOAS possui base e QA, mas não Editor específico |
| Criminal | 🟡 Operacional, Editor pendente | Pacote inicial validado fora do Editor atual |
| Civil/Ambiental | 🟡 Operacional, Editor pendente | Checklist e QA existentes, sem roteador próprio |
| Empresarial/Contratos | 🔴 Inicial | Apenas cobrança contratual simples possui avanço parcial |

---

## 9. Ordem de prioridade recomendada

A prioridade deve considerar ganho jurídico, fechamento de lacunas existentes e risco de regressão.

### Prioridade 1 — completar áreas já roteadas

1. Provas específicas do Consumidor por escopo.
2. Provas específicas de horas extras e intervalo.
3. Provas, partes e endereçamento da cobrança contratual.

### Prioridade 2 — transformar módulos operacionais em Editor especializado

1. BPC/LOAS.
2. Criminal inicial, após definir estrutura adequada por medida.
3. Civil/Ambiental de vizinhança e impacto local.

### Prioridade 3 — ampliar Trabalhista

1. Acidente e doença ocupacional.
2. Vínculo, CTPS, verbas e FGTS.
3. Rescisão indireta.
4. Equiparação salarial.
5. Assédio.
6. Estabilidade.

### Prioridade 4 — ampliar Família

1. Revisão e exoneração de alimentos.
2. Divórcio e união estável.
3. Partilha.
4. Investigação de paternidade.
5. Curatela, tutela e adoção.

### Prioridade 5 — novas famílias consumeristas e cíveis

1. Seguro.
2. Telefonia e energia.
3. Turismo.
4. Superendividamento.
5. Dados pessoais e LGPD.
6. Possessório e imobiliário.
7. Sucessões.

---

## 10. Fluxo obrigatório de evolução

Toda nova especialização deverá seguir este ciclo:

1. escolher um item desta matriz;
2. definir o escopo exato;
3. criar ou selecionar caso real supervisionado;
4. executar o caso no navegador;
5. registrar as falhas concretas;
6. especializar somente o necessário;
7. criar testes unitários;
8. executar a regressão completa;
9. validar novamente no navegador;
10. abrir e revisar o pull request;
11. mergear;
12. criar tag oficial;
13. atualizar esta matriz.

Nenhuma etapa deve ser pulada.

---

## 11. Regra para alteração de status

### De 🔴 para 🟡

Exige pelo menos:

- escopo documentado;
- checklist ou contrato inicial;
- comportamento prudente identificável;
- alguma cobertura operacional ou implementação parcial;
- declaração explícita das limitações.

### De 🟡 para ✅

Exige:

- detecção específica;
- fundamentação específica;
- pedidos específicos;
- provas específicas;
- cautelas preservadas;
- testes dedicados;
- regressão completa;
- teste real no navegador;
- merge;
- tag;
- atualização desta matriz.

Nenhum status deve ser elevado apenas porque o texto parece bom visualmente.

---

## 12. Regras contra regressão

Toda nova entrega deve provar que:

- não misturou áreas jurídicas;
- não adicionou pedido incompatível;
- não inventou prova;
- não removeu cautelas;
- não alterou blocos não relacionados;
- não quebrou casos anteriores;
- não transformou fallback em especialização falsa;
- não tratou ausência de dados como autorização para completar fatos;
- não aumentou texto sem ganho jurídico real.

---

## 13. Relação com documentos anteriores

Os documentos anteriores continuam válidos como histórico e apoio operacional, especialmente:

- `docs/LEGAL_MODULES_V1.md`;
- `docs/LEGAL_MODULE_CHECKLISTS_V1.md`;
- `docs/LEGAL_MODULE_CHECKLISTS_V2.md`;
- `docs/LEGAL_MODULE_COVERAGE_MATRIX_V1.md`;
- relatórios QA por área.

Entretanto, este documento passa a ser a referência principal para:

- estado atual da cobertura;
- escolha das próximas especializações;
- classificação de pronto, parcial ou inexistente;
- atualização posterior a cada versão.

A matriz antiga em `docs/LEGAL_MODULE_COVERAGE_MATRIX_V1.md` não deve ser apagada, pois registra uma fase histórica baseada principalmente em cobertura operacional e Audiência Estratégica.

---

## 14. Registro de atualizações

| Data | Versão | Alteração |
|---|---|---|
| 2026-07-21 | `v0.2.35` | Criação da matriz oficial de cobertura jurídica após a `v0.2.34` |
| 2026-07-22 | `v0.2.36` | Especialização do Bloco 6 por escopo consumerista, com regressão e validação real de fraude Pix, cobrança e negativação |
| 2026-07-22 | `v0.2.37` | Especialização consumerista dos Blocos 1 e 2, com limites civis prudentes, preservação das partes e validação real no navegador |

A cada nova tag jurídica:

1. atualizar o item afetado;
2. registrar a versão;
3. explicar o que ficou pronto;
4. manter explícito o que continua pendente.

---

## 15. Diretriz final

O objetivo da Plataforma Jurídica Pro não é produzir o maior texto possível.

O objetivo é produzir a melhor primeira minuta possível, com:

- precisão;
- prudência;
- coerência;
- especialização;
- consistência entre fatos, fundamentos, pedidos e provas;
- ausência de informações inventadas;
- revisão profissional obrigatória;
- proteção automatizada contra regressões.

A matriz deve impedir que evolução técnica seja confundida com volume de funcionalidades.

Cobertura jurídica real é aquilo que foi delimitado, implementado, testado, validado e documentado.
