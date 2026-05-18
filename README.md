# ledger-event-sourcing-api

API backend em Python preparada para evoluir como um projeto de portfólio com FastAPI, DDD, Clean Architecture e Event Sourcing.

O projeto expõe uma API REST para contas, lançamentos, saldos, transferências e extratos.

## Stack

- Python 3.12+
- uv
- FastAPI
- Uvicorn
- SQLAlchemy
- PostgreSQL
- Alembic
- Ruff
- Pytest

## Como executar

Instale as dependências:

```bash
uv sync
```

Configure o banco local, se estiver rodando fora do Docker:

```bash
export DATABASE_URL=postgresql+psycopg://ledger:ledger@localhost:5432/ledger_db
```

Execute as migrations:

```bash
uv run alembic upgrade head
```

Execute a aplicação em modo desenvolvimento:

```bash
uv run uvicorn app.main:app --reload
```

Documentação automática:

```text
http://localhost:8000/docs
```

Acesse:

```text
GET /health
```

Resposta esperada:

```json
{
  "status": "ok"
}
```

## API Endpoints

Health check:

```bash
curl http://localhost:8000/health
```

Criar conta:

```bash
curl -X POST http://localhost:8000/accounts \
  -H "Content-Type: application/json" \
  -d '{"owner_name":"Maria Silva"}'
```

Consultar saldo:

```bash
curl http://localhost:8000/accounts/{account_id}/balance
```

Depositar:

```bash
curl -X POST http://localhost:8000/accounts/{account_id}/deposit \
  -H "Content-Type: application/json" \
  -d '{
    "amount": "100.00",
    "description": "Initial deposit"
  }'
```

Sacar:

```bash
curl -X POST http://localhost:8000/accounts/{account_id}/withdraw \
  -H "Content-Type: application/json" \
  -d '{
    "amount": "50.00",
    "description": "ATM withdraw"
  }'
```

Transferir:

```bash
curl -X POST http://localhost:8000/transfers \
  -H "Content-Type: application/json" \
  -d '{
    "from_account_id": "00000000-0000-0000-0000-000000000001",
    "to_account_id": "00000000-0000-0000-0000-000000000002",
    "amount": "25.00"
  }'
```

Extrato:

```bash
curl http://localhost:8000/accounts/{account_id}/statement
```

## Idempotência

Idempotência garante que a repetição da mesma operação financeira não gere novos lançamentos no ledger. Isso é essencial quando uma requisição é reenviada por timeout, perda de conexão, retry automático, clique duplo ou concorrência entre serviços.

Nos endpoints HTTP, os campos técnicos de idempotência são gerados automaticamente pela API. O cliente envia apenas os dados da operação.

A API gera internamente:

- `transaction_id`
- `timestamp`
- `idempotency_key`

A `idempotency_key` é uma chave assinada com HMAC-SHA256 a partir de `transaction_id`, `account_id` e `timestamp`, usando `IDEMPOTENCY_SECRET`.

Exemplo de depósito:

```bash
curl -X POST http://localhost:8000/accounts/{account_id}/deposit \
  -H "Content-Type: application/json" \
  -d '{
    "amount": "100.00",
    "description": "Initial deposit"
  }'
```

A resposta inclui a `idempotency_key` gerada para auditoria. Nas camadas internas, a regra de idempotência continua centralizada na aplicação e protegida pelo repositório.

## Persistência

O sistema possui repositórios PostgreSQL com SQLAlchemy e migrations via Alembic. Os repositórios em memória continuam disponíveis para testes e desenvolvimento local, mas o backend padrão da API é `database`.

O saldo não é persistido como fonte principal. Ele continua sendo calculado a partir dos lançamentos em `ledger_entries`.

Dependências adicionadas:

```bash
uv add sqlalchemy psycopg[binary] alembic
```

Configuração esperada:

```env
DATABASE_URL=postgresql+psycopg://ledger:ledger@localhost:5432/ledger_db
LEDGER_REPOSITORY_BACKEND=database
IDEMPOTENCY_SECRET=change-me-in-production
```

Comandos de Alembic usados nesta etapa:

```bash
alembic init migrations
alembic revision --autogenerate -m "create accounts and ledger entries tables"
alembic upgrade head
```

Para aplicar as migrations:

```bash
uv run alembic upgrade head
```

Para usar os repositórios em memória temporariamente:

```bash
LEDGER_REPOSITORY_BACKEND=in_memory uv run uvicorn app.main:app --reload
```

## Concorrência e consistência financeira

Idempotência evita retries duplicados, mas não resolve sozinha duas operações diferentes tentando consumir o mesmo saldo ao mesmo tempo.

Exemplo de race condition:

- saldo inicial: `100`
- saque A tenta debitar `80`
- saque B tenta debitar `80`
- sem controle transacional, os dois poderiam passar e deixar o saldo negativo

O projeto evita isso com transação de banco e lock pessimista na conta de origem para operações críticas:

- `withdraw`
- `transfer`

No backend PostgreSQL, o repositório usa `SELECT ... FOR UPDATE` ao carregar a conta de origem. O caso de uso calcula o saldo e grava o ledger dentro da mesma Unit of Work. Se uma segunda operação concorrente chegar, ela espera a primeira finalizar e recalcula o saldo a partir do ledger atualizado.

Para rodar os testes de concorrência:

```bash
docker compose up -d postgres
CONCURRENCY_DATABASE_URL=postgresql+psycopg://ledger:ledger@localhost:5432/ledger_db \
  uv run pytest tests/integration/test_concurrency.py
```

Use um banco dedicado para esses testes em ambientes compartilhados, porque eles recriam as tabelas do schema. Sem `CONCURRENCY_DATABASE_URL`, eles são pulados para manter a suíte local simples e não tocar no banco principal por acidente.

## Rodando com Docker

Crie o arquivo `.env` a partir do exemplo:

```bash
cp .env.example .env
```

Suba os serviços:

```bash
docker compose up --build
```

Execute as migrations dentro do container:

```bash
docker compose run --rm api uv run alembic upgrade head
```

Acessos:

- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Adminer: http://localhost:8080

Credenciais Adminer:

- Sistema: PostgreSQL
- Servidor: postgres
- Usuário: ledger
- Senha: ledger
- Banco: ledger_db

Testes via Docker:

```bash
docker compose run --rm api uv run pytest
```

## Qualidade

Execute os testes:

```bash
uv run pytest
```

Execute lint:

```bash
uv run ruff check .
```

Execute formatação:

```bash
uv run ruff format .
```

## Estrutura

```text
app/
  main.py
  domain/
  application/
  infrastructure/
  api/
tests/
```

- `app/main.py`: ponto de entrada da aplicação FastAPI.
- `app/domain`: regras de negócio e modelos de domínio.
- `app/application`: casos de uso e orquestração da aplicação.
- `app/infrastructure`: integrações externas, persistência e detalhes técnicos.
- `app/api`: rotas, schemas e adaptadores HTTP.
- `tests`: testes automatizados.
