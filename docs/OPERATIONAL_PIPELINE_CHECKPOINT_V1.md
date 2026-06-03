# Checkpoint — Esteira Operacional Real de Escritório V1

Marco base: `v0.1.45-case-internal-dossier-qa`

## Objetivo

Registrar o estado consolidado da esteira operacional da Plataforma IA Jurídica Pro / IA Trabalhista Robusta após a validação do Dossiê Interno do Caso V1.

Este documento existe para evitar retrabalho, decisões impulsivas e perda de foco em ciclos futuros.

O projeto é real, voltado para operação jurídica supervisionada em escritório.

Este projeto carrega aproximadamente dois anos de construção, validações, decisões técnicas, ciclos de QA, ajustes de produto e evolução comercial. Portanto, não pode ser tratado como estudo, brincadeira, prova de conceito descartável, laboratório visual ou experimento improvisado.

A regra para qualquer próximo chat, desenvolvedor, revisão ou retomada é simples:

- preservar o que já foi validado;
- não reconstruir fluxo aprovado sem motivo concreto;
- não reabrir discussão técnica encerrada sem bug real;
- não trocar arquitetura estável por preferência estética;
- não criar feature nova por empolgação;
- não quebrar módulos validados para “melhorar” sem necessidade;
- não confundir MVP real com projeto escolar.

Este checkpoint protege trabalho acumulado e deve ser lido antes de qualquer novo ciclo.

## Regra de preservação do trabalho acumulado

A partir deste checkpoint, qualquer evolução deve partir da premissa de que a plataforma já possui uma base operacional real e validada.

Não é aceitável voltar etapas, recriar módulos, apagar decisões anteriores ou tratar entregas aprovadas como rascunho.

Antes de qualquer alteração, deve ser respondido:

1. Qual problema real essa mudança resolve?
2. Ela aumenta valor para o escritório?
3. Ela preserva o que já foi validado?
4. Ela mantém revisão humana do advogado?
5. Ela evita risco jurídico, técnico e comercial?
6. Ela pode ser feita sem quebrar a esteira existente?

Se a resposta não for clara, a mudança não deve ser feita.

Este projeto deve evoluir como produto de mercado: com cautela, rastreabilidade, testes, documentação, QA e responsabilidade.

## Princípio central

A plataforma deve organizar a operação jurídica antes, durante e depois da produção documental.

O objetivo não é apenas gerar peças.

O objetivo é ajudar o escritório a controlar:

- cliente;
- contato;
- documentos;
- provas;
- pendências;
- testemunhas;
- prontidão;
- dossiê interno;
- revisão humana;
- próximos passos operacionais.

Nenhum recurso deve sugerir protocolo automático ou decisão jurídica sem advogado.

## Estado atual validado

### 1. Cliente e WhatsApp

Tags relacionadas:

- `v0.1.33-client-whatsapp-contact-v1`
- `v0.1.34-client-whatsapp-contact-audit-v1`
- `v0.1.35-client-whatsapp-message-templates-v1`
- `v0.1.36-client-whatsapp-contact-history-v1`
- `v0.1.37-client-whatsapp-contact-history-qa`

Status: validado.

O sistema já permite:

- cadastrar cliente no caso;
- registrar WhatsApp;
- registrar consentimento;
- abrir WhatsApp com mensagem segura;
- usar mensagens prontas;
- registrar contato manualmente;
- visualizar histórico de contatos no card do caso.

Escopo preservado:

- sem WhatsApp Business API;
- sem webhook;
- sem captura automática de conversa real;
- sem envio automático sem ação do advogado.

## 2. Grade de Testemunhas/Depoentes

Tags relacionadas:

- `v0.1.38-case-witness-grid-v1`
- `v0.1.39-case-witness-grid-qa`

Status: validado.

O sistema já permite:

- carregar grade de pessoas do caso;
- adicionar testemunha/depoente V1;
- registrar papel;
- registrar o que a pessoa sabe;
- exibir risco, confirmação e pontos sensíveis;
- persistir dados após reload.

Base técnica:

- `case_party_states`;
- `case_parties`;
- `party_metadata`.

Escopo preservado:

- sem tabela nova;
- sem migration;
- sem instrução de testemunha a mentir;
- sem resposta pronta induzida;
- sem automação jurídica sem advogado.

## 3. Checklist de Provas e Pendências

Tags relacionadas:

- `v0.1.40-case-evidence-checklist-v1`
- `v0.1.41-case-evidence-checklist-qa`

Status: validado.

O sistema já permite:

- criar item pendente;
- controlar status operacional;
- marcar item como solicitado, recebido, validado, dispensado ou em revisão;
- registrar prioridade;
- registrar prazo;
- registrar solicitante;
- registrar observação;
- vincular opcionalmente com anexo;
- preservar fluxo antigo de anexos/provas.

Base técnica:

- tabela `case_evidence_checklist_items`;
- rota `/api/v1/cases/{case_id}/evidence-checklist`;
- integração no painel de Provas e Anexos.

Escopo preservado:

- anexos continuam em `case_attachments`;
- checklist não deve ser misturado com arquivo anexado;
- sem IA automática neste ciclo;
- sem decisão jurídica automática.

## 4. Anexos e Provas

Status: preservado e revalidado.

O sistema já permite:

- upload de arquivo;
- listagem de anexo;
- download;
- exclusão;
- categoria;
- descrição;
- data da prova.

