from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError

from app.api.routes import accounts_router, ledger_router
from app.application.exceptions import (
    AccountNotFoundError,
    DuplicateTransactionError,
    InsufficientFundsError,
    InvalidOperationError,
)

app = FastAPI(
    title="Ledger Event Sourcing API",
    version="0.1.0",
)
app.include_router(accounts_router)
app.include_router(ledger_router)


def _error_detail(exc: Exception) -> str:
    return str(exc).rstrip(".")


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(AccountNotFoundError)
def handle_account_not_found(
    _request: Request,
    exc: AccountNotFoundError,
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": _error_detail(exc)})


@app.exception_handler(InsufficientFundsError)
def handle_insufficient_funds(
    _request: Request,
    exc: InsufficientFundsError,
) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": _error_detail(exc)})


@app.exception_handler(DuplicateTransactionError)
def handle_duplicate_transaction(
    _request: Request,
    exc: DuplicateTransactionError,
) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": _error_detail(exc)})


@app.exception_handler(InvalidOperationError)
def handle_invalid_operation(
    _request: Request,
    exc: InvalidOperationError,
) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": _error_detail(exc)})


@app.exception_handler(ValueError)
def handle_value_error(_request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": _error_detail(exc)})


@app.exception_handler(ProgrammingError)
def handle_database_schema_error(
    _request: Request,
    _exc: ProgrammingError,
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": "Database schema is not ready. Run migrations."},
    )


@app.exception_handler(SQLAlchemyError)
def handle_database_error(_request: Request, _exc: SQLAlchemyError) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": "Database operation failed."},
    )
