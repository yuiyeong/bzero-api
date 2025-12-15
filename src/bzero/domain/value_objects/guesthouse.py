from enum import Enum


class GuestHouseType(str, Enum):
    MIXED = "mixed"  # 혼합형: 정해진 시간에 함께하는 이벤트 중심
    QUIET = "quiet"  # 조용한 방: 개인적인 대화와 자기성찰 중심
