from dataclasses import dataclass
from datetime import datetime

from bzero.domain.value_objects import Balance, Email, Id, Nickname, Profile


@dataclass
class User:
    user_id: Id
    email: Email
    password_hash: str
    nickname: Nickname
    profile: Profile
    current_points: Balance

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    def add_points(self, amount: int) -> None:
        self.current_points = self.current_points.add(amount)

    def deduct_points(self, amount: int) -> None:
        self.current_points = self.current_points.deduct(amount)
