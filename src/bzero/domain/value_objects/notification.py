from enum import Enum


class NotificationType(str, Enum):
    """알림 유형."""

    CHECKOUT_REMINDER = "CHECKOUT_REMINDER"
