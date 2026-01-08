from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from uuid_utils import uuid7

from bzero.application.use_cases.chat_messages import GetMessageHistoryUseCase, SendMessageUseCase
from bzero.domain.entities import ChatMessage, RoomStay
from bzero.domain.services import ChatMessageService, RoomStayService, UserService
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.chat_message import MessageContent, MessageType


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def mock_chat_message_service():
    service = MagicMock(spec=ChatMessageService)
    service.send_message = AsyncMock()
    service.get_messages_by_room = AsyncMock()
    return service


@pytest.fixture
def mock_room_stay_service():
    service = MagicMock(spec=RoomStayService)
    service.get_stays_by_user_id_and_room_id = AsyncMock()
    return service


@pytest.fixture
def mock_user_service():
    return MagicMock(spec=UserService)


class TestSendMessageUseCase:
    @pytest.mark.asyncio
    async def test_execute_success(self, mock_session, mock_chat_message_service, mock_user_service):
        # Given
        use_case = SendMessageUseCase(mock_session, mock_chat_message_service, mock_user_service)
        user_id = uuid7()
        room_id = uuid7()
        content = "Hello, World!"

        expected_message = ChatMessage(
            message_id=Id(),
            room_id=Id(room_id),
            user_id=Id(user_id),
            content=MessageContent(content),
            card_id=None,
            message_type=MessageType.TEXT,
            is_system=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            deleted_at=None,
            expires_at=datetime.now() + timedelta(days=3),
        )
        mock_chat_message_service.send_message.return_value = expected_message

        # When
        result = await use_case.execute(
            room_id=room_id.hex,
            content=content,
            user_id=user_id.hex,
        )

        # Then
        assert result.content == content
        assert result.user_id == user_id.hex
        mock_chat_message_service.send_message.assert_called_once()
        mock_session.commit.assert_called_once()


class TestGetMessageHistoryUseCase:
    @pytest.mark.asyncio
    async def test_execute_success(self, mock_chat_message_service, mock_room_stay_service, mock_user_service):
        # Given
        use_case = GetMessageHistoryUseCase(mock_user_service, mock_chat_message_service, mock_room_stay_service)
        user_id = uuid7()
        room_id = uuid7()
        provider = "google"
        provider_user_id = str(uuid7())

        # Mock user lookup
        mock_user = MagicMock()
        mock_user.user_id = Id(user_id)
        mock_user_service.find_user_by_provider_and_provider_user_id = AsyncMock(return_value=mock_user)

        # RoomStay check
        mock_room_stay_service.get_stays_by_user_id_and_room_id.return_value = [MagicMock(spec=RoomStay)]

        # Messages
        messages = [
            ChatMessage(
                message_id=Id(),
                room_id=Id(room_id),
                user_id=Id(user_id),
                content=MessageContent(f"Message {i}"),
                card_id=None,
                message_type=MessageType.TEXT,
                is_system=False,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                deleted_at=None,
                expires_at=datetime.now() + timedelta(days=3),
            )
            for i in range(3)
        ]
        mock_chat_message_service.get_message_history.return_value = messages

        # When
        results = await use_case.execute(
            provider=provider,
            provider_user_id=provider_user_id,
            room_id=room_id.hex,
        )

        # Then
        assert len(results) == 3
        mock_user_service.find_user_by_provider_and_provider_user_id.assert_called_once()
        mock_room_stay_service.get_stays_by_user_id_and_room_id.assert_called_once()
        mock_chat_message_service.get_message_history.assert_called_once()
