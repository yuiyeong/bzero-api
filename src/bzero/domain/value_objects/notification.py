from enum import Enum


class NotificationType(str, Enum):
    """알림 유형."""

    CHECKOUT_REMINDER = "CHECKOUT_REMINDER"
    DM_REQUEST = "DM_REQUEST"
