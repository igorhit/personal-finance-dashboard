# Personal Finance Dashboard

Aplicação web de análise financeira pessoal construída com FastAPI, PostgreSQL e JavaScript puro.

---

## O que o projeto faz

- Cadastra **transações** (receitas e despesas) com descrição, valor, categoria, data e tipo
- Lista transações com **filtros** por período e categoria
- Exibe um **dashboard** com:
  - Saldo atual (acumulado de todas as transações)
  - Total de receitas e despesas do mês corrente
  - Gráfico de pizza — gastos por categoria no mês
  - Gráfico de linha — evolução de saldo nos últimos 12 meses
- **Deleta** transações individualmente

---

## Tecnologias e por que cada uma

| Tecnologia | Por quê |
|---|---|
| **FastAPI** | Framework Python moderno com validação automática via Pydantic, documentação OpenAPI gerada automaticamente e serving de arquivos estáticos nativo |
| **PostgreSQL** | Banco relacional robusto; permite queries com CTEs e window functions que seriam impossíveis em soluções NoSQL simples |
| **psycopg2** | Acesso direto ao banco sem ORM — as queries de relatório usam CTEs e funções de janela que seriam obscurecidas por um ORM |
| **Docker Compose** | Garante que qualquer pessoa reproduza o ambiente com um único comando, sem instalar Postgres localmente |
| **Chart.js** | Biblioteca de gráficos madura, leve e fácil de integrar via CDN — sem build step necessário |
| **HTML/CSS/JS puro** | Sem framework frontend: o projeto permanece simples, sem etapa de build, e demonstra domínio de fundamentos web |

---

## Como rodar

**Pré-requisito:** Docker e Docker Compose instalados.

```bash
git clone <url-do-repo>
cd personal-finance-dashboard
docker-compose up
```

Abra **http://localhost:8000** no navegador.

O dashboard já estará populado com 12 meses de dados fictícios gerados automaticamente no primeiro boot.

---

## Estrutura do projeto

```
personal-finance-dashboard/
├── docker-compose.yml      # Serviços: db (Postgres) + api (FastAPI)
├── Dockerfile
├── requirements.txt
├── .env.example
└── app/
    ├── main.py             # Entrypoint: lifespan, routers, static files
    ├── routers/
    │   ├── transactions.py # CRUD de transações
    │   └── reports.py      # Endpoints de relatório (dashboard)
    ├── db/
    │   ├── connection.py   # Pool de conexão + criação de schema
    │   ├── queries.py      # Carrega e executa os arquivos .sql
    │   ├── seed.py         # Dados fictícios para o primeiro boot
    │   └── sql/            # Queries SQL puras (CTEs, window functions)
    │       ├── schema.sql
    │       ├── get_summary.sql
    │       ├── get_expenses_by_category.sql
    │       ├── get_monthly_balance_evolution.sql
    │       └── ...
    └── static/
        ├── index.html
        ├── style.css
        └── app.js
```

---

## API

A documentação interativa está disponível em **http://localhost:8000/docs** (Swagger UI gerado pelo FastAPI).

Endpoints principais:

| Método | Path | Descrição |
|---|---|---|
| `POST` | `/api/transactions/` | Cria transação |
| `GET` | `/api/transactions/` | Lista transações (filtros opcionais) |
| `DELETE` | `/api/transactions/{id}` | Remove transação |
| `GET` | `/api/reports/summary` | Saldo + totais do mês |
| `GET` | `/api/reports/expenses-by-category` | Breakdown por categoria |
| `GET` | `/api/reports/balance-evolution` | Evolução mensal (N meses) |

---

## Decisões técnicas

### SQL explícito em vez de ORM

As queries de relatório usam CTEs e window functions (`SUM(...) OVER`). Um ORM como SQLAlchemy geraria múltiplos round-trips ou exigiria SQL raw de qualquer forma. Escrever SQL diretamente é mais legível, mais rápido e mais fácil de auditar — e por estarem isoladas em `app/db/sql/`, cada query pode ser lida como um arquivo `.sql` puro, sem precisar navegar por código Python.

### Seed automático

A variável `SEED_DB=true` (definida no `docker-compose.yml`) faz o servidor inserir 12 meses de dados fictícios no primeiro boot, somente se o banco estiver vazio. O recrutador vê o dashboard populado imediatamente sem nenhum passo extra.

### Sem build step no frontend

O frontend consome a API via `fetch()` e importa Chart.js via CDN. Não há Webpack, Vite ou TypeScript — a intenção é manter o projeto reproduzível com apenas Docker, sem Node.js na máquina do avaliador.
