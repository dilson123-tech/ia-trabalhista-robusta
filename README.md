# IA Trabalhista Robusta

Plataforma jurídica SaaS em evolução, com foco inicial em **demandas trabalhistas**, preparada para operar com **multi-tenant**, **autenticação JWT**, **auditoria**, **análise assistida por IA**, **relatórios executivos** e **PDF**.

> O projeto nasce como **IA Trabalhista Robusta**, mas a arquitetura e a evolução do produto já consideram o futuro como núcleo inicial de uma **plataforma jurídica multicausa**, preparada para incorporar módulos como:
> **Trabalhista, Criminal, Família, Cível, Previdenciário, Empresarial** e outras áreas.

---

## Visão do produto

Hoje o sistema entrega, no núcleo do MVP:

- autenticação e controle de acesso
- segregação por tenant/escritório
- criação e consulta de casos
- análise técnica inicial
- diagnóstico estratégico
- decisão executiva assistida
- relatório HTML
- PDF executivo
- controle de uso/plano
- auditoria administrativa

Em termos de produto, a proposta é simples:

**transformar um caso cadastrado em análise executiva documentada, com base operacional séria para escritórios.**

---

## Status atual do MVP

O projeto já possui base funcional para:

- fluxo principal ponta a ponta
- auth com tenant
- health e readiness
- smoke operacional
- geração de relatório/PDF
- backoffice administrativo inicial

Ainda em evolução para nível premium de mercado:

- refinamento do relatório/PDF
- documentação operacional completa
- blindagem adicional de produção
- posicionamento comercial final
- expansão modular futura para outras áreas jurídicas

---

## Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- JWT
- Middleware de auditoria
- WeasyPrint / fpdf2 para PDF executivo

---

## Estrutura principal

- `backend/` → aplicação FastAPI
- `scripts/` → scripts de subida e smoke
- `docs/` → regras, roadmap e registros de evolução
- `.env` / `.env.example` → configuração de ambiente
- `docker-compose.yml` → banco local PostgreSQL

---

## Ambiente local

Na raiz do projeto:

```bash
cp -n .env.example .env
```

### Observação importante

Para ambiente local com `docker-compose.yml`, a `DATABASE_URL` deve estar alinhada com o banco do compose:

```env
DATABASE_URL="postgresql+psycopg2://ia_user:ia_pass@127.0.0.1:55432/ia_trabalhista"
```

---

## Subir o banco local

```bash
cd ~/projetos/ia_trabalhista_robusta && docker-compose up -d db
```

Validar container:

```bash
cd ~/projetos/ia_trabalhista_robusta && docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

O esperado é o container `ia_trabalhista_db` ficar **healthy** na porta `55432`.


---

## Subir a aplicação local

O projeto usa o script:

```bash
cd ~/projetos/ia_trabalhista_robusta && bash scripts/dev_up.sh
```

Esse script sobe o backend em:

- `http://127.0.0.1:8099`

> Se aparecer `Address already in use`, significa que já existe uma instância rodando na porta 8099.

---

## Endpoints operacionais

### Root health

```bash
curl -i http://127.0.0.1:8099/health
```

### Root readiness

```bash
curl -i http://127.0.0.1:8099/ready
```

### API v1 health

```bash
curl -i http://127.0.0.1:8099/api/v1/health
```

### Contrato esperado

- `/health` → status básico da aplicação
- `/ready` → valida aplicação + conexão com banco
- `/api/v1/health` → health versionado da API

---

## Smoke operacional

### Smoke principal

Valida:

- `/health`
- `/ready`
- `/api/v1/health`

```bash
cd ~/projetos/ia_trabalhista_robusta && bash scripts/smoke.sh
```


### Smoke de autenticação

Valida:

- `seed-admin`
- `login`
- `whoami`
- `admin-only`

Exemplo:

```bash
cd ~/projetos/ia_trabalhista_robusta && \
ADMIN_SEED_TOKEN="SEU_TOKEN" \
bash scripts/smoke_auth.sh
```

> Sem `ALLOW_SEED_ADMIN=true` e sem `ADMIN_SEED_TOKEN` válido, o `seed-admin` deve retornar erro. Isso é esperado em ambiente seguro.

---

## Seed admin (break-glass)

O endpoint `/api/v1/auth/seed-admin` é um mecanismo de bootstrap e está protegido por configuração.

Condições para funcionar:

- `ALLOW_SEED_ADMIN=true`
- `ADMIN_SEED_TOKEN` configurado corretamente

Se essas condições não forem atendidas, o endpoint não deve ser usado em operação normal.

### Diretriz

`seed-admin` é **break-glass**, não fluxo padrão de produto.

---

## Fluxo principal do MVP

1. autenticar usuário
2. criar caso
3. consultar caso
4. gerar análise
5. obter resumo/decisão executiva
6. gerar relatório HTML
7. gerar PDF executivo
8. acompanhar health/ready/smoke
9. operar tenant/plano/admin

---

## Diretriz arquitetural permanente

Embora o nome atual seja **IA Trabalhista Robusta**, o sistema não deve evoluir de forma presa apenas ao trabalhista.

A regra de evolução do projeto é:

- manter o nome atual por enquanto
- evitar reestruturação total agora
- desenvolver com visão modular
- separar núcleo genérico de regras por domínio jurídico
- reaproveitar motores de análise
- adaptar relatórios e fluxos por área

### Pergunta obrigatória para novas features

**isso está sendo feito de modo reaproveitável para futura plataforma jurídica multicausa?**

Se a resposta for não, ajustar antes.

---

## O que o escritório compra

Hoje o produto pode ser posicionado como:

**um núcleo SaaS jurídico para organizar casos, gerar análise assistida, produzir decisão executiva e emitir relatório/PDF com base operacional por escritório.**

---

## Próximos focos

- elevar relatório/PDF para padrão premium
- consolidar documentação operacional
- fortalecer deploy/release
- expandir narrativa comercial
- preparar estrutura para múltiplas áreas jurídicas

---

## Observações finais

Este projeto já deixou de ser apenas um backend de estudo.
Ele é tratado como **produto real**, com foco em:

- segurança
- auditabilidade
- previsibilidade operacional
- evolução modular
- venda futura como SaaS jurídico

