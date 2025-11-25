from dataclasses import dataclass, field
from uuid import UUID

from uuid_utils import uuid7


@dataclass(frozen=True)
class Id:
    """모든 엔티티에서 공통으로 사용하는 식별자 값 객체 (UUID v7)"""

    value: UUID = field(default_factory=uuid7)

    @classmethod
    def from_hex(cls, hex_string: str) -> "Id":
        """UUID hex string으로부터 Id 생성"""
        return cls(value=UUID(hex=hex_string))
