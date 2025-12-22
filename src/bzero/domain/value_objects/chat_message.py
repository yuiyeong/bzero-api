from dataclasses import dataclass
from enum import Enum

from bzero.domain.errors import InvalidMessageContentError


class MessageType(str, Enum):
    """메시지 타입"""

    TEXT = "text"
    CARD_SHARED = "card_shared"
    SYSTEM = "system"


@dataclass(frozen=True)
class MessageContent:
    """메시지 내용 값 객체 (최대 300자)"""

    MAX_LENGTH = 300

    value: str

    def __post_init__(self):
        if len(self.value) == 0 or len(self.value) > self.MAX_LENGTH:
            raise InvalidMessageContentError


class SystemMessage:
    """시스템 메시지 템플릿"""

    USER_JOINED = "사용자가 입장했습니다."
    USER_LEFT = "사용자가 퇴장했습니다."
