from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True, kw_only=True)
class Account:
    owner_name: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        owner_name = self.owner_name.strip()
        if not owner_name:
            raise ValueError("Account owner name is required.")

        object.__setattr__(self, "owner_name", owner_name)
