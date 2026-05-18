from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

router = APIRouter(tags=["observability"])

HTTP_REQUESTS_TOTAL = Counter(
    "ledger_http_requests_total",
    "Total HTTP requests.",
    ["method", "path", "status_code"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "ledger_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method", "path"],
)

DEPOSITS_TOTAL = Counter("ledger_deposits_total", "Total approved deposits.")
WITHDRAWALS_TOTAL = Counter("ledger_withdrawals_total", "Total approved withdrawals.")
TRANSFERS_TOTAL = Counter("ledger_transfers_total", "Total approved transfers.")
REJECTED_TRANSACTIONS_TOTAL = Counter(
    "ledger_rejected_transactions_total",
    "Total rejected financial transactions.",
    ["reason"],
)
IDEMPOTENCY_ERRORS_TOTAL = Counter(
    "ledger_idempotency_errors_total",
    "Total idempotency errors.",
)
INSUFFICIENT_FUNDS_TOTAL = Counter(
    "ledger_insufficient_funds_total",
    "Total insufficient funds errors.",
)


@router.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


def record_deposit() -> None:
    DEPOSITS_TOTAL.inc()


def record_withdrawal() -> None:
    WITHDRAWALS_TOTAL.inc()


def record_transfer() -> None:
    TRANSFERS_TOTAL.inc()


def record_rejected_transaction(reason: str) -> None:
    REJECTED_TRANSACTIONS_TOTAL.labels(reason=reason).inc()


def record_idempotency_error() -> None:
    IDEMPOTENCY_ERRORS_TOTAL.inc()
    record_rejected_transaction("idempotency")


def record_insufficient_funds() -> None:
    INSUFFICIENT_FUNDS_TOTAL.inc()
    record_rejected_transaction("insufficient_funds")
