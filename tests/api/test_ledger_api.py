from collections.abc import Generator

import pytest
from app.api.dependencies import reset_in_memory_repositories
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient]:
    monkeypatch.setenv("LEDGER_REPOSITORY_BACKEND", "in_memory")
    reset_in_memory_repositories()
    with TestClient(app) as test_client:
        yield test_client
    reset_in_memory_repositories()


def create_account(
    client: TestClient,
    owner_name: str = "Maria Silva",
) -> dict[str, str]:
    response = client.post("/accounts", json={"owner_name": owner_name})

    assert response.status_code == 201
    return response.json()


def deposit(
    client: TestClient,
    account_id: str,
    amount: str = "100.00",
) -> dict[str, str]:
    response = client.post(
        f"/accounts/{account_id}/deposit",
        json={
            "amount": amount,
            "description": "Initial deposit",
        },
    )

    assert response.status_code == 200
    return response.json()


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_account(client: TestClient) -> None:
    response = client.post("/accounts", json={"owner_name": "Maria Silva"})

    assert response.status_code == 201
    data = response.json()
    assert data["id"]
    assert data["owner_name"] == "Maria Silva"
    assert data["created_at"]


def test_get_initial_balance(client: TestClient) -> None:
    account = create_account(client)

    response = client.get(f"/accounts/{account['id']}/balance")

    assert response.status_code == 200
    assert response.json() == {
        "account_id": account["id"],
        "balance": "0",
    }


def test_deposit(client: TestClient) -> None:
    account = create_account(client)

    response = client.post(
        f"/accounts/{account['id']}/deposit",
        json={
            "amount": "100.00",
            "description": "Initial deposit",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"]
    assert data["account_id"] == account["id"]
    assert data["transaction_type"] == "CREDIT"
    assert data["amount"] == "100.00"
    assert data["description"] == "Initial deposit"
    assert data["created_at"]
    assert data["idempotency_key"].startswith("idem_")


def test_withdraw(client: TestClient) -> None:
    account = create_account(client)
    deposit(client, account["id"])

    response = client.post(
        f"/accounts/{account['id']}/withdraw",
        json={
            "amount": "50.00",
            "description": "ATM withdraw",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["transaction_type"] == "DEBIT"
    assert data["amount"] == "50.00"


def test_prevent_withdraw_without_funds(client: TestClient) -> None:
    account = create_account(client)

    response = client.post(
        f"/accounts/{account['id']}/withdraw",
        json={
            "amount": "50.00",
            "description": "ATM withdraw",
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Insufficient funds"}


def test_transfer(client: TestClient) -> None:
    source = create_account(client, "Source Account")
    destination = create_account(client, "Destination Account")
    deposit(client, source["id"])

    response = client.post(
        "/transfers",
        json={
            "from_account_id": source["id"],
            "to_account_id": destination["id"],
            "amount": "25.00",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["debit_entry"]["account_id"] == source["id"]
    assert data["debit_entry"]["transaction_type"] == "DEBIT"
    assert data["debit_entry"]["amount"] == "25.00"
    assert data["credit_entry"]["account_id"] == destination["id"]
    assert data["credit_entry"]["transaction_type"] == "CREDIT"
    assert data["credit_entry"]["amount"] == "25.00"


def test_statement(client: TestClient) -> None:
    account = create_account(client)
    deposit(client, account["id"])
    client.post(
        f"/accounts/{account['id']}/withdraw",
        json={
            "amount": "40.00",
            "description": "ATM withdraw",
        },
    )

    response = client.get(f"/accounts/{account['id']}/statement")

    assert response.status_code == 200
    data = response.json()
    assert data["account_id"] == account["id"]
    assert [entry["transaction_type"] for entry in data["entries"]] == [
        "CREDIT",
        "DEBIT",
    ]


def test_deposit_generates_idempotency_key(client: TestClient) -> None:
    account = create_account(client)

    response = client.post(
        f"/accounts/{account['id']}/deposit",
        json={
            "amount": "100.00",
            "description": "Initial deposit",
        },
    )

    assert response.status_code == 200
    assert response.json()["idempotency_key"].startswith("idem_")

    balance_response = client.get(f"/accounts/{account['id']}/balance")
    assert balance_response.json()["balance"] == "100.00"


def test_technical_idempotency_fields_are_not_accepted(client: TestClient) -> None:
    account = create_account(client)

    response = client.post(
        f"/accounts/{account['id']}/deposit",
        json={
            "amount": "100.00",
            "description": "Initial deposit",
            "idempotency_key": "deposit-001",
        },
    )

    assert response.status_code == 422
