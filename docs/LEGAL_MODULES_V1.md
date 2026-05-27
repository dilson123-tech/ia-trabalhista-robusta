# Plataforma IA Jurídica Pro — Módulos Jurídicos V1

## Natureza do produto

A IA Trabalhista Robusta evolui para Plataforma IA Jurídica Pro, uma plataforma jurídica multiárea para uso supervisionado por advogado.

A IA organiza, estrutura, analisa, gera minutas assistidas e apoia a revisão documental. O advogado revisa, corrige, aprova, assina e protocola.

## Objetivo da modularização

Formalizar as áreas já existentes em módulos oficiais, com separação clara entre tipos de caso, fundamentos, checklists, documentos, minutas e regras de segurança.

Esta etapa não reconstrói a plataforma. Ela organiza a arquitetura multiárea sobre a base já validada.

## Módulos oficiais iniciais

### 1. Trabalhista

Foco:
- reclamação trabalhista;
- verbas rescisórias;
- horas extras;
- FGTS;
- insalubridade;
- periculosidade;
- checklist de provas trabalhistas;
- análise assistida e minuta editável supervisionada.

Status:
- fluxo real supervisionado validado no caso REAL-TRAB-001;
- PDF exportado com sucesso;
- módulo operacional em uso supervisionado.

### 2. Cível

Foco:
- cobrança civil;
- obrigação de fazer;
- indenização por dano moral/material;
- tutela de urgência;
- documentos contratuais e provas básicas.

Status:
- casos QA já existentes;
- precisa padronizar action_type e checklists oficiais.

### 3. Consumidor

Foco:
- produto com defeito;
- serviço não prestado;
- cobrança indevida;
- negativação;
- restituição;
- obrigação de fazer consumerista.

Status:
- casos QA já existentes;
- pode ser separado de cível como módulo próprio.

### 4. Família

Foco:
- alimentos;
- guarda;
- convivência;
- divórcio;
- partilha simples;
- documentos familiares;
- melhor interesse da criança quando aplicável.

Status:
- casos QA já existentes;
- precisa checklist próprio e linguagem sensível.

### 5. Previdenciário / BPC-LOAS

Foco:
- BPC/LOAS;
- idoso;
- pessoa com deficiência;
- vulnerabilidade social;
- CadÚnico;
- INSS;
- documentos sociais, médicos e econômicos.

Status:
- fluxo QA já existente;
- precisa deixar de ser tratado genericamente como cível e virar módulo próprio.

### 6. Criminal

Foco:
- liberdade provisória;
- habeas corpus inicial;
- relaxamento de prisão;
- resposta à acusação;
- revisão obrigatória por advogado;
- sem promessa de resultado;
- sem afirmação definitiva de culpa ou inocência.

Status:
- Criminal V1 Initial Package validado;
- hardening contra contaminação temática aplicado;
- módulo inicial funcional e blindado.

### 7. Civil/Ambiental

Foco:
- poeira;
- ruído;
- vibração;
- barreira de contenção;
- vizinhança;
- dano ambiental/civil;
- prova técnica/pericial.

Status:
- caso QA já existente;
- precisa documentação própria e checklist técnico.

## Próximo módulo planejado

### 8. Empresarial / Contratos / Cobrança

Foco planejado:
- cobrança contratual;
- prestação de serviço inadimplida;
- rescisão contratual;
- notificação extrajudicial;
- confissão de dívida;
- acordo extrajudicial;
- ação monitória simples;
- execução de título extrajudicial;
- análise de cláusulas;
- contrato de prestação de serviço.

Status:
- próximo módulo a ser criado após formalização dos módulos existentes.

## Regra de segurança jurídica

Nenhum módulo deve prometer resultado, substituir advogado ou gerar peça final sem revisão humana.

Toda minuta deve ser tratada como minuta assistida, sujeita a revisão, correção, aprovação, assinatura e protocolo pelo advogado responsável.

## Ordem estratégica

1. Formalizar módulos já existentes.
2. Mapear action_type e legal_area oficiais.
3. Criar checklists por módulo.
4. Padronizar linguagem e segurança por área.
5. Só depois criar Empresarial/Contratos/Cobrança V1.
