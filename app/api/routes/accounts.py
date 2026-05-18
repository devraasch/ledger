from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, status

from app.api.dependencies import (
    get_balance_use_case,
    get_create_account_use_case,
    get_deposit_use_case,
    get_statement_use_case,
    get_withdraw_use_case,
)
from app.api.schemas.account import AccountCreateRequest, AccountResponse
from app.api.schemas.ledger import (
    BalanceResponse,
    LedgerEntryResponse,
    MoneyOperationRequest,
    StatementResponse,
)
from app.application.use_cases.create_account import CreateAccountUseCase
from app.application.use_cases.deposit import DepositUseCase
from app.application.use_cases.get_balance import GetBalanceUseCase
from app.application.use_cases.get_statement import GetStatementUseCase
from app.application.use_cases.withdraw import WithdrawUseCase

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    request: AccountCreateRequest,
    use_case: Annotated[
        CreateAccountUseCase,
        Depends(get_create_account_use_case),
    ],
) -> AccountResponse:
    account = use_case.execute(owner_name=request.owner_name)
    return AccountResponse.model_validate(account)


@router.get("/{account_id}/balance", response_model=BalanceResponse)
def get_balance(
    account_id: UUID,
    use_case: Annotated[GetBalanceUseCase, Depends(get_balance_use_case)],
) -> BalanceResponse:
    balance = use_case.execute(account_id)
    return BalanceResponse.from_money(account_id=account_id, balance=balance)


@router.post("/{account_id}/deposit", response_model=LedgerEntryResponse)
def deposit(
    account_id: UUID,
    request: MoneyOperationRequest,
    use_case: Annotated[DepositUseCase, Depends(get_deposit_use_case)],
) -> LedgerEntryResponse:
    entry = use_case.execute(
        account_id=account_id,
        amount=request.amount,
        description=request.description,
        idempotency_key=None,
        transaction_id=uuid4(),
        timestamp=datetime.now(UTC),
    )
    return LedgerEntryResponse.from_domain(entry)


@router.post("/{account_id}/withdraw", response_model=LedgerEntryResponse)
def withdraw(
    account_id: UUID,
    request: MoneyOperationRequest,
    use_case: Annotated[WithdrawUseCase, Depends(get_withdraw_use_case)],
) -> LedgerEntryResponse:
    entry = use_case.execute(
        account_id=account_id,
        amount=request.amount,
        description=request.description,
        idempotency_key=None,
        transaction_id=uuid4(),
        timestamp=datetime.now(UTC),
    )
    return LedgerEntryResponse.from_domain(entry)


@router.get("/{account_id}/statement", response_model=StatementResponse)
def get_statement(
    account_id: UUID,
    use_case: Annotated[GetStatementUseCase, Depends(get_statement_use_case)],
) -> StatementResponse:
    entries = use_case.execute(account_id)
    return StatementResponse(
        account_id=account_id,
        entries=[LedgerEntryResponse.from_domain(entry) for entry in entries],
    )
