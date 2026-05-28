# Audiência Estratégica V1

## Identificação

Projeto: IA Trabalhista Robusta / Plataforma IA Jurídica Pro
Documento: Audiência Estratégica V1
Status: definição funcional e estratégica antes da implementação
Base recomendada: após v0.1.16-legal-module-checklists-v2

## Natureza do projeto

Este projeto é uma plataforma jurídica real, em evolução para uso supervisionado por advogados/escritórios e futura comercialização.

Não é projeto de estudo, demo solta ou protótipo acadêmico.

A IA organiza, estrutura, analisa, gera minutas assistidas, controla documentos/provas, apoia estratégia de audiência e exporta PDF.

O advogado revisa, corrige, decide, aprova, assina, pergunta em audiência e protocola.

A IA não substitui advogado, não promete resultado, não assina, não protocola, não decide estratégia final e não conduz audiência.

## Origem da necessidade

Durante teste real supervisionado no processo 0008577-74.2019.8.16.0035, PRATIC SIDER x Dilson Pereira, a advogada demonstrou interesse específico em saber se a plataforma consegue pensar e organizar perguntas para audiência.

O teste revelou que a plataforma já entende tese, risco, fatos relevantes e prova oral, mas o editor atual ainda tende a gerar peça processual formal quando o usuário precisa de roteiro de audiência.

Problema observado:

- o caso era cível;
- o objetivo era roteiro de perguntas;
- o sistema gerou manifestação/petição formal;
- a entrega útil precisou ser reorganizada como roteiro estratégico de audiência.

Conclusão de produto:

Antes de criar novos tipos de processos ou nova área Empresarial, devemos fortalecer os módulos existentes com um recurso transversal de audiência estratégica.

## Objetivo do módulo

Criar um fluxo próprio para gerar roteiros estratégicos de audiência, separados do motor de petição.

O módulo deve ajudar o advogado a:

- organizar perguntas por pessoa ou parte;
- separar perguntas essenciais;
- identificar perguntas repetitivas;
- identificar perguntas perigosas;
- montar perguntas condicionais;
- preparar versão enxuta para audiência com pouco tempo;
- mapear pontos que precisam ser confirmados antes da audiência;
- transformar análise do caso e anexos em roteiro prático de prova oral.

## Nome funcional sugerido

Audiência Estratégica

Nomes secundários possíveis:

- Roteiro de Audiência
- Perguntas para Audiência
- Prova Oral Estratégica
- Preparação de Testemunhas
- Mapa de Audiência

## Escopo transversal

Este recurso deve funcionar nos módulos existentes:

1. Trabalhista
2. Cível
3. Consumidor
4. Família
5. Previdenciário / BPC-LOAS
6. Criminal
7. Civil/Ambiental

Não criar Empresarial / Contratos / Cobrança antes de consolidar este recurso nos módulos já existentes.

## Tipos documentais sugeridos

Criar tipos próprios, sem reaproveitar petição inicial ou manifestação genérica:

- audiencia_estrategica
- roteiro_audiencia
- perguntas_testemunhas
- prova_oral_estrategica

Esses tipos devem impedir que a IA gere automaticamente:

- endereçamento;
- qualificação completa das partes;
- pedidos processuais;
- estrutura de petição;
- conclusão típica de peça;
- linguagem de protocolo.

## Estrutura padrão da saída

A saída padrão do módulo deve conter:

1. Síntese da tese para audiência
2. Pontos que precisam ser provados
3. Perguntas indispensáveis para parte autora
4. Perguntas indispensáveis para parte ré
5. Perguntas para testemunhas da parte autora
6. Perguntas para testemunhas da parte ré
7. Perguntas por pessoa específica, quando houver nomes nos autos
8. Perguntas repetitivas que podem ser cortadas
9. Perguntas sensíveis ou perigosas
10. Perguntas condicionais
11. Versão curtíssima para audiência com pouco tempo
12. Pontos que o advogado deve confirmar antes da audiência
13. Observação de revisão profissional obrigatória

## Exemplo de organização por pessoa

Quando o caso trouxer pessoas específicas, o roteiro deve separar perguntas por nome.

Exemplo do caso PRATIC SIDER x Dilson Pereira:

