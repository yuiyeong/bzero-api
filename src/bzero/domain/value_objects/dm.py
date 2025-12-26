"""DM (1:1 대화) 관련 값 객체.

1:1 대화방의 상태(DMStatus)를 정의합니다.
"""

from enum import Enum


class DMStatus(Enum):
    """DM 대화방 상태.

    대화방의 생명주기를 나타내는 상태값입니다.

    상태 전이:
        PENDING → ACCEPTED → ACTIVE → ENDED
                ↘ REJECTED

    Attributes:
        PENDING: 대화 신청 대기 중 (user1이 신청, user2가 아직 응답하지 않음)
        ACCEPTED: 대화 수락됨 (아직 메시지가 없는 상태)
        ACTIVE: 활성 대화 (첫 메시지가 전송된 후)
        REJECTED: 대화 거절됨
        ENDED: 대화 종료 (체크아웃 시)
    """

    PENDING = "pending"
    ACCEPTED = "accepted"
    ACTIVE = "active"
    REJECTED = "rejected"
    ENDED = "ended"
