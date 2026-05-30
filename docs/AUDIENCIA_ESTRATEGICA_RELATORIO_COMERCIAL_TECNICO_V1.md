# Relatório Comercial e Técnico — Módulo Audiência Estratégica V1

## Plataforma IA Jurídica Pro

Este documento apresenta o estado atual do módulo **Audiência Estratégica** da Plataforma IA Jurídica Pro, produto real em construção para uso comercial por advogados e escritórios.

A Audiência Estratégica é um recurso premium voltado à preparação de audiência, prova oral, organização de perguntas por pessoa, identificação de pontos críticos e apoio à atuação supervisionada do advogado.

---

## 1. Objetivo do módulo

O objetivo do módulo Audiência Estratégica é transformar os dados do caso em um roteiro prático de preparação para audiência.

O sistema organiza:

- síntese da tese para audiência;
- pontos que precisam ser provados;
- perguntas por pessoa/parte/testemunha;
- perguntas perigosas;
- perguntas repetitivas;
- perguntas condicionais;
- versão curta para uso rápido;
- pontos que o advogado precisa confirmar antes da audiência;
- material final exportável em PDF.

Importante: o roteiro não substitui o advogado. Ele é material de apoio estratégico supervisionado.

---

## 2. O que o módulo não é

A Audiência Estratégica não é:

- petição inicial;
- contestação;
- manifestação;
- recurso;
- sentença;
- parecer definitivo;
- peça automática para protocolo;
- promessa de resultado;
- substituto da análise jurídica humana.

Ela é um roteiro interno para preparação da audiência e prova oral.

---

## 3. Fluxo funcional validado

O fluxo validado é:

1. criação ou seleção do caso;
2. análise técnica do caso;
3. criação do documento `AUDIENCIA_ESTRATEGICA`;
4. geração do roteiro assistido;
5. edição/revisão pelo advogado;
6. aprovação de versão;
7. exportação em PDF;
8. uso como material de apoio à audiência.

O módulo usa o mesmo conceito do **Editor Jurídico Vivo**, com versionamento, aprovação e exportação.

---

## 4. Áreas já validadas

### 4.1 Cível

O fluxo cível foi validado com perguntas por pessoas específicas em caso envolvendo:

- PRATIC SIDER;
- Dilson Pereira;
- Edson Estevão;
- Rosangela de Lourdes Siqueira;
- locação de carreta;
- desaparecimento/furto;
- boletim de ocorrência;
- relação entre partes e testemunhas.

O módulo gera perguntas específicas para cada pessoa, evitando roteiro genérico.

### 4.2 Criminal

A Audiência Estratégica Criminal está validada com fluxo E2E e PDF.

Papéis contemplados:

- vítima / ofendido;
- policial militar / agente da abordagem;
- policial civil / investigador;
- delegado / autoridade policial;
- testemunha de acusação;
- testemunha de defesa;
- acusado / réu;
- perito / responsável por laudo.

Pontos sensíveis tratados:

- cadeia de custódia;
- risco de autoincriminação;
- prova direta e indireta;
- reconhecimento;
- abordagem;
- diligências;
- materialidade;
- autoria;
- limitações de laudo.

### 4.3 Trabalhista

A Audiência Estratégica Trabalhista está validada com fluxo E2E e PDF.

Papéis contemplados:

- reclamante / empregado;
- preposto / representante da reclamada;
- testemunha do reclamante;
- testemunha da reclamada;
- gestor / encarregado;
- RH / responsável por folha, ponto e rescisão;
- técnico de segurança / medicina do trabalho;
- perito / responsável por laudo trabalhista.

Temas contemplados:

- jornada;
- controle de ponto;
- horas extras;
- intervalo intrajornada;
- FGTS;
- verbas rescisórias;
- holerites;
- TRCT;
- EPI;
- insalubridade;
- periculosidade;
- prova documental;
- prova testemunhal.

### 4.4 Consumidor

A Audiência Estratégica Consumidor está validada com fluxo E2E e PDF.

Papéis contemplados:

