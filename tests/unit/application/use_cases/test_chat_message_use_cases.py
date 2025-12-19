
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta
from uuid_utils import uuid7

from bzero.application.use_cases.chat_messages import SendMessageUseCase, GetMessageHistoryUseCase
from bzero.domain.services import ChatMessageService, RoomStayService
from bzero.domain.entities import ChatMessage, RoomStay
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.chat_message import MessageContent, MessageType
from bzero.domain.errors import BeZeroError

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

class TestSendMessageUseCase:
    @pytest.mark.asyncio
    async def test_execute_success(self, mock_session, mock_chat_message_service):
        # Given
        use_case = SendMessageUseCase(mock_session, mock_chat_message_service)
        user_id = str(uuid7().hex)
        room_id = str(uuid7().hex)
        content = "Hello, World!"
        
        expected_message = ChatMessage(
            message_id=Id(),
            room_id=Id.from_hex(room_id),
            user_id=Id.from_hex(user_id),
            content=MessageContent(content),
            card_id=None,
            message_type=MessageType.TEXT,
            is_system=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            deleted_at=None,
            expires_at=datetime.now() + timedelta(days=3)
        )
        mock_chat_message_service.send_message.return_value = expected_message

        # When
        result = await use_case.execute(user_id, room_id, content)

        # Then
        assert result.content == content
        assert result.user_id == user_id
        mock_chat_message_service.send_message.assert_called_once()
        mock_session.commit.assert_called_once()

class TestGetMessageHistoryUseCase:
    @pytest.mark.asyncio
    async def test_execute_success(self, mock_chat_message_service, mock_room_stay_service):
        # Given
        use_case = GetMessageHistoryUseCase(mock_chat_message_service, mock_room_stay_service)
        user_id = str(uuid7().hex)
        room_id = str(uuid7().hex)
        
        # RoomStay check
        mock_room_stay_service.get_stays_by_user_id_and_room_id.return_value = [MagicMock(spec=RoomStay)]
        
        # Messages
        messages = [
            ChatMessage(
                message_id=Id(),
                room_id=Id.from_hex(room_id),
                user_id=Id.from_hex(user_id),
                content=MessageContent(f"Message {i}"),
                card_id=None,
                message_type=MessageType.TEXT,
                is_system=False,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                deleted_at=None,
                expires_at=datetime.now() + timedelta(days=3)
            ) for i in range(3)
        ]
        mock_chat_message_service.get_message_history.return_value = messages

        # When
        results = await use_case.execute(user_id, room_id)

        # Then
        assert len(results) == 3
        mock_room_stay_service.get_stays_by_user_id_and_room_id.assert_called_once()
        mock_chat_message_service.get_message_history.assert_called_once()
