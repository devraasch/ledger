from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_transfer_use_case
from app.api.schemas.ledger import (
    LedgerEntryResponse,
    TransferRequest,
    TransferResponse,
)
from app.application.use_cases.transfer import TransferUseCase

router = APIRouter(tags=["ledger"])


@router.post("/transfers", response_model=TransferResponse)
def transfer(
    request: TransferRequest,
    use_case: Annotated[TransferUseCase, Depends(get_transfer_use_case)],
) -> TransferResponse:
    debit_entry, credit_entry = use_case.execute(
        from_account_id=request.from_account_id,
        to_account_id=request.to_account_id,
        amount=request.amount,
        idempotency_key=request.idempotency_key,
    )
    return TransferResponse(
        debit_entry=LedgerEntryResponse.from_domain(debit_entry),
        credit_entry=LedgerEntryResponse.from_domain(credit_entry),
    )
