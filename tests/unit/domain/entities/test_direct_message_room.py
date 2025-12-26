"""DirectMessageRoom 엔티티 단위 테스트"""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from bzero.core.settings import get_settings
from bzero.domain.entities.direct_message_room import DirectMessageRoom
from bzero.domain.errors import InvalidDMRoomStatusError
from bzero.domain.value_objects import DMStatus, Id


class TestDirectMessageRoom:
    """DirectMessageRoom 엔티티 단위 테스트"""

    @pytest.fixture
    def tz(self) -> ZoneInfo:
        """Seoul timezone"""
        return get_settings().timezone

    @pytest.fixture
    def sample_dm_room(self, tz: ZoneInfo) -> DirectMessageRoom:
        """샘플 대화방 (PENDING 상태)"""
        now = datetime.now(tz)
        return DirectMessageRoom.create(
            guesthouse_id=Id(),
            room_id=Id(),
            requester_id=Id(),
            receiver_id=Id(),
            created_at=now,
        )

    def test_create_dm_room(self, tz: ZoneInfo):
        """대화방을 생성할 수 있다"""
        # Given
        now = datetime.now(tz)
        guesthouse_id = Id()
        room_id = Id()
        requester_id = Id()
        receiver_id = Id()

        # When
        dm_room = DirectMessageRoom.create(
            guesthouse_id=guesthouse_id,
            room_id=room_id,
            requester_id=requester_id,
            receiver_id=receiver_id,
            created_at=now,
        )

        # Then
        assert dm_room.dm_room_id is not None
        assert dm_room.guesthouse_id == guesthouse_id
        assert dm_room.room_id == room_id
        assert dm_room.requester_id == requester_id
        assert dm_room.receiver_id == receiver_id
        assert dm_room.status == DMStatus.PENDING
        assert dm_room.started_at is None
        assert dm_room.ended_at is None
        assert dm_room.deleted_at is None

    def test_is_participant_requester(self, sample_dm_room: DirectMessageRoom):
        """requester는 참여자이다"""
        assert sample_dm_room.is_participant(sample_dm_room.requester_id) is True

    def test_is_participant_receiver(self, sample_dm_room: DirectMessageRoom):
        """receiver는 참여자이다"""
        assert sample_dm_room.is_participant(sample_dm_room.receiver_id) is True

    def test_is_participant_other_user(self, sample_dm_room: DirectMessageRoom):
        """다른 사용자는 참여자가 아니다"""
        other_user = Id()
        assert sample_dm_room.is_participant(other_user) is False

    def test_can_accept_or_reject_receiver(self, sample_dm_room: DirectMessageRoom):
        """receiver는 수락/거절 권한이 있다"""
        assert sample_dm_room.can_accept_or_reject(sample_dm_room.receiver_id) is True

    def test_can_accept_or_reject_requester(self, sample_dm_room: DirectMessageRoom):
        """requester는 수락/거절 권한이 없다"""
        assert sample_dm_room.can_accept_or_reject(sample_dm_room.requester_id) is False

    def test_get_other_user_id_from_requester(self, sample_dm_room: DirectMessageRoom):
        """requester의 상대방은 receiver이다"""
        other = sample_dm_room.get_other_user_id(sample_dm_room.requester_id)
        assert other.value == sample_dm_room.receiver_id.value

    def test_get_other_user_id_from_receiver(self, sample_dm_room: DirectMessageRoom):
        """receiver의 상대방은 requester이다"""
        other = sample_dm_room.get_other_user_id(sample_dm_room.receiver_id)
        assert other.value == sample_dm_room.requester_id.value

    def test_get_other_user_id_non_participant_raises(self, sample_dm_room: DirectMessageRoom):
        """참여자가 아닌 사용자로 상대방을 조회하면 에러가 발생한다"""
        other_user = Id()
        with pytest.raises(ValueError, match="not a participant"):
            sample_dm_room.get_other_user_id(other_user)

    # ============ 상태 전이 테스트 ============

    def test_accept_from_pending(self, sample_dm_room: DirectMessageRoom, tz: ZoneInfo):
        """PENDING 상태에서 수락할 수 있다"""
        # Given
        assert sample_dm_room.status == DMStatus.PENDING
        now = datetime.now(tz)

        # When
        sample_dm_room.accept(now)

        # Then
        assert sample_dm_room.status == DMStatus.ACCEPTED
        assert sample_dm_room.started_at == now

    def test_accept_from_non_pending_raises(self, sample_dm_room: DirectMessageRoom, tz: ZoneInfo):
        """PENDING이 아닌 상태에서 수락하면 에러가 발생한다"""
        # Given
        now = datetime.now(tz)
        sample_dm_room.accept(now)  # ACCEPTED로 변경
        assert sample_dm_room.status == DMStatus.ACCEPTED

        # When/Then
        with pytest.raises(InvalidDMRoomStatusError):
            sample_dm_room.accept(now)

    def test_reject_from_pending(self, sample_dm_room: DirectMessageRoom):
        """PENDING 상태에서 거절할 수 있다"""
        # Given
        assert sample_dm_room.status == DMStatus.PENDING

        # When
        sample_dm_room.reject()

        # Then
        assert sample_dm_room.status == DMStatus.REJECTED

    def test_reject_from_non_pending_raises(self, sample_dm_room: DirectMessageRoom, tz: ZoneInfo):
        """PENDING이 아닌 상태에서 거절하면 에러가 발생한다"""
        # Given
        now = datetime.now(tz)
        sample_dm_room.accept(now)  # ACCEPTED로 변경

        # When/Then
        with pytest.raises(InvalidDMRoomStatusError):
            sample_dm_room.reject()

    def test_activate_from_accepted(self, sample_dm_room: DirectMessageRoom, tz: ZoneInfo):
        """ACCEPTED 상태에서 활성화할 수 있다"""
        # Given
        now = datetime.now(tz)
        sample_dm_room.accept(now)
        assert sample_dm_room.status == DMStatus.ACCEPTED

        # When
        sample_dm_room.activate()

        # Then
        assert sample_dm_room.status == DMStatus.ACTIVE

    def test_activate_from_non_accepted_raises(self, sample_dm_room: DirectMessageRoom):
        """ACCEPTED가 아닌 상태에서 활성화하면 에러가 발생한다"""
        # Given
        assert sample_dm_room.status == DMStatus.PENDING

        # When/Then
        with pytest.raises(InvalidDMRoomStatusError):
            sample_dm_room.activate()

    def test_end_dm_room(self, sample_dm_room: DirectMessageRoom, tz: ZoneInfo):
        """대화방을 종료할 수 있다"""
        # Given
        now = datetime.now(tz)
        sample_dm_room.accept(now)
        sample_dm_room.activate()
        assert sample_dm_room.status == DMStatus.ACTIVE

        # When
        sample_dm_room.end(now)

        # Then
        assert sample_dm_room.status == DMStatus.ENDED
        assert sample_dm_room.ended_at == now

    def test_can_send_message_accepted(self, sample_dm_room: DirectMessageRoom, tz: ZoneInfo):
        """ACCEPTED 상태에서 메시지 전송이 가능하다"""
        now = datetime.now(tz)
        sample_dm_room.accept(now)
        assert sample_dm_room.can_send_message() is True

    def test_can_send_message_active(self, sample_dm_room: DirectMessageRoom, tz: ZoneInfo):
        """ACTIVE 상태에서 메시지 전송이 가능하다"""
        now = datetime.now(tz)
        sample_dm_room.accept(now)
        sample_dm_room.activate()
        assert sample_dm_room.can_send_message() is True

    def test_can_send_message_pending(self, sample_dm_room: DirectMessageRoom):
        """PENDING 상태에서 메시지 전송이 불가능하다"""
        assert sample_dm_room.can_send_message() is False

    def test_can_send_message_rejected(self, sample_dm_room: DirectMessageRoom):
        """REJECTED 상태에서 메시지 전송이 불가능하다"""
        sample_dm_room.reject()
        assert sample_dm_room.can_send_message() is False

