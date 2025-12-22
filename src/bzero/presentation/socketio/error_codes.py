"""Socket.IO 에러 코드 정의"""
from enum import Enum


class SocketIOErrorCode(str, Enum):
    """Socket.IO 핸들러에서 사용하는 에러 코드"""

    # 인증 및 인가
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    ROOM_ID_MISMATCH = "ROOM_ID_MISMATCH"

    # 요청 데이터
    MISSING_CONTENT = "MISSING_CONTENT"
    MISSING_CARD_ID = "MISSING_CARD_ID"
    INVALID_PARAMETER = "INVALID_PARAMETER"

    # 리소스
    NOT_FOUND = "NOT_FOUND"

    # 제한 및 서버 에러
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
