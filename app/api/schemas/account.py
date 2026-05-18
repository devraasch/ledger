from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AccountCreateRequest(BaseModel):
    owner_name: str


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_name: str
    created_at: datetime
