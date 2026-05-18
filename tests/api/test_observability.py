from collections.abc import Generator

import pytest
from app.api.dependencies import reset_in_memory_repositories
from app.main import app
from app.observability.middleware import REQUEST_ID_HEADER
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient]:
    monkeypatch.setenv("LEDGER_REPOSITORY_BACKEND", "in_memory")
    reset_in_memory_repositories()
    with TestClient(app) as test_client:
        yield test_client
    reset_in_memory_repositories()


def test_request_id_header_is_returned(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER]


def test_request_id_header_is_preserved(client: TestClient) -> None:
    response = client.get("/health", headers={REQUEST_ID_HEADER: "test-request-id"})

    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER] == "test-request-id"


def test_metrics_endpoint_works(client: TestClient) -> None:
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "ledger_http_requests_total" in response.text


def test_financial_metrics_increase_after_deposit(client: TestClient) -> None:
    before = _metric_value(client.get("/metrics").text, "ledger_deposits_total")
    account_response = client.post("/accounts", json={"owner_name": "Maria Silva"})
    account_id = account_response.json()["id"]

    deposit_response = client.post(
        f"/accounts/{account_id}/deposit",
        json={
            "amount": "100.00",
            "description": "Initial deposit",
        },
    )
    metrics_response = client.get("/metrics")

    assert deposit_response.status_code == 200
    assert _metric_value(metrics_response.text, "ledger_deposits_total") == before + 1


def test_structured_logging_does_not_break_requests(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def _metric_value(metrics_text: str, metric_name: str) -> float:
    for line in metrics_text.splitlines():
        if line.startswith(f"{metric_name} "):
            return float(line.split()[-1])

    return 0.0