QA recente confirmou que o fluxo continuou funcionando após o Checklist de Provas e Pendências V1.

Escopo preservado:

- não quebrar upload/download/delete;
- não substituir armazenamento por improviso;
- não misturar pendência operacional com arquivo real.

## 5. Prontidão do Caso

Tags relacionadas:

- `v0.1.42-case-readiness-v1`
- `v0.1.43-case-readiness-qa`

Status: validado.

O sistema já permite calcular uma régua operacional do caso com:

- score de 0 a 100%;
- status operacional;
- contatos;
- testemunhas;
- checklist;
- pendências;
- anexos;
- pendências principais;
- aviso de segurança.

Status possíveis:

- `Crítico`;
- `Em preparação`;
- `Quase pronto`;
- `Pronto para revisão do advogado`.

Regra obrigatória:

`Pronto para revisão do advogado` não significa pronto para protocolo automático.

Significa apenas que, operacionalmente, o caso tem elementos mínimos para revisão humana supervisionada.

## 6. Dossiê Interno do Caso

Tags relacionadas:

- `v0.1.44-case-internal-dossier-v1`
- `v0.1.45-case-internal-dossier-qa`

Status: validado.

O sistema já exibe no card do caso:

- processo;
- score/status de prontidão;
- contadores;
- cliente;
- WhatsApp;
- último contato;
- pessoas-chave;
- provas/anexos;
- pendências abertas;
- próximos passos operacionais;
- aviso de segurança.

Aviso obrigatório:

`Dossiê interno é apoio operacional supervisionado, não peça processual e não protocolo automático.`

Escopo preservado:

- sem PDF/exportação neste ciclo;
- sem backend novo;
- sem migration;
- sem nova tabela;
- sem decisão jurídica automática.

## Régua de maturidade atual

### Esteira operacional do caso

Status: forte / validada.

Percentual estimado: 85%

Já existe base real para o escritório controlar um caso antes da produção final da peça.

### Produção documental assistida

Status: avançada / já existente em ciclos anteriores.

Percentual estimado: 75%

Editor jurídico, peças, audiência estratégica e exportação PDF já existem, mas devem continuar passando por revisão humana.

### Integração operacional com cliente

Status: funcional / manual supervisionado.

Percentual estimado: 60%

WhatsApp manual, mensagens prontas e logs existem. Ainda não há WhatsApp Business API, webhook ou automação externa.

### Produto comercial demonstrável

Status: em maturação.

Percentual estimado: 70%

A esteira já é demonstrável, mas a apresentação comercial e documentação consolidada ainda podem melhorar.

### Automação avançada

Status: propositalmente limitada.

Percentual estimado: 25%

Não deve avançar sem necessidade real, revisão de segurança e clareza jurídica.

## O que NÃO fazer agora sem justificativa forte

Não criar nova área jurídica só por criar.

Não criar nova tabela se a dor puder ser resolvida com estrutura existente.

Não refazer arquitetura já validada.

Não transformar o produto em gerador automático de processo.

Não prometer decisão jurídica automática.

Não prometer protocolo automático.

Não implementar WhatsApp Business API antes de existir necessidade operacional real.

Não criar PDF/exportação do dossiê antes de validar que o advogado realmente precisa disso.

Não poluir o card do caso com botões infinitos.

Não trocar segurança por velocidade.

## Próximos ciclos permitidos

### 1. Integração Checklist + WhatsApp

Só deve ser feita se gerar ganho operacional real.

Ideia permitida:

- botão para pedir ao cliente as pendências abertas do checklist;
- mensagem montada com itens pendentes;
- registro manual no histórico de contato;
- abertura via `wa.me`;
- sem envio automático oculto;
- sem webhook.

### 2. Melhoria visual premium dos formulários

Permitido se o objetivo for venda, demonstração ou usabilidade real.

Foco:

- reduzir poluição visual;
- melhorar hierarquia;
- deixar blocos mais comerciais;
- preservar lógica existente.

### 3. Exportação futura do Dossiê Interno

Permitida apenas em ciclo separado.

Condição:

- manter como documento interno;
- não confundir com peça processual;
- deixar aviso de revisão humana;
- não protocolar automaticamente.

### 4. Documentação comercial controlada

Permitida e recomendada.

Foco:

- demonstrar a esteira para advogado/escritório;
- mostrar valor operacional;
- evitar linguagem de promessa jurídica;
- destacar supervisão humana.

## Próxima decisão recomendada

Antes de criar novo código, decidir se o próximo ciclo será:

1. integração Checklist + WhatsApp;
2. melhoria visual premium;
3. documentação comercial da esteira;
4. exportação futura do dossiê.

Recomendação atual:

Priorizar documentação consolidada e demonstração controlada antes de novas automações.

## Conclusão

A Plataforma IA Jurídica Pro / IA Trabalhista Robusta atingiu uma fase importante: deixou de ser apenas uma ferramenta de geração documental e passou a ter uma esteira operacional real de escritório.

O foco daqui para frente deve ser maturidade, clareza, segurança, usabilidade e valor comercial.

A regra é simples:

Construir apenas o que aumenta valor real para o escritório.

Nada de feature por vaidade.
Nada de automação perigosa.
Nada de bagunçar o que já está validado.

Este documento deve servir como trava de segurança para impedir que o projeto volte a ser tratado como estudo ou experimento. A plataforma deve continuar evoluindo como produto real, com foco em venda, uso supervisionado por advogados e operação prática de escritório.
