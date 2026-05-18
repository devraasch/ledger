from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends

from app.api.dependencies import get_transfer_use_case
from app.api.schemas.ledger import (
    LedgerEntryResponse,
    TransferRequest,
    TransferResponse,
)
from app.application.use_cases.transfer import TransferUseCase
from app.observability.logging import get_logger
from app.observability.metrics import record_transfer

router = APIRouter(tags=["ledger"])
logger = get_logger()


@router.post("/transfers", response_model=TransferResponse)
def transfer(
    request: TransferRequest,
    use_case: Annotated[TransferUseCase, Depends(get_transfer_use_case)],
) -> TransferResponse:
    transaction_id = uuid4()
    timestamp = datetime.now(UTC)
    debit_entry, credit_entry = use_case.execute(
        from_account_id=request.from_account_id,
        to_account_id=request.to_account_id,
        amount=request.amount,
        idempotency_key=None,
        transaction_id=transaction_id,
        timestamp=timestamp,
    )
    record_transfer()
    logger.info(
        "transfer_completed",
        operation="transfer",
        account_id=str(request.from_account_id),
        transaction_id=str(transaction_id),
        idempotency_key=debit_entry.idempotency_key,
    )
    return TransferResponse(
        debit_entry=LedgerEntryResponse.from_domain(debit_entry),
        credit_entry=LedgerEntryResponse.from_domain(credit_entry),
    )
