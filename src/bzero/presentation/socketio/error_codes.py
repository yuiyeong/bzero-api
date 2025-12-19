"""Socket.IO 에러 코드 정의"""
from enum import Enum


class SocketIOErrorCode(str, Enum):
    """Socket.IO 핸들러에서 사용하는 에러 코드"""

    ROOM_ID_MISMATCH = "ROOM_ID_MISMATCH"
    MISSING_CONTENT = "MISSING_CONTENT"
    MISSING_CARD_ID = "MISSING_CARD_ID"
    INTERNAL_ERROR = "INTERNAL_ERROR"
