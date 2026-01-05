from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from bzero.domain.entities import Notification, Room, RoomStay, Ticket
from bzero.domain.errors import (
    ForbiddenRoomForUserError,
    InsufficientBalanceError,
    InvalidAmountError,
    InvalidStayStatusError,
    InvalidTicketStatusError,
    NoActiveStayError,
)
from bzero.domain.repositories.notification import NotificationRepository, NotificationSyncRepository
from bzero.domain.repositories.room import RoomRepository, RoomSyncRepository
from bzero.domain.repositories.room_stay import RoomStayRepository, RoomStaySyncRepository
from bzero.domain.repositories.user import UserRepository
from bzero.domain.services.point_transaction import PointTransactionService
from bzero.domain.value_objects import (
    Id,
    NotificationType,
    RoomStayStatus,
    TransactionReason,
    TransactionReference,
)


class RoomStayService:
    """체류 도메인 서비스 (비동기)."""

    def __init__(self, room_stay_repository: RoomStayRepository):
        self._room_stay_repository = room_stay_repository

    async def get_checked_in_by_user_id(self, user_id: Id) -> RoomStay | None:
        """사용자의 현재 활성 체류를 조회합니다."""
        return await self._room_stay_repository.find_checked_in_by_user_id(user_id)

    async def get_stays_by_user_id_and_room_id(self, user_id: Id, room_id: Id) -> list[RoomStay]:
        stays = await self._room_stay_repository.find_all_checked_in_by_room_id(room_id)
        if all(user_id != stay.user_id for stay in stays):
            raise ForbiddenRoomForUserError
        return stays


class StayExtensionService:
    """체류 연장 서비스 (비동기)."""

    EXTENSION_COST = 300
    EXTENSION_DURATION_HOURS = 24

    def __init__(
        self,
        room_stay_repository: RoomStayRepository,
        user_repository: UserRepository,
        point_transaction_service: PointTransactionService,
    ):
        self._room_stay_repository = room_stay_repository
        self._user_repository = user_repository
        self._point_transaction_service = point_transaction_service

    async def extend_stay(self, room_stay_id: Id, user_id: Id) -> RoomStay:
        """체류를 연장합니다.

        Concurrency:
            - SELECT ... FOR UPDATE를 사용하여 RoomStay를 잠급니다.
            - 배치 워커와의 경합을 방지합니다.

        Args:
            room_stay_id: 체류 ID
            user_id: 요청 사용자 ID

        Returns:
            연장된 체류 엔티티
        """
        # 1. RoomStay 조회 및 잠금
        room_stay = await self._room_stay_repository.find_by_room_stay_id(room_stay_id, with_for_update=True)
        if not room_stay:
            raise NoActiveStayError
        if room_stay.user_id != user_id:
            raise ForbiddenRoomForUserError
        if room_stay.status != RoomStayStatus.CHECKED_IN:
            raise InvalidStayStatusError

        # 2. 사용자 조회
        user = await self._user_repository.find_by_user_id(user_id)
        if not user:
            # 이는 발생하기 어려운 상황이나 안전을 위해 체크
            raise NoActiveStayError  # 적절한 에러 필요

        # 3. 포인트 차감 (포인트 부족 시 내부에서 에러 발생)
        # 3. 포인트 차감 (포인트 부족 시 내부에서 에러 발생)
        # PointTransactionService.spend_by는 트랜잭션 내에서 실행되어야 함
        try:
            await self._point_transaction_service.spend_by(
                user=user,
                amount=self.EXTENSION_COST,
                reason=TransactionReason.EXTENSION,
                reference_type=TransactionReference.ROOM_STAYS,
                reference_id=room_stay.room_stay_id,
                description=f"Stay extension for Room {room_stay.room_id}",
            )
        except InvalidAmountError as e:
            raise InsufficientBalanceError from e

        # 4. 체류 정보 업데이트
        room_stay.scheduled_check_out_at += timedelta(hours=self.EXTENSION_DURATION_HOURS)
        room_stay.extension_count += 1
        room_stay.is_checkout_reminder_sent = False  # 알림 상태 초기화

        return await self._room_stay_repository.update(room_stay)


