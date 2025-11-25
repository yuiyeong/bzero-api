from dataclasses import dataclass
from datetime import datetime

from bzero.domain.value_objects import Balance, Email, Id, Nickname, Profile


@dataclass
class User:
    user_id: Id
    email: Email
    nickname: Nickname | None
    profile: Profile | None
    current_points: Balance

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
