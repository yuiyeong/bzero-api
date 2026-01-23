from unittest.mock import AsyncMock, MagicMock
from zoneinfo import ZoneInfo

import pytest

from bzero.domain.entities.notification import Notification
from bzero.domain.errors import ForbiddenError, NotFoundNotificationError
from bzero.domain.repositories.notification import NotificationRepository
from bzero.domain.services.notification import NotificationService
from bzero.domain.value_objects import Id, NotificationType


@pytest.fixture
def mock_notification_repository():
    return AsyncMock(spec=NotificationRepository)


@pytest.fixture
def notification_service(mock_notification_repository):
    return NotificationService(mock_notification_repository, ZoneInfo("UTC"))


@pytest.mark.asyncio
async def test_create_notification(notification_service, mock_notification_repository):
    user_id = Id()
    notification_type = NotificationType.CHECKOUT_REMINDER
    title = "Test Title"
    message = "Test Message"

    mock_notification = MagicMock(spec=Notification)
    mock_notification_repository.create.return_value = mock_notification

    result = await notification_service.create_notification(user_id, notification_type, title, message)

    assert result == mock_notification
    mock_notification_repository.create.assert_called_once()
    call_args = mock_notification_repository.create.call_args[0][0]
    assert call_args.user_id == user_id
    # Notification entity might not map 'notification_type' property to same arg name if 'Notification.create' does it.
    # checking call_args.type depending on Notification entity structure.
    # Assuming Notification entity actually has 'type' field as defined in schemas/NotificationResponse.
    # But wait, NotificationService calls Notification.create(..., notification_type=notification_type...).
    # Notification.create probably creates an instance with `type` attribute.
    # Let's verify Notification entity first or assume `type` attribute exists.
    assert call_args.type == notification_type
    assert call_args.title == title
    assert call_args.message == message


@pytest.mark.asyncio
async def test_get_my_notifications(notification_service, mock_notification_repository):
    user_id = Id()
    mock_notifications = [MagicMock(spec=Notification)]
    mock_notification_repository.find_all_by_user_id.return_value = (mock_notifications, 1)

    notifications, total = await notification_service.get_my_notifications(user_id)

    assert notifications == mock_notifications
    assert total == 1
    mock_notification_repository.find_all_by_user_id.assert_called_once_with(user_id, 0, 20)


@pytest.mark.asyncio
async def test_get_unread_count(notification_service, mock_notification_repository):
    user_id = Id()
    mock_notification_repository.count_unread_by_user_id.return_value = 5

    count = await notification_service.get_unread_count(user_id)

    assert count == 5
    mock_notification_repository.count_unread_by_user_id.assert_called_once_with(user_id)


@pytest.mark.asyncio
async def test_mark_as_read(notification_service, mock_notification_repository):
    user_id = Id()
    notification_id = Id()
    mock_notification = MagicMock(spec=Notification)
    mock_notification.user_id = user_id
    mock_notification.is_read = False
    mock_notification_repository.find_by_id.return_value = mock_notification
    mock_notification_repository.update.return_value = mock_notification

    result = await notification_service.mark_as_read(notification_id, user_id)

    assert result == mock_notification
    mock_notification.mark_as_read.assert_called_once()
    mock_notification_repository.update.assert_called_once_with(mock_notification)


@pytest.mark.asyncio
async def test_mark_as_read_not_found(notification_service, mock_notification_repository):
    user_id = Id()
    notification_id = Id()
    mock_notification_repository.find_by_id.return_value = None

    with pytest.raises(NotFoundNotificationError):
        await notification_service.mark_as_read(notification_id, user_id)


@pytest.mark.asyncio
async def test_mark_as_read_forbidden(notification_service, mock_notification_repository):
    user_id = Id()
    other_user_id = Id()
    notification_id = Id()
    mock_notification = MagicMock(spec=Notification)
    mock_notification.user_id = other_user_id
    mock_notification_repository.find_by_id.return_value = mock_notification

    with pytest.raises(ForbiddenError):
        await notification_service.mark_as_read(notification_id, user_id)


@pytest.mark.asyncio
async def test_mark_all_as_read(notification_service, mock_notification_repository):
    user_id = Id()
    mock_notification_repository.mark_all_as_read.return_value = 10

    count = await notification_service.mark_all_as_read(user_id)

    assert count == 10
    mock_notification_repository.mark_all_as_read.assert_called_once_with(user_id)