class CheckoutService:
    """체크아웃 서비스 (비동기 - 사용자/API용)."""

    def __init__(
        self,
        room_stay_repository: RoomStayRepository,
        room_repository: RoomRepository,
        timezone: ZoneInfo,
    ):
        self._room_stay_repository = room_stay_repository
        self._room_repository = room_repository
        self._timezone = timezone

    async def checkout(self, room_stay_id: Id, user_id: Id) -> RoomStay:
        """사용자가 직접 체크아웃을 수행합니다.

        Args:
            room_stay_id: 체류 ID
            user_id: 사용자 ID
        """
        # 1. RoomStay 조회 및 잠금
        room_stay = await self._room_stay_repository.find_by_room_stay_id(room_stay_id, with_for_update=True)
        if not room_stay:
            raise NoActiveStayError
        if room_stay.user_id != user_id:
            raise ForbiddenRoomForUserError

        # 멱등성: 이미 체크아웃 된 경우 성공으로 간주하고 그대로 반환
        if room_stay.status == RoomStayStatus.CHECKED_OUT:
            return room_stay

        # 2. 체크아웃 처리
        now = datetime.now(self._timezone)
        room_stay.status = RoomStayStatus.CHECKED_OUT
        room_stay.actual_check_out_at = now

        # 3. 방 인원 감소 (Atomic)
        await self._room_repository.decrease_capacity(room_stay.room_id)

        # TODO: 마지막 사용자 체크아웃 시 방 정리 로직 (Issue #55) - 추후 구현 필요 시 추가

        return await self._room_stay_repository.update(room_stay)


class NotificationService:
    """알림 서비스 (비동기)."""

    def __init__(self, notification_repository: NotificationRepository):
        self._notification_repository = notification_repository

    async def create_checkout_reminder(self, user_id: Id, message: str) -> Notification:
        return await self._notification_repository.create(
            Notification.create(
                user_id=user_id,
                notification_type=NotificationType.CHECKOUT_REMINDER,
                title="체크아웃 알림",
                message=message,
            )
        )

    async def get_user_notifications(self, user_id: Id, limit: int = 20) -> list[Notification]:
        return await self._notification_repository.find_by_user_id(user_id, limit)


class RoomStaySyncService:
    """체류 도메인 서비스 (동기 - 워커용)."""

    ROOM_STAY_DURATION_IN_HOUR = 24

    def __init__(
        self,
        room_stay_sync_repository: RoomStaySyncRepository,
        room_sync_repository: RoomSyncRepository,
        timezone: ZoneInfo,
    ) -> None:
        self._room_stay_repository = room_stay_sync_repository
        self._room_repository = room_sync_repository
        self._timezone = timezone

    def assign_room(self, ticket: Ticket, room: Room) -> RoomStay:
        """티켓으로 방에 체크인합니다."""
        if not ticket.is_completed:
            raise InvalidTicketStatusError

        check_in_at = datetime.now(self._timezone)
        scheduled_check_out_at = check_in_at + timedelta(hours=self.ROOM_STAY_DURATION_IN_HOUR)

        # 새 체류 생성 시 is_checkout_reminder_sent=False는 create메서드 내 기본값
        room_stay = RoomStay.create(
            user_id=ticket.user_id,
            city_id=ticket.city_snapshot.city_id,
            guest_house_id=room.guest_house_id,
            room_id=room.room_id,
            ticket_id=ticket.ticket_id,
            check_in_at=check_in_at,
            scheduled_check_out_at=scheduled_check_out_at,
            created_at=check_in_at,
            updated_at=check_in_at,
        )
        return self._room_stay_repository.create(room_stay)

    def checkout_if_expired(self, room_stay_id: Id) -> bool:
        """만료된 경우 체크아웃을 수행합니다 (배치용).

        Concurrency:
            - 잠금 후 시간을 다시 확인합니다 (Double-Check).

        Returns:
            bool: 체크아웃 수행 여부 (False면 이미 처리되었거나 연장됨)
        """
        # 1. 잠금 모드로 조회
        room_stay = self._room_stay_repository.find_by_room_stay_id(room_stay_id, with_for_update=True)
        if not room_stay:
            return False

        if room_stay.status == RoomStayStatus.CHECKED_OUT:
            return False

        # 2. Double-Check: 여전히 만료 상태인지 확인
        now = datetime.now(self._timezone)
        if room_stay.scheduled_check_out_at > now:
            # 그 사이 연장되었음 -> 스킵
            return False

        # 3. 체크아웃 처리
        room_stay.status = RoomStayStatus.CHECKED_OUT
        room_stay.actual_check_out_at = now

        # 4. 방 인원 감소 (Atomic)
        self._room_repository.decrease_capacity(room_stay.room_id)

        self._room_stay_repository.update(room_stay)
        return True


class NotificationSyncService:
    """알림 서비스 (동기 - 워커용)."""

    def __init__(self, notification_repository: NotificationSyncRepository):
        self._notification_repository = notification_repository

    def create_checkout_reminder(self, user_id: Id, message: str) -> Notification:
        return self._notification_repository.create(
            Notification.create(
                user_id=user_id,
                notification_type=NotificationType.CHECKOUT_REMINDER,
                title="체크아웃 알림",
                message=message,
            )
        )
