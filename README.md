# IA Trabalhista Robusta

Sistema backend (FastAPI + PostgreSQL) para dar suporte a advogados em demandas trabalhistas,
com foco em **segurança**, **auditoria** e **automação** com IA.

> Projeto real, pensado para uso em escritório de advocacia:
> logs de auditoria, autenticação JWT e base pronta para integrar modelos de IA.

---

## 🧱 Stack

- Python / FastAPI
- PostgreSQL
- SQLAlchemy + Alembic
- JWT (autenticação)
- Middleware de auditoria gravando na tabela `audit_logs`

---

## ⚙️ Configuração de ambiente

Na raiz do projeto:

1. Copie o arquivo de exemplo:

   ```bash
   cp -n .env.example .env

