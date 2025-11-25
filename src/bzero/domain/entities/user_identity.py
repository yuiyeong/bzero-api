from dataclasses import dataclass
from datetime import datetime

from bzero.domain.value_objects import AuthProvider, Email, Id


@dataclass
class UserIdentity:
    identity_id: Id
    user_id: Id
    provider: AuthProvider
    provider_user_id: str
    provider_email: Email

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
