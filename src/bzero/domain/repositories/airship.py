from abc import ABC, abstractmethod

from bzero.domain.entities import Airship


class AirshipRepository(ABC):
    """비행선 리포지토리 추상 클래스.

    비행선 엔티티의 CRUD 작업을 정의하는 인터페이스입니다.
    Clean Architecture 원칙에 따라 도메인 계층에서 인터페이스를 정의하고,
    인프라 계층에서 구현체를 제공합니다.
    """

    @abstractmethod
    async def create(self, airship: Airship) -> Airship:
        """새로운 비행선을 생성합니다.

        Args:
            airship: 생성할 비행선 엔티티

        Returns:
            생성된 비행선 엔티티 (DB에서 생성된 타임스탬프 포함)
        """

    @abstractmethod
    async def find_all(self, offset: int = 0, limit: int = 100) -> list[Airship]:
        """모든 비행선을 조회합니다 (소프트 삭제된 항목 제외).

        Args:
            offset: 조회 시작 위치 (기본값: 0)
            limit: 최대 조회 개수 (기본값: 100)

        Returns:
            비행선 엔티티 목록
        """

    @abstractmethod
    async def find_all_by_active_state(self, is_active: bool, offset: int = 0, limit: int = 100) -> list[Airship]:
        """활성화 상태에 따라 비행선을 조회합니다.

        Args:
            is_active: 활성화 여부 (True: 활성화된 비행선만, False: 비활성화된 비행선만)
            offset: 조회 시작 위치 (기본값: 0)
            limit: 최대 조회 개수 (기본값: 100)

        Returns:
            조건에 맞는 비행선 엔티티 목록
        """

    @abstractmethod
    async def count_by(self, is_active: bool | None) -> int:
        """조건에 맞는 비행선 개수를 반환합니다.

        Args:
            is_active: 활성화 여부 필터 (None이면 전체 조회)

        Returns:
            조건에 맞는 비행선 개수
        """
