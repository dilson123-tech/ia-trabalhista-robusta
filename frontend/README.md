# Frontend — IA Trabalhista Robusta

Frontend oficial do painel web do produto IA Trabalhista Robusta.

## Papel no produto

- autenticação do usuário
- acesso ao workspace jurídico
- operação de casos, análises, editor e PDFs
- consumo da API FastAPI do backend

## Stack

- React
- TypeScript
- Vite

## Ambiente local

Instalar dependências:

```bash
cd ~/projetos/ia_trabalhista_robusta/frontend && npm install
```

Subir ambiente de desenvolvimento:

```bash
cd ~/projetos/ia_trabalhista_robusta/frontend && npm run dev -- --host 0.0.0.0
```

Build local:

```bash
cd ~/projetos/ia_trabalhista_robusta/frontend && npm run build
```

## Integração com backend

O frontend deve apontar para o backend oficial do projeto.

Durante desenvolvimento local, validar principalmente:

- login
- reidratação de sessão
- painel de capacidade/plano
- fluxo de caso -> análise -> decisão executiva -> editor -> PDF

## Diretriz

Este frontend não deve ser tratado como template genérico.
Ele faz parte de um produto real para mercado e deve evoluir com foco em estabilidade, clareza operacional e percepção premium.
