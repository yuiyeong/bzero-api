from dataclasses import dataclass
from typing import ClassVar

from bzero.domain.errors import InvalidDiaryContentError, InvalidDiaryMoodError


@dataclass(frozen=True)
class DiaryContent:
    """일기 내용 값 객체 (최대 500자)"""

    MAX_LENGTH = 500

    value: str

    def __post_init__(self):
        if len(self.value) > self.MAX_LENGTH:
            raise InvalidDiaryContentError


@dataclass(frozen=True)
class DiaryMood:
    """일기 기분 이모지 값 객체"""

    ALLOWED_MOODS: ClassVar[tuple[str, ...]] = ("😊", "😐", "😢", "😠", "🥰")

    value: str

    def __post_init__(self):
        if self.value not in self.ALLOWED_MOODS:
            raise InvalidDiaryMoodError
