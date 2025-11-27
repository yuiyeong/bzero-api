"""공통 Result 클래스들"""

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class PaginatedResult(Generic[T]):
    """Pagination이 포함된 목록 조회 결과

    Attributes:
        items: 조회된 항목 목록
        total: 전체 항목 수
        offset: 조회 시작 위치
        limit: 조회한 최대 개수
    """

    items: list[T]
    total: int
    offset: int
    limit: int
