# Criminal Module V1 — Escopo Oficial

## 1. Natureza do módulo

O módulo Criminal V1 faz parte da evolução do IA Trabalhista Robusta para uma plataforma jurídica multiárea.

Este módulo é destinado a uso jurídico supervisionado por advogado habilitado. A IA atua como ferramenta de apoio para organizar fatos, estruturar informações, identificar pontos de atenção, sugerir minutas e controlar documentos/provas.

A IA não substitui o advogado, não decide estratégia final, não assina, não protocola e não deve ser tratada como autoridade jurídica autônoma.

Toda análise, minuta, peça, pedido, tese ou documento gerado pelo sistema deve ser obrigatoriamente revisado, validado e aprovado por advogado antes de qualquer uso externo.

## 2. Objetivo do Criminal V1

O objetivo do Criminal V1 é criar uma fundação segura, modular e auditável para lidar com casos criminais reais em ambiente supervisionado.

A prioridade não é criar uma área criminal completa de imediato, mas sim iniciar com fluxos de alto valor prático, mantendo segurança, rastreabilidade, revisão humana e controle de provas.

## 3. Princípios obrigatórios

- Não reconstruir a base atual do sistema.
- Reaproveitar a arquitetura existente de casos, documentos editáveis, anexos, versões, análise, minuta e exportação PDF.
- Usar `legal_area="criminal"` para identificar casos criminais.
- Usar `action_type` para identificar o tipo de medida criminal.
- Nunca apresentar documento criminal como peça final sem aprovação humana.
- Nunca expor percentual de êxito, promessa de resultado ou linguagem de garantia.
- Nunca orientar fuga, ocultação de prova, fraude processual, intimidação de testemunha ou qualquer conduta ilegal.
- Sempre destacar necessidade de revisão do advogado.
- Preservar histórico, versões, anexos e evidências.

## 4. Escopo inicial permitido

O Criminal V1 poderá apoiar inicialmente os seguintes fluxos:

### 4.1 Triagem criminal supervisionada

Organização inicial dos fatos, pessoas envolvidas, data, local, fase do procedimento, existência de prisão, documentos disponíveis, riscos urgentes e próximos passos jurídicos para avaliação do advogado.

### 4.2 Pedido de liberdade provisória

Apoio à estruturação de minuta para casos em que o advogado avalie juridicamente a possibilidade de liberdade provisória, com ou sem medidas cautelares.

### 4.3 Relaxamento de prisão

Apoio à estruturação de minuta quando houver indícios de ilegalidade formal ou material na prisão, sempre dependendo de revisão técnica do advogado.

### 4.4 Resposta à acusação

Apoio à organização de fatos, teses preliminares, mérito, provas, testemunhas e pedidos possíveis na fase de resposta à acusação.

### 4.5 Habeas corpus inicial

Apoio à estruturação inicial de habeas corpus em hipóteses de constrangimento ilegal, com tratamento especialmente cauteloso e revisão obrigatória do advogado.

## 5. Escopo fora do Criminal V1

Nesta primeira versão, o módulo não deve tentar cobrir de forma completa:

- Júri completo.
- Recursos criminais avançados.
- Execução penal completa.
- Acordo de não persecução penal completo.
- Colaboração premiada.
- Crimes financeiros complexos.
- Crimes eleitorais.
- Crimes militares.
- Atuação autônoma em flagrante sem advogado.
- Qualquer orientação operacional para prática ou ocultação de crime.

Esses temas poderão ser analisados futuramente, em módulos separados, com documentação própria e validação técnica específica.

## 6. Campos mínimos recomendados para caso criminal

Um caso criminal real deve conter, sempre que possível:

- Área jurídica: criminal.
- Tipo de ação ou medida.
- Nome ou identificação das partes envolvidas.
- Fase do procedimento.
- Data e local dos fatos.
- Existência ou não de prisão.
- Tipo de prisão, se houver.
- Autoridade policial ou judicial envolvida.
- Resumo objetivo dos fatos.
- Documentos recebidos.
- Provas disponíveis.
- Testemunhas conhecidas.
- Prazos urgentes.
- Riscos imediatos.
- Pendências para o advogado.

## 7. Provas e documentos esperados

Conforme o caso, o sistema poderá organizar:

- Boletim de ocorrência.
- Auto de prisão em flagrante.
- Nota de culpa.
- Decisão judicial.
- Ata de audiência de custódia.
- Denúncia.
- Citação/intimação.
- Certidões.
- Prints, conversas e registros digitais.
- Vídeos, fotos e áudios.
- Comprovantes de endereço.
- Documentos pessoais.
- Procuração.
- Declarações e documentos complementares.

O sistema deve registrar documentos/provas como anexos e preservar rastreabilidade.

## 8. Linguagem obrigatória

A linguagem das análises e minutas criminais deve ser:

- Técnica.
- Prudente.
- Sem promessa de resultado.
- Sem juízo definitivo de culpa ou inocência.
- Sem orientação ilegal.
- Com indicação clara de revisão obrigatória por advogado.

## 9. Integração com a arquitetura atual

O Criminal V1 deve usar a base já validada do sistema:

- Casos.
- `legal_area`.
- `action_type`.
- Anexos/provas.
- Análise.
- Editor Jurídico Vivo.
- Versões.
- Aprovação humana.
- Exportação PDF.
- Histórico.

Não deve haver reconstrução do sistema.

## 10. Critérios de aceite da primeira implementação

A primeira implementação técnica do Criminal V1 somente será considerada válida se:

- Criar caso com `legal_area="criminal"`.
- Preservar `action_type`.
- Gerar análise coerente com área criminal.
- Gerar minuta criminal inicial sem linguagem de promessa.
- Exigir revisão/aprovação humana.
- Exportar PDF não vazio.
- Preservar anexos/provas.
- Passar em testes determinísticos.
- Não quebrar casos trabalhistas, cíveis e civil_ambiental já existentes.

## 11. Ordem recomendada de evolução

1. Documentar escopo Criminal V1.
2. Mapear pontos de roteamento por área.
3. Adicionar fundação `criminal` na análise.
4. Adicionar fundação `criminal` no editor.
5. Criar testes de triagem criminal.
6. Criar teste de liberdade provisória.
7. Criar teste de resposta à acusação.
8. Validar PDF.
9. Validar anexos/provas.
10. Usar com advogado parceiro em caso real supervisionado.

## 12. Regra final

Criminal V1 é um módulo de apoio jurídico supervisionado.

A IA prepara. O advogado valida.

Nenhuma peça criminal gerada pelo sistema deve ser usada externamente sem revisão, aprovação e responsabilidade profissional do advogado.
