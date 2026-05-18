# ledger-event-sourcing-api

API backend em Python preparada para evoluir como um projeto de portfólio com FastAPI, DDD, Clean Architecture e Event Sourcing.

O projeto expõe uma primeira API REST para contas, lançamentos, saldos, transferências e extratos.

> Nesta etapa, os dados são armazenados apenas em memória.

## Stack

- Python 3.12+
- uv
- FastAPI
- Uvicorn
- Ruff
- Pytest

## Como executar

Instale as dependências:

```bash
uv sync
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
    "description": "Initial deposit",
    "idempotency_key": "deposit-001"
  }'
```

Sacar:

```bash
curl -X POST http://localhost:8000/accounts/{account_id}/withdraw \
  -H "Content-Type: application/json" \
  -d '{
    "amount": "50.00",
    "description": "ATM withdraw",
    "idempotency_key": "withdraw-001"
  }'
```

Transferir:

```bash
curl -X POST http://localhost:8000/transfers \
  -H "Content-Type: application/json" \
  -d '{
    "from_account_id": "00000000-0000-0000-0000-000000000001",
    "to_account_id": "00000000-0000-0000-0000-000000000002",
    "amount": "25.00",
    "idempotency_key": "transfer-001"
  }'
```

Extrato:

```bash
curl http://localhost:8000/accounts/{account_id}/statement
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
