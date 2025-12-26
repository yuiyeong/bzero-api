"""1:1 대화방 엔티티.

같은 룸에 체류 중인 두 여행자 간의 1:1 대화방을 나타냅니다.
대화 신청, 수락/거절, 메시지 교환의 컨테이너 역할을 합니다.
"""

from dataclasses import dataclass
from datetime import datetime

from bzero.domain.errors import InvalidDMRoomStatusError
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.dm import DMStatus


@dataclass
class DirectMessageRoom:
    """1:1 대화방 엔티티.

    Attributes:
        dm_room_id: 대화방 고유 식별자 (UUID v7)
        guesthouse_id: 대화방이 속한 게스트하우스 ID
        room_id: 대화방이 생성된 룸 ID (같은 룸 검증 기준)
        requester_id: 대화 신청자 ID
        receiver_id: 대화 수신자 ID (수락/거절 권한)
        status: 대화방 상태 (PENDING, ACCEPTED, ACTIVE, REJECTED, ENDED)
        started_at: 대화 시작 시간 (ACCEPTED 상태로 전환 시 기록)
        ended_at: 대화 종료 시간 (ENDED 상태로 전환 시 기록)
        created_at: 생성 일시
        updated_at: 수정 일시 (DB 트리거에서 자동 업데이트)
        deleted_at: 삭제 일시 (soft delete)
    """

    dm_room_id: Id
    guesthouse_id: Id
    room_id: Id
    requester_id: Id
    receiver_id: Id
    status: DMStatus
    started_at: datetime | None
    ended_at: datetime | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    @classmethod
    def create(
        cls,
        guesthouse_id: Id,
        room_id: Id,
        requester_id: Id,
        receiver_id: Id,
        created_at: datetime,
    ) -> "DirectMessageRoom":
        """새 1:1 대화방을 생성합니다 (PENDING 상태).

        Args:
            guesthouse_id: 게스트하우스 ID
            room_id: 룸 ID
            requester_id: 대화 신청자 ID
            receiver_id: 대화 수신자 ID
            created_at: 생성 일시

        Returns:
            새로 생성된 DirectMessageRoom 엔티티 (status: PENDING)
        """
        return cls(
            dm_room_id=Id(),
            guesthouse_id=guesthouse_id,
            room_id=room_id,
            requester_id=requester_id,
            receiver_id=receiver_id,
            status=DMStatus.PENDING,
            started_at=None,
            ended_at=None,
            created_at=created_at,
            updated_at=created_at,
            deleted_at=None,
        )

    def is_participant(self, user_id: Id) -> bool:
        """사용자가 대화 참여자인지 확인합니다.

        Args:
            user_id: 확인할 사용자 ID

        Returns:
            requester 또는 receiver이면 True
        """
        return user_id.value in {self.requester_id.value, self.receiver_id.value}

    def can_accept_or_reject(self, user_id: Id) -> bool:
        """사용자가 대화 수락/거절 권한이 있는지 확인합니다.

        Args:
            user_id: 확인할 사용자 ID

        Returns:
            receiver(수신자)이면 True
        """
        return user_id.value == self.receiver_id.value

    def get_other_user_id(self, user_id: Id) -> Id:
        """상대방 사용자 ID를 반환합니다.

        Args:
            user_id: 현재 사용자 ID

        Returns:
            상대방 사용자 ID

        Raises:
            ValueError: 참여자가 아닌 경우
        """
        if user_id.value == self.requester_id.value:
            return self.receiver_id
        if user_id.value == self.receiver_id.value:
            return self.requester_id
        raise ValueError("User is not a participant of this DM room")

    def accept(self, now: datetime) -> None:
        """대화 신청을 수락합니다 (PENDING → ACCEPTED).

        Args:
            now: 현재 시간

        Raises:
            InvalidDMRoomStatusError: PENDING 상태가 아닌 경우
        """
        if self.status != DMStatus.PENDING:
            raise InvalidDMRoomStatusError
        self.status = DMStatus.ACCEPTED
        self.started_at = now

    def reject(self) -> None:
        """대화 신청을 거절합니다 (PENDING → REJECTED).

        Raises:
            InvalidDMRoomStatusError: PENDING 상태가 아닌 경우
        """
        if self.status != DMStatus.PENDING:
            raise InvalidDMRoomStatusError
        self.status = DMStatus.REJECTED

    def activate(self) -> None:
        """대화방을 활성화합니다 (ACCEPTED → ACTIVE).

        첫 메시지 전송 시 호출됩니다.

        Raises:
            InvalidDMRoomStatusError: ACCEPTED 상태가 아닌 경우
        """
        if self.status != DMStatus.ACCEPTED:
            raise InvalidDMRoomStatusError
        self.status = DMStatus.ACTIVE

    def end(self, now: datetime) -> None:
        """대화를 종료합니다 (→ ENDED).

        체크아웃 시 호출됩니다.

        Args:
            now: 현재 시간
        """
        self.status = DMStatus.ENDED
        self.ended_at = now

    def can_send_message(self) -> bool:
        """메시지 전송이 가능한 상태인지 확인합니다.

        Returns:
            ACCEPTED 또는 ACTIVE 상태이면 True
        """
        return self.status in (DMStatus.ACCEPTED, DMStatus.ACTIVE)

