from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from zoneinfo import ZoneInfo

import pytest

from bzero.domain.entities import RoomStay
from bzero.domain.errors import (
    ForbiddenRoomForUserError,
    InsufficientBalanceError,
    InvalidAmountError,
    InvalidStayStatusError,
)
from bzero.domain.services.room_stay import CheckoutService, StayExtensionService
from bzero.domain.value_objects import Id, RoomStayStatus, TransactionReason, TransactionReference


@pytest.fixture
def mock_room_stay_repository():
    return AsyncMock()


@pytest.fixture
def mock_user_repository():
    return AsyncMock()


@pytest.fixture
def mock_point_transaction_service():
    service = AsyncMock()
    # spend_by는 기본적으로 성공한다고 가정
    service.spend_by.return_value = None
    return service


@pytest.fixture
def stay_extension_service(mock_room_stay_repository, mock_user_repository, mock_point_transaction_service):
    return StayExtensionService(
        room_stay_repository=mock_room_stay_repository,
        user_repository=mock_user_repository,
        point_transaction_service=mock_point_transaction_service,
    )


@pytest.fixture
def checkout_service(mock_room_stay_repository):
    return CheckoutService(
        room_stay_repository=mock_room_stay_repository,
        timezone=ZoneInfo("Asia/Seoul"),
    )


class TestStayExtensionService:
    async def test_extend_stay_success(
        self, stay_extension_service, mock_room_stay_repository, mock_user_repository, mock_point_transaction_service
    ):
        """체류 연장 성공 테스트"""
        # Given
        room_stay_id = Id()
        user_id = Id()
        initial_checkout_time = datetime.now()

        room_stay = RoomStay(
            room_stay_id=room_stay_id,
            user_id=user_id,
            city_id=Id(),
            guest_house_id=Id(),
            room_id=Id(),
            ticket_id=Id(),
            status=RoomStayStatus.CHECKED_IN,
            check_in_at=datetime.now(),
            scheduled_check_out_at=initial_checkout_time,
            actual_check_out_at=None,
            extension_count=0,
            is_checkout_reminder_sent=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        user = MagicMock()
        user.user_id = user_id

        mock_room_stay_repository.find_by_room_stay_id.return_value = room_stay
        mock_user_repository.find_by_user_id.return_value = user
        mock_room_stay_repository.update.return_value = room_stay

        # When
        result = await stay_extension_service.extend_stay(room_stay_id, user_id)

        # Then
        assert result.extension_count == 1
        assert result.scheduled_check_out_at > initial_checkout_time
        assert result.is_checkout_reminder_sent is False

        mock_point_transaction_service.spend_by.assert_called_once_with(
            user=user,
            amount=300,
            reason=TransactionReason.EXTENSION,
            reference_type=TransactionReference.ROOM_STAYS,
            reference_id=room_stay_id,
            description=f"Stay extension for Room {room_stay.room_id}",
        )
        mock_room_stay_repository.update.assert_called_once()

    async def test_extend_stay_raises_error_when_invalid_status(
        self, stay_extension_service, mock_room_stay_repository
    ):
        """체크아웃 상태에서는 연장 불가"""
        # Given
        room_stay_id = Id()
        user_id = Id()
        room_stay = MagicMock(status=RoomStayStatus.CHECKED_OUT, user_id=user_id)
        mock_room_stay_repository.find_by_room_stay_id.return_value = room_stay

        # When, Then
        with pytest.raises(InvalidStayStatusError):
            await stay_extension_service.extend_stay(room_stay_id, user_id)

    async def test_extend_stay_raises_error_when_forbidden(self, stay_extension_service, mock_room_stay_repository):
        """다른 사용자의 체류 연장 시도 시 권한 에러"""
        # Given
        room_stay_id = Id()
        user_id = Id()
        other_user_id = Id()
        room_stay = MagicMock(status=RoomStayStatus.CHECKED_IN, user_id=other_user_id)
        mock_room_stay_repository.find_by_room_stay_id.return_value = room_stay

        # When, Then
        with pytest.raises(ForbiddenRoomForUserError):
            await stay_extension_service.extend_stay(room_stay_id, user_id)

    async def test_extend_stay_raises_error_when_insufficient_balance(
        self, stay_extension_service, mock_room_stay_repository, mock_user_repository, mock_point_transaction_service
    ):
        """잔액 부족 시 에러 발생"""
        # Given
        room_stay_id = Id()
        user_id = Id()
        room_stay = MagicMock(status=RoomStayStatus.CHECKED_IN, user_id=user_id)
        user = MagicMock(user_id=user_id)

        mock_room_stay_repository.find_by_room_stay_id.return_value = room_stay
        mock_user_repository.find_by_user_id.return_value = user
        mock_point_transaction_service.spend_by.side_effect = InvalidAmountError

        # When, Then
        with pytest.raises(InsufficientBalanceError):
            await stay_extension_service.extend_stay(room_stay_id, user_id)


class TestCheckoutService:
    async def test_checkout_success(self, checkout_service, mock_room_stay_repository):
        """체크아웃 성공 테스트"""
        # Given
        room_stay_id = Id()
        user_id = Id()
        room_stay = RoomStay(
            room_stay_id=room_stay_id,
            user_id=user_id,
            city_id=Id(),
            guest_house_id=Id(),
            room_id=Id(),
            ticket_id=Id(),
            status=RoomStayStatus.CHECKED_IN,
            check_in_at=datetime.now(),
            scheduled_check_out_at=datetime.now(),
            actual_check_out_at=None,
            extension_count=0,
            is_checkout_reminder_sent=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_room_stay_repository.find_by_room_stay_id.return_value = room_stay
        mock_room_stay_repository.update.return_value = room_stay

        # When
        result = await checkout_service.checkout(room_stay_id, user_id)

        # Then
        assert result.status == RoomStayStatus.CHECKED_OUT
        assert result.actual_check_out_at is not None
        mock_room_stay_repository.update.assert_called_once()

    async def test_checkout_idempotency(self, checkout_service, mock_room_stay_repository):
        """이미 체크아웃 된 경우 멱등성 보장"""
        # Given
        room_stay_id = Id()
        user_id = Id()
        room_stay = MagicMock(status=RoomStayStatus.CHECKED_OUT, user_id=user_id)
        mock_room_stay_repository.find_by_room_stay_id.return_value = room_stay

        # When
        result = await checkout_service.checkout(room_stay_id, user_id)

        # Then
        assert result.status == RoomStayStatus.CHECKED_OUT
        mock_room_stay_repository.update.assert_not_called()