- consumidor / autor;
- fornecedor / empresa ré;
- atendente / suporte / SAC / ouvidoria;
- representante comercial / vendedor / loja;
- testemunha do consumidor;
- testemunha do fornecedor;
- responsável financeiro / cobrança / negativação;
- técnico / assistência / perito do produto ou serviço.

Temas contemplados:

- relação de consumo;
- cobrança indevida;
- negativação;
- banco;
- fornecedor;
- contrato contestado;
- faturas;
- protocolos de atendimento;
- SAC;
- ouvidoria;
- oferta/publicidade;
- dano material;
- dano moral;
- baixa de restrição;
- restituição;
- obrigação de fazer/não fazer.


### 4.5 Família

A Audiência Estratégica Família está validada com fluxo E2E e PDF.

Papéis contemplados:

- genitor / requerente;
- genitor / requerido;
- criança / adolescente, quando houver escuta adequada;
- responsável financeiro / alimentos;
- testemunha familiar;
- testemunha escolar / cuidador / profissional próximo;
- assistente social / equipe técnica;
- psicólogo / perito psicossocial.

Temas contemplados:

- guarda;
- alimentos;
- convivência;
- divórcio;
- união estável;
- alienação parental;
- renda;
- rotina da criança;
- melhor interesse da criança/adolescente;
- estudo social;
- avaliação psicossocial;
- testemunhas familiares;
- prova documental.

### 4.6 Previdenciário/BPC-LOAS

A Audiência Estratégica Previdenciário/BPC-LOAS está validada com fluxo E2E e PDF.

Papéis contemplados:

- requerente / segurado;
- familiar cuidador / responsável pela rotina;
- representante legal / procurador;
- médico assistente / profissional de saúde;
- perito médico;
- assistente social / avaliador social;
- servidor / representante do INSS;
- testemunha sobre rotina, incapacidade e vulnerabilidade.

Temas contemplados:

- BPC/LOAS;
- benefício assistencial;
- benefício por incapacidade;
- deficiência;
- impedimento de longo prazo;
- incapacidade funcional;
- laudos médicos;
- receitas;
- exames;
- CadÚnico;
- NIS;
- renda familiar;
- grupo familiar;
- cuidador;
- avaliação social;
- perícia médica;
- INSS;
- indeferimento administrativo;
- rotina diária;
- vulnerabilidade;
- prova testemunhal.

---

## 5. Contexto Estruturado V2

O módulo evoluiu para usar contexto estruturado do caso.

Além da descrição textual e da análise, a Audiência Estratégica agora considera:

- partes cadastradas;
- papéis das partes;
- pessoas ativas;
- pessoas históricas;
- representantes;
- relações entre pessoas/partes;
- eventos relevantes;
- anexos/provas cadastrados;
- metadados estruturados do caso.

Isso permite que o roteiro seja mais próximo da realidade do escritório, com nomes, documentos e relações do caso concreto.

---

## 6. Tipo documental único

O módulo reaproveita o tipo documental:

`AUDIENCIA_ESTRATEGICA`

Não foram criados tipos duplicados para cada área.

Isso mantém a arquitetura limpa:

- um tipo documental;
- especialização por área;
- reaproveitamento do motor de geração;
- reaproveitamento do Editor Jurídico Vivo;
- reaproveitamento do motor de PDF;
- controle de versão único;
- aprovação unificada.

---

## 7. Validações técnicas realizadas

O módulo possui testes automatizados para:

- perguntas por pessoa;
- detecção de área criminal;
- detecção de área trabalhista;
- detecção de área consumidor;
- preservação do fluxo cível;
- preservação do fluxo criminal;
- preservação do fluxo trabalhista;
- uso de contexto estruturado;
- uso de anexos/provas;
- criação de documento;
- geração de roteiro;
- aprovação de versão;
- exportação PDF.

---

## 8. Marcos versionados

Linha oficial do módulo Audiência Estratégica:

