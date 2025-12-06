from dataclasses import dataclass
from datetime import datetime

from bzero.domain.value_objects import AuthProvider, Id


@dataclass
class UserIdentity:
    identity_id: Id
    user_id: Id
    provider: AuthProvider
    provider_user_id: str

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    @classmethod
    def create(
        cls,
        user_id: Id,
        provider: AuthProvider,
        provider_user_id: str,
        created_at: datetime,
        updated_at: datetime,
    ) -> "UserIdentity":
        return cls(
            identity_id=Id(),
            user_id=user_id,
            provider=provider,
            provider_user_id=provider_user_id,
            created_at=created_at,
            updated_at=updated_at,
        )
