from dataclasses import dataclass
from datetime import datetime

from bzero.domain.entities import User


@dataclass
class UserResult:
    """UseCase에서 반환하는 User 결과 객체"""

    user_id: str
    email: str
    nickname: str | None
    profile_emoji: str | None
    current_points: int
    created_at: datetime
    updated_at: datetime

    @property
    def is_profile_complete(self) -> bool:
        """프로필 완료 여부: nickname과 profile_emoji가 모두 있어야 완료"""
        return self.nickname is not None and self.profile_emoji is not None

    @classmethod
    def create_from(cls, entity: User) -> "UserResult":
        return cls(
            user_id=entity.user_id.value.hex,
            email=entity.email.value,
            nickname=entity.nickname.value if entity.nickname else None,
            profile_emoji=entity.profile.value if entity.profile else None,
            current_points=entity.current_points.value,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
