from enum import Enum


class RoomStayStatus(str, Enum):
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    EXTENDED = "extended"