- representante legal da autora;
- Edson Estevão;
- Rosangela de Lourdes Siqueira.

A IA deve evitar misturar perguntas de parte, representante e testemunha.

## Perguntas indispensáveis

Perguntas indispensáveis são aquelas diretamente ligadas ao núcleo da tese.

Critérios:

- ajudam a provar fato central;
- reduzem dúvida relevante;
- exploram contradição documental;
- confirmam posse, conduta, comunicação, ciência ou responsabilidade;
- não dependem de rodeio;
- podem ser feitas mesmo com tempo curto.

## Perguntas repetitivas

A IA deve apontar perguntas repetitivas quando várias perguntas buscam a mesma resposta com pequenas variações.

A saída deve sugerir:

- manter uma pergunta principal;
- usar a repetida apenas se houver evasiva;
- cortar perguntas que alongam audiência sem ganho probatório.

## Perguntas perigosas

A IA deve sinalizar perguntas que possam prejudicar a tese.

Exemplos:

- pergunta que reforça responsabilidade formal da própria parte;
- pergunta que abre tema sem prova documental;
- pergunta que permite confissão desfavorável;
- pergunta que parece induzir testemunha;
- pergunta agressiva ou especulativa;
- pergunta que afirma fato ainda não comprovado;
- pergunta que pode levar o depoente a explicar ponto fraco da parte contrária.

A IA não deve proibir a pergunta, mas deve marcar como “usar com cautela” e explicar o motivo.

## Perguntas condicionais

Perguntas condicionais só devem ser feitas se a resposta anterior abrir caminho.

Exemplo:

Se a parte autora admitir que sabia da participação de terceiro:
- perguntar desde quando sabia;
- perguntar por que não ouviu diretamente o terceiro;
- perguntar se a empresa documentou essa ciência.

Se a parte autora negar:
- perguntar por que o nome do terceiro aparece nos autos;
- perguntar se há documento que afaste a participação dele.

## Versão curtíssima

Todo roteiro deve trazer uma versão de emergência para audiência com pouco tempo.

Essa versão deve conter:

- 5 a 10 perguntas para a pessoa principal;
- 5 a 10 perguntas para a testemunha principal;
- foco nos pontos de prova indispensáveis;
- sem perguntas repetitivas;
- sem longas explicações.

## Pontos a confirmar pelo advogado

A IA deve listar pontos que precisam ser conferidos pelo advogado antes da audiência.

Exemplos:

- documento existe nos autos?
- a afirmação está na inicial, contestação ou réplica?
- a testemunha sabe por conhecimento direto ou por ouvir dizer?
- há risco de contradição?
- a pergunta pode reforçar responsabilidade formal?
- existe prova mínima para sustentar a pergunta?
- o tema foi delimitado no saneamento?
- a pessoa será ouvida como parte, representante ou testemunha?

## Regras por área jurídica

### Trabalhista

Focos comuns:

- vínculo;
- jornada;
- subordinação;
- salário;
- função;
- horas extras;
- intervalo;
- verbas rescisórias;
- dano moral;
- testemunha de rotina de trabalho.

Cuidado:

- perguntas que induzem testemunha;
- perguntas genéricas sobre jornada;
- perguntas que abrem espaço para confissão de informalidade prejudicial;
- cálculos sem base documental.

### Cível

Focos comuns:

- contrato;
- obrigação;
- inadimplemento;
- posse;
- dano;
- nexo causal;
- comunicação;
- quantificação;
- mitigação do prejuízo;
- boa-fé.

Cuidado:

- assumir culpa sem necessidade;
- reforçar responsabilidade formal;
- abrir discussão sobre fatos sem prova;
- perguntar sobre valor sem documento.

### Consumidor

Focos comuns:

- relação de consumo;
- defeito/falha;
- protocolo;
- tentativa de solução;
- pagamento;
- fornecedor;
- negativação;
- dano material;
- dano moral.

Cuidado:

- presumir dano moral automático;
- perguntar sem comprovante;
- confundir mero aborrecimento com dano relevante;
- deixar fornecedor explicar solução oferecida sem contraponto.

### Família

Focos comuns:

- melhor interesse do menor;
- rotina;
- cuidados;
- alimentos;
- renda;
- despesas;
- convivência;
- acordos anteriores;
- risco ou urgência.

