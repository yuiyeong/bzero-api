import re
from dataclasses import dataclass, field
from uuid import UUID

from uuid_utils import uuid7

from bzero.domain.errors import InvalidAmountError, InvalidEmailError, InvalidNicknameError, InvalidProfileError


@dataclass(frozen=True)
class Id:
    value: UUID = field(default_factory=uuid7)


@dataclass(frozen=True)
class Email:
    PATTERN = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    value: str

    def __post_init__(self):
        if not re.match(self.PATTERN, self.value):
            raise InvalidEmailError


@dataclass(frozen=True)
class Nickname:
    MIN_LENGTH = 2
    MAX_LENGTH = 20

    value: str

    def __post_init__(self):
        if len(self.value) < self.MIN_LENGTH or len(self.value) > self.MAX_LENGTH:
            raise InvalidNicknameError


@dataclass(frozen=True)
class Profile:
    MIN_LENGTH = 1
    MAX_LENGTH = 10

    value: str

    def __post_init__(self):
        if len(self.value) < self.MIN_LENGTH or len(self.value) > self.MAX_LENGTH:
            raise InvalidProfileError


@dataclass(frozen=True)
class Balance:
    value: int

    def __post_init__(self):
        if self.value < 0:
            raise InvalidAmountError

    def add(self, amount: int) -> "Balance":
        if amount < 0:
            raise InvalidAmountError

        return Balance(self.value + amount)

    def deduct(self, amount: int) -> "Balance":
        if self.value - amount < 0:
            raise InvalidAmountError

        return Balance(self.value - amount)