- `v0.1.17-audiencia-estrategica-v1`
- `v0.1.18-audiencia-estrategica-document-type`
- `v0.1.19-audiencia-perguntas-pessoas`
- `v0.1.20-audiencia-pessoas-qa`
- `v0.1.21-criminal-audiencia-estrategica-v1`
- `v0.1.22-criminal-audiencia-qa`
- `v0.1.23-trabalhista-audiencia-estrategica-v1`
- `v0.1.24-audiencia-pessoas-contexto-v2`
- `v0.1.25-consumidor-audiencia-estrategica-v1`
- `v0.1.26-audiencia-estrategica-relatorio-comercial-v1`
- `v0.1.27-familia-audiencia-estrategica-v1`
- `v0.1.28-legal-module-coverage-matrix-v1`
- `v0.1.29-previdenciario-bpc-loas-audiencia-estrategica-v1`

---

## 9. Estado atual da régua

- Base da Audiência Estratégica: 100%
- Tipo documental único: 100%
- Geração assistida: 100%
- Versionamento: 100%
- Aprovação: 100%
- Exportação PDF: 100%
- Cível com perguntas por pessoa: 100%
- Criminal com E2E/PDF: 100%
- Trabalhista com E2E/PDF: 100%
- Consumidor com E2E/PDF: 100%
- Contexto Estruturado V2: 100%
- Família com E2E/PDF: 100%
- Previdenciário/BPC-LOAS com E2E/PDF: 100%
- Civil/Ambiental: planejado
- Empresarial/Contratos/Cobrança: planejado para etapa posterior

---

## 10. Valor comercial para escritórios

O módulo entrega valor porque ajuda o advogado a:

- preparar audiência com mais organização;
- evitar perguntas genéricas;
- separar perguntas por pessoa;
- mapear pontos fracos;
- mapear pontos fortes;
- revisar documentos e anexos;
- evitar perguntas perigosas;
- criar versão curta para uso rápido;
- gerar material PDF de apoio;
- manter histórico e versionamento;
- trabalhar com supervisão profissional.

Esse tipo de recurso pode ser apresentado como diferencial premium para escritórios que lidam com volume de casos e precisam padronizar qualidade sem perder personalização.

---

## 11. Limites e segurança

O sistema mantém limites importantes:

- não promete resultado;
- não substitui decisão do advogado;
- não afirma culpa/inocência definitiva em criminal;
- não inventa prova;
- não inventa documento;
- não dispensa revisão humana;
- não transforma roteiro em peça processual automaticamente;
- exige aprovação final supervisionada.

---

## 12. Próximas evoluções recomendadas

### 12.1 Família

Próxima área recomendada para Audiência Estratégica:

- guarda;
- alimentos;
- convivência;
- divórcio;
- união estável;
- alienação parental;
- estudo social;
- renda;
- rotina da criança;
- testemunhas familiares.

### 12.2 Previdenciário/BPC-LOAS

Status atual:

- validado com E2E/PDF;
- cobre requerente/segurado;
- familiar cuidador;
- médico assistente;
- perito médico;
- assistente social/avaliador social;
- servidor/representante do INSS;
- testemunha sobre rotina, incapacidade e vulnerabilidade;
- prova médica/social;
- CadÚnico;
- renda familiar;
- perícia.

### 12.3 Civil/Ambiental

Possível evolução:

- dano;
- vizinhança;
- responsabilidade civil;
- laudos;
- fiscalização;
- testemunhas;
- perícia;
- nexo causal.

### 12.4 Interface guiada

Melhorar a interface para cadastro guiado antes da geração do roteiro:

- partes;
- representantes;
- testemunhas;
- documentos;
- anexos;
- eventos;
- relações;
- observações estratégicas.

---

## 13. Conclusão

O módulo Audiência Estratégica já saiu do estágio conceitual.

Ele possui base técnica validada, especialização por área, testes automatizados, fluxo E2E, aprovação, versionamento e PDF.

Atualmente, o módulo cobre:

- Cível;
- Criminal;
- Trabalhista;
- Consumidor;
- Família;
- Previdenciário/BPC-LOAS.

Com Contexto Estruturado V2, ele passa a aproveitar dados reais cadastrados no caso, tornando o produto mais próximo da rotina prática de um escritório de advocacia.

Este é um recurso com alto potencial comercial, especialmente como diferencial premium da Plataforma IA Jurídica Pro.
