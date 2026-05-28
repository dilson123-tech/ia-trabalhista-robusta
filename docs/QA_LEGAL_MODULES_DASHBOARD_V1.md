# QA Visual — Legal Modules Dashboard V1

## Identificação

Projeto: IA Trabalhista Robusta / Plataforma IA Jurídica Pro
Checkpoint: QA_VISUAL_LEGAL_MODULES_DASHBOARD_OK
Data: 2026-05-27
Base validada: v0.1.13-legal-modules-dashboard-v1
Commit base: 9a8af37
PR relacionado: #165 feat(frontend): show legal modules on dashboard

## Natureza do projeto

Este projeto é uma plataforma jurídica real, em evolução para uso supervisionado por advogados/escritórios e futura comercialização.

Não é projeto de estudo, demo solta ou protótipo acadêmico.

A IA organiza, estrutura, analisa, gera minutas assistidas, controla documentos/provas e exporta PDF.

O advogado revisa, corrige, decide, aprova, assina e protocola.

A IA não substitui advogado, não promete resultado, não assina, não protocola e não decide estratégia final.

## Objetivo da validação

Validar visualmente que os módulos jurídicos oficiais da Plataforma IA Jurídica Pro aparecem no painel principal, no workspace Produção, consumindo a rota GET /api/v1/legal-modules.

## Escopo validado

Após a tag v0.1.13-legal-modules-dashboard-v1, foi validado que o painel exibe os 7 módulos oficiais:

1. Trabalhista
2. Cível
3. Consumidor
4. Família
5. Previdenciário / BPC-LOAS
6. Criminal
7. Civil/Ambiental

## Ambiente local usado

Backend:

- Porta: 8099
- Comando utilizado: PYTHONPATH=backend backend/.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8099

Frontend:

- Porta: 5173
- Acesso local/rede: http://192.168.1.20:5173

## Evidência funcional

O backend inicialmente não respondia ao curl porque o serviço não estava rodando na porta 8099.

Após subir o backend, o painel carregou corretamente os módulos jurídicos oficiais no workspace Produção.

## Resultado visual — desktop

Status: aprovado.

Validação observada:

- cards dos módulos aparecem no painel;
- grid renderiza corretamente;
- workspace Produção segue separado da Gestão Comercial;
- painel principal não quebrou;
- fluxo visual geral ficou funcional.

Observações não bloqueantes:

- textos internos dos cards ainda podem receber polimento futuro;
- keywords aparecem sem acento por virem do registry técnico;
- Civil/Ambiental pode cair para linha própria dependendo da largura da tela.

Essas observações não bloqueiam o checkpoint.

## Resultado visual — mobile/celular

Status: aprovado.

Validação observada:

- painel abriu no celular;
- cards dos módulos ficaram bonitos no mobile;
- layout foi considerado aprovado visualmente pelo usuário;
- não houve bloqueio visual reportado.

## Resultado final

Checkpoint aprovado:

QA_VISUAL_LEGAL_MODULES_DASHBOARD_OK

## Régua de estado atual

- Documento multiárea V1: 100%
- Registry multiárea backend: 100%
- Rota GET /api/v1/legal-modules: 100%
- Painel consumindo módulos jurídicos oficiais: 100%
- QA visual desktop dos cards: 100%
- QA visual mobile dos cards: 100%

## O que não foi feito neste checkpoint

- Não foi criada área Empresarial / Contratos / Cobrança.
- Não foi refeito QA antigo dos 14 casos oficiais.
- Não foi mexido em PDF/editor/documentos.
- Não foi mexido em banco/migrations.
- Não foi alterado fluxo de criação de caso.
- Não foi redesenhado o painel inteiro.

## Próximo passo recomendado

Não criar Empresarial ainda.

Próximo bloco recomendado:

1. criar checklists por módulo jurídico;
2. começar por Trabalhista, Criminal e Consumidor;
3. depois Família, Previdenciário/BPC-LOAS e Civil/Ambiental;
4. só depois iniciar Empresarial / Contratos / Cobrança V1.

## Trava para próximos chats

Não voltar a tratar os módulos jurídicos como “não exibidos no painel”.

A partir deste checkpoint, os módulos oficiais já aparecem visualmente no workspace Produção e foram validados em desktop e mobile.
