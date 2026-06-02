# QA Cliente WhatsApp — Histórico Visual V1

## Checkpoint

`QA_CLIENT_WHATSAPP_CONTACT_HISTORY_VISUAL_OK`

## Data

2026-06-01 / 2026-06-02

## Contexto

Este QA valida visualmente o ciclo operacional do módulo WhatsApp/cliente da Plataforma IA Jurídica Pro.

O objetivo foi confirmar, no painel local, que o advogado consegue:

- cadastrar cliente no caso;
- cadastrar WhatsApp do cliente;
- registrar consentimento básico;
- abrir WhatsApp pelo card do caso;
- registrar contato manual;
- abrir mensagens prontas;
- registrar automaticamente mensagens prontas no log;
- visualizar o histórico recente de contatos no próprio card do caso.

## Ambiente validado

Backend local:

`http://127.0.0.1:8099`

Frontend local:

`http://127.0.0.1:5173`

Correção necessária durante QA:

O frontend estava apontando para IP antigo em `.env.local`:

`http://192.168.1.20:8099/api/v1`

Foi corrigido localmente para:

`VITE_API_URL=http://127.0.0.1:8099/api/v1`

Após reiniciar o Vite, o login e o painel funcionaram corretamente.

## Usuário QA local

Usuário criado via seed local:

`admin_whatsapp_qa@example.com`

Login foi validado por `curl` com HTTP 200 e retorno de `access_token`.

## Fluxo visual validado

No card do caso, foram confirmados visualmente:

- cliente exibido;
- WhatsApp exibido;
- consentimento exibido;
- botão `Abrir WhatsApp`;
- botão `Registrar contato`;
- bloco `Mensagens prontas`;
- botões:
  - `Pedir documentos`;
  - `Pedir provas`;
  - `Lembrar audiência`;
  - `Avisar andamento`;
  - `Confirmar dados`;
- bloco `Histórico de contatos`;
- botão `Atualizar`.

## Evidência funcional observada

O histórico exibiu corretamente:

1. Registro manual:

`01/06/2026, 22:49 — whatsapp / outgoing`

Resumo:

`Contato realizado via WhatsApp`

2. Mensagem pronta:

`01/06/2026, 22:51 — whatsapp / outgoing`

Resumo:

`Solicitação de documentos pelo WhatsApp`

Observação:

`Mensagem pronta aberta: Pedir documentos`

## Resultado

`QA_CLIENT_WHATSAPP_CONTACT_HISTORY_VISUAL_OK`

O ciclo completo foi validado visualmente:

- abrir WhatsApp;
- registrar contato;
- abrir mensagem pronta;
- registrar log automático;
- visualizar histórico no card do caso.

## Escopo preservado

Esta entrega continua segura:

- sem WhatsApp Business API;
- sem webhook;
- sem captura automática de conversa real;
- sem leitura de mensagens privadas;
- sem envio automático sem ação do advogado;
- sem salvar conteúdo recebido do WhatsApp.

## Sequência oficial do módulo WhatsApp/cliente

- `v0.1.33-client-whatsapp-contact-v1`
  - contato/WhatsApp no caso;
  - consentimento básico;
  - botão Abrir WhatsApp.

- `v0.1.34-client-whatsapp-contact-audit-v1`
  - tabela/log manual de contato;
  - rotas GET/POST de contact logs;
  - botão Registrar contato.

- `v0.1.35-client-whatsapp-message-templates-v1`
  - mensagens prontas;
  - log automático ao abrir mensagem pronta.

- `v0.1.36-client-whatsapp-contact-history-v1`
  - histórico visual no card do caso;
  - últimos 5 contatos;
  - botão Atualizar.

## Próximo passo recomendado

Depois deste QA visual, a próxima prioridade não é WhatsApp Business API.

A próxima prioridade é completar a esteira operacional do caso jurídico real:

1. Grade de testemunhas/depoentes;
2. Checklist de provas e pendências;
3. Prontidão do caso;
4. Dossiê interno do caso;
5. Depois validar com casos reais em escritório/parceria com advogado.

