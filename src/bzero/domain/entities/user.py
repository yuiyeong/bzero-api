from dataclasses import dataclass
from datetime import datetime

from bzero.domain.value_objects import Balance, Email, Id, Nickname, Profile


@dataclass
class User:
    user_id: Id
    email: Email | None
    nickname: Nickname | None
    profile: Profile | None
    current_points: Balance

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    @classmethod
    def create(
        cls,
        email: Email | None,
        created_at: datetime,
        updated_at: datetime,
        nickname: Nickname | None = None,
        profile: Profile | None = None,
    ) -> "User":
        return cls(
            user_id=Id(),
            email=email,
            nickname=nickname,
            profile=profile,
            current_points=Balance(0),
            created_at=created_at,
            updated_at=updated_at,
        )
