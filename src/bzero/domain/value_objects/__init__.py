"""값 객체 패키지

모든 값 객체를 여기서 import 가능:
    from bzero.domain.value_objects import Id, Email, TransactionType
"""

from bzero.domain.value_objects.chat_message import MessageContent, MessageType
from bzero.domain.value_objects.common import Id
from bzero.domain.value_objects.guesthouse import GuestHouseType
from bzero.domain.value_objects.point_transaction import (
    TransactionReason,
    TransactionReference,
    TransactionStatus,
    TransactionType,
)
from bzero.domain.value_objects.room_stay import RoomStayStatus
from bzero.domain.value_objects.ticket import AirshipSnapshot, CitySnapshot, TicketStatus
from bzero.domain.value_objects.user import AuthProvider, Balance, Email, Nickname, Profile


__all__ = [
    "AirshipSnapshot",
    "AuthProvider",
    "Balance",
    "CitySnapshot",
    "Email",
    "GuestHouseType",
    "Id",
    "MessageContent",
    "MessageType",
    "Nickname",
    "Profile",
    "RoomStayStatus",
    "TicketStatus",
    "TransactionReason",
    "TransactionReference",
    "TransactionStatus",
    "TransactionType",
]
