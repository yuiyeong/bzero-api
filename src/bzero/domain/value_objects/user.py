import re
from dataclasses import dataclass
from enum import Enum

from bzero.domain.errors import InvalidAmountError, InvalidEmailError, InvalidNicknameError, InvalidProfileError


class AuthProvider(str, Enum):
    """인증 제공자"""

    EMAIL = "email"
    GOOGLE = "google"
    APPLE = "apple"
    KAKAO = "kakao"


@dataclass(frozen=True)
class Email:
    """이메일 값 객체"""

    PATTERN = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    value: str

    def __post_init__(self):
        if not re.match(self.PATTERN, self.value):
            raise InvalidEmailError


@dataclass(frozen=True)
class Nickname:
    """닉네임 값 객체 (2-20자)"""

    MIN_LENGTH = 2
    MAX_LENGTH = 20

    value: str

    def __post_init__(self):
        if len(self.value) < self.MIN_LENGTH or len(self.value) > self.MAX_LENGTH:
            raise InvalidNicknameError


@dataclass(frozen=True)
class Profile:
    """프로필 이모지 값 객체 (1-10자)"""

    MIN_LENGTH = 1
    MAX_LENGTH = 10

    value: str

    def __post_init__(self):
        if len(self.value) < self.MIN_LENGTH or len(self.value) > self.MAX_LENGTH:
            raise InvalidProfileError


@dataclass(frozen=True)
class Balance:
    """포인트 잔액 값 객체 (음수 불가)"""

    value: int

    def __post_init__(self):
        if self.value < 0:
            raise InvalidAmountError

    def add(self, amount: int) -> "Balance":
        """포인트 추가"""
        if amount < 0:
            raise InvalidAmountError

        return Balance(self.value + amount)

    def deduct(self, amount: int) -> "Balance":
        """포인트 차감"""
        if self.value - amount < 0:
            raise InvalidAmountError

        return Balance(self.value - amount)
