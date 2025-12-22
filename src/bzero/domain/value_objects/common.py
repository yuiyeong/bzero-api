from dataclasses import dataclass, field
from uuid import UUID

from uuid_utils import uuid7

from bzero.domain.errors import InvalidIdError


@dataclass(frozen=True)
class Id:
    """모든 엔티티에서 공통으로 사용하는 식별자 값 객체 (UUID v7)"""

    value: UUID = field(default_factory=uuid7)

    def __post_init__(self):
        """문자열이 전달된 경우 UUID로 변환합니다."""
        if isinstance(self.value, str):
            try:
                object.__setattr__(self, "value", UUID(self.value))
            except (ValueError, AttributeError) as e:
                raise InvalidIdError from e

    def extract_time(self) -> int:
        return self.value.time

    def to_hex(self) -> str:
        return self.value.hex

    @classmethod
    def from_hex(cls, hex_string: str) -> "Id":
        """UUID hex string으로부터 Id 생성

        Args:
            hex_string: UUID hex 문자열

        Returns:
            Id 인스턴스

        Raises:
            InvalidIdError: 잘못된 UUID 형식일 때
        """
        try:
            return cls(value=UUID(hex=hex_string))
        except (ValueError, AttributeError) as e:
            raise InvalidIdError from e