Cuidado:

- exposição desnecessária de menor;
- linguagem agressiva;
- acusações sem prova;
- perguntas que aumentam conflito familiar.

### Previdenciário / BPC-LOAS

Focos comuns:

- incapacidade;
- impedimento de longo prazo;
- renda;
- composição familiar;
- CadÚnico;
- requerimento administrativo;
- indeferimento;
- documentos médicos;
- vulnerabilidade.

Cuidado:

- substituir perícia;
- afirmar doença/incapacidade sem laudo;
- confundir benefício assistencial com previdenciário;
- exagerar vulnerabilidade sem prova.

### Criminal

Focos comuns:

- legalidade da prisão;
- autoria;
- materialidade;
- reconhecimento;
- cadeia de custódia;
- fundamentação;
- contradições;
- testemunha policial;
- vítima;
- álibi;
- cautelares.

Cuidado:

- não afirmar culpa/inocência definitiva;
- não orientar conduta ilícita;
- não criar tese sem autos;
- não perguntar algo que reforce confissão;
- sempre exigir revisão por advogado criminalista.

### Civil/Ambiental

Focos comuns:

- dano;
- nexo causal;
- ruído;
- poeira;
- vibração;
- prova técnica;
- vizinhança;
- fiscalização;
- laudo;
- continuidade do impacto.

Cuidado:

- afirmar nexo sem prova técnica;
- exagerar dano;
- perguntar sobre laudo inexistente;
- confundir incômodo comum com dano juridicamente relevante.

## O que o módulo não deve fazer

O módulo Audiência Estratégica não deve:

- gerar petição inicial;
- gerar manifestação processual;
- gerar contestação;
- gerar habeas corpus;
- gerar endereçamento ao juízo;
- criar pedidos processuais;
- inventar fatos;
- inventar testemunhas;
- inventar documentos;
- instruir testemunha a mentir;
- sugerir resposta pronta para testemunha;
- prometer resultado;
- substituir a estratégia da advogada.

## Linguagem esperada

A linguagem deve ser:

- objetiva;
- técnica;
- respeitosa;
- prática;
- própria para audiência;
- organizada por blocos;
- fácil de copiar para PDF;
- clara para revisão do advogado.

## Critérios de sucesso da V1

A V1 será considerada pronta quando:

- existir tipo documental próprio para audiência estratégica;
- o sistema não gerar peça formal quando o usuário pedir roteiro;
- o roteiro sair separado por pessoa;
- houver seção de perguntas perigosas;
- houver seção de perguntas repetitivas;
- houver seção de perguntas condicionais;
- houver versão curta;
- houver pontos a confirmar pelo advogado;
- o caso PRATIC SIDER x Dilson Pereira for reprocessado com saída adequada;
- o resultado puder ser exportado em PDF.

## Caso piloto recomendado

Caso: 0008577-74.2019.8.16.0035
Partes: PRATIC SIDER x Dilson Pereira
Área: Cível
Tipo: audiência de instrução / prova oral
Objetivo: roteiro de perguntas para representante da autora e testemunhas.

Pessoas principais:

- representante legal da autora;
- Edson Estevão;
- Rosangela de Lourdes Siqueira.

Focos:

- Edson como usuário/condutor de fato;
- Dilson como locatário formal;
- ciência da empresa sobre a participação de Edson;
- comunicação do desaparecimento/furto;
- boletim de ocorrência;
- seguro;
- diligências internas da autora;
- quantificação do dano;
- boa-fé.

## Próximo passo técnico recomendado

Após merge deste documento:

1. mapear tipos documentais atuais do editor;
2. adicionar tipo audiencia_estrategica;
3. criar prompt próprio separado do prompt de petição;
4. criar teste determinístico com caso 282 ou fixture equivalente;
5. validar que a saída não contém endereçamento nem estrutura de petição;
6. validar que contém perguntas por pessoa;
7. validar exportação PDF;
8. só depois pensar em novos tipos de processo.

## Trava estratégica

Antes de criar novos tipos de processos ou novas áreas, priorizar a implementação de Audiência Estratégica nos módulos já existentes.

Este recurso responde a uma dor real observada em validação com advogada: organização de perguntas para audiência.

Não transformar esta feature em petição disfarçada.
