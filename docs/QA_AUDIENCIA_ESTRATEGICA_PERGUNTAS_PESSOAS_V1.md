# QA — Audiência Estratégica com Perguntas por Pessoa V1

## Identificação

Projeto: IA Trabalhista Robusta / Plataforma IA Jurídica Pro  
Marco técnico: v0.1.19-audiencia-perguntas-pessoas  
Data: 2026-05-29  
Status: aprovado em validação funcional real supervisionada

## Natureza do projeto

Este projeto é uma plataforma jurídica real em evolução para uso supervisionado por advogados/escritórios e futura comercialização.

Não é projeto de estudo.

A plataforma apoia análise, organização estratégica, geração de documentos editáveis, controle de versões, aprovação e exportação PDF.

O advogado continua responsável por revisar, ajustar, aprovar, assinar, protocolar e conduzir audiência.

## Objetivo deste QA

Validar que o módulo Audiência Estratégica deixou de gerar apenas perguntas genéricas e passou a gerar perguntas específicas por pessoa identificada no contexto do caso.

## Caso validado

- Caso interno: 282
- Processo: 0008577-74.2019.8.16.0035
- Caso: PRATIC SIDER x Dilson Pereira
- Área: Cível
- Documento: 135
- Tipo documental: AUDIENCIA_ESTRATEGICA
- Versão aprovada validada: 18
- PDF exportado: roteiro estratégico de audiência v18
- Total do PDF: 7 páginas

## Escopo funcional validado

O fluxo validado foi:

1. Documento de Audiência Estratégica já existente
2. Nova geração de roteiro após patch de perguntas por pessoa
3. Criação de versão com bloco novo
4. Aprovação da versão 18
5. Exportação PDF
6. Conferência visual e textual do PDF exportado

## Resultado esperado

O PDF deveria conter, além dos blocos gerais de audiência, um bloco específico chamado:

- Perguntas por pessoa identificada

## Resultado obtido

Resultado aprovado.

O PDF exportado da versão 18 contém o bloco:

- Perguntas por pessoa identificada

Com perguntas separadas para:

- Representante da PRATIC SIDER / parte autora
- Edson Estevão
- Dilson Pereira / parte ré

## Estrutura do PDF validado

O PDF exportado contém:

1. Síntese da tese para audiência
2. Pontos que precisam ser provados
3. Perguntas indispensáveis para parte autora / representante da autora
4. Perguntas indispensáveis para parte ré
5. Perguntas para testemunhas
6. Perguntas por pessoa identificada
7. Perguntas repetitivas e perguntas perigosas
8. Perguntas condicionais
9. Versão curtíssima para audiência com pouco tempo
10. Pontos que o advogado deve confirmar antes da audiência

## Evidências da versão aprovada

Documento 135:

- status: approved
- current_version_number: 18
- document_type: audiencia_estrategica
- versão aprovada: 18
- HAS_PEOPLE_BLOCK: True

## Validações locais realizadas

- py_compile OK
- npm run build OK
- git diff --check OK
- CI GitHub OK no PR funcional
- PDF exportado com conteúdo real
- PDF exportado com bloco de perguntas por pessoa identificada

## Observação sobre Rosangela

Rosangela de Lourdes Siqueira ainda não apareceu no PDF desta geração.

Motivo provável: o nome não estava presente no contexto consolidado usado pelo detector nesta versão.

Próximo refinamento recomendado:

- ampliar detecção de pessoas usando partes do caso
- anexos
- metadados
- nomes manuais informados pelo advogado
- documentos do processo

## Decisão de produto

O módulo Audiência Estratégica deve continuar sendo tratado como recurso transversal premium da Plataforma IA Jurídica Pro.

Antes de expandir para novas áreas ou novos tipos de processo, a prioridade é fortalecer recursos úteis em escritório real, especialmente:

- audiência
- prova oral
- perguntas por pessoa
- perguntas perigosas
- perguntas condicionais
- versão curta
- comparação com roteiro de advogado

## Status final

QA_AUDIENCIA_ESTRATEGICA_PESSOAS_V1_OK

O marco v0.1.19 está validado como primeiro refinamento funcional do roteiro de audiência com perguntas por pessoa real do processo.
