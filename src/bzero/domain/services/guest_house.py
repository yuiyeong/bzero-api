from bzero.domain.entities import GuestHouse
from bzero.domain.errors import NotFoundGuestHouseError
from bzero.domain.repositories.guest_house import GuestHouseSyncRepository
from bzero.domain.value_objects import Id


class GuestHouseSyncService:
    """게스트하우스 도메인 서비스 (동기).

    Celery 백그라운드 태스크에서 게스트하우스 관련 비즈니스 로직을 처리합니다.
    """

    def __init__(self, guest_house_sync_repository: GuestHouseSyncRepository):
        """GuestHouseSyncService를 초기화합니다.

        Args:
            guest_house_sync_repository: 게스트하우스 동기 리포지토리
        """
        self._guest_house_repository = guest_house_sync_repository

    def get_guest_house_in_city(self, city_id: Id) -> GuestHouse:
        """도시에서 이용 가능한 게스트하우스를 조회합니다.

        활성화된 게스트하우스 중 하나를 반환합니다.

        Args:
            city_id: 도시 ID

        Returns:
            이용 가능한 게스트하우스 엔티티

        Raises:
            NotFoundGuestHouseError: 이용 가능한 게스트하우스가 없는 경우
        """
        guest_house = self._guest_house_repository.find_available_one_by_city_id(city_id)

        if not guest_house:
            raise NotFoundGuestHouseError

        return guest_house
