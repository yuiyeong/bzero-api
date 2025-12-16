from datetime import datetime

import pytest
from sqlalchemy.orm import Session
from uuid_utils import uuid7

from bzero.domain.errors import NotFoundGuestHouseError
from bzero.domain.services.guest_house import GuestHouseSyncService
from bzero.domain.value_objects import GuestHouseType, Id
from bzero.infrastructure.db.city_model import CityModel
from bzero.infrastructure.db.guest_house_model import GuestHouseModel
from bzero.infrastructure.repositories.guest_house import SqlAlchemyGuestHouseSyncRepository


@pytest.fixture
def guest_house_sync_service(test_sync_session: Session) -> GuestHouseSyncService:
    """GuestHouseSyncService fixture를 생성합니다."""
    guest_house_repository = SqlAlchemyGuestHouseSyncRepository(test_sync_session)
    return GuestHouseSyncService(guest_house_repository)


@pytest.fixture
def sync_sample_city(test_sync_session: Session) -> CityModel:
    """테스트용 샘플 도시 데이터를 생성합니다."""
    now = datetime.now()
    city_model = CityModel(
        city_id=str(uuid7()),
        name="세렌시아",
        theme="관계",
        image_url="https://example.com/serencia.jpg",
        description="노을빛 항구 마을",
        base_cost_points=300,
        base_duration_hours=24,
        display_order=1,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    test_sync_session.add(city_model)
    test_sync_session.flush()
    return city_model


@pytest.fixture
def sync_sample_guest_house(test_sync_session: Session, sync_sample_city: CityModel) -> GuestHouseModel:
    """테스트용 샘플 게스트하우스 데이터를 생성합니다."""
    now = datetime.now()
    guest_house_model = GuestHouseModel(
        guest_house_id=str(uuid7()),
        city_id=sync_sample_city.city_id,
        guest_house_type=GuestHouseType.MIXED.value,
        name="편안한 게스트하우스",
        description="조용하고 편안한 공간",
        image_url="https://example.com/guesthouse1.jpg",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    test_sync_session.add(guest_house_model)
    test_sync_session.flush()
    return guest_house_model


@pytest.fixture
def sync_multiple_guest_houses(test_sync_session: Session, sync_sample_city: CityModel) -> list[GuestHouseModel]:
    """테스트용 여러 게스트하우스 데이터를 생성합니다."""
    now = datetime.now()
    guest_houses = [
        GuestHouseModel(
            guest_house_id=str(uuid7()),
            city_id=sync_sample_city.city_id,
            guest_house_type=GuestHouseType.MIXED.value,
            name="첫 번째 게스트하우스",
            description="첫 번째 공간",
            image_url="https://example.com/guesthouse1.jpg",
            is_active=True,
            created_at=now,
            updated_at=now,
        ),
        GuestHouseModel(
            guest_house_id=str(uuid7()),
            city_id=sync_sample_city.city_id,
            guest_house_type=GuestHouseType.QUIET.value,
            name="두 번째 게스트하우스",
            description="두 번째 공간",
            image_url="https://example.com/guesthouse2.jpg",
            is_active=True,
            created_at=now,
            updated_at=now,
        ),
    ]
    test_sync_session.add_all(guest_houses)
    test_sync_session.flush()
    return guest_houses


class TestGuestHouseSyncServiceGetGuestHouseInCity:
    """get_guest_house_in_city 메서드 통합 테스트"""

    def test_get_guest_house_in_city_success(
        self,
        guest_house_sync_service: GuestHouseSyncService,
        sync_sample_city: CityModel,
        sync_sample_guest_house: GuestHouseModel,
    ):
        """도시 ID로 게스트하우스를 조회할 수 있어야 합니다."""
        # Given
        city_id = Id(str(sync_sample_city.city_id))

        # When
        guest_house = guest_house_sync_service.get_guest_house_in_city(city_id)

        # Then
        assert guest_house is not None
        assert str(guest_house.guest_house_id.value) == str(sync_sample_guest_house.guest_house_id)
        assert str(guest_house.city_id.value) == str(sync_sample_city.city_id)
        assert guest_house.name == "편안한 게스트하우스"
        assert guest_house.guest_house_type == GuestHouseType.MIXED

    def test_get_guest_house_in_city_returns_first_when_multiple(
        self,
        guest_house_sync_service: GuestHouseSyncService,
        sync_sample_city: CityModel,
        sync_multiple_guest_houses: list[GuestHouseModel],
    ):
        """여러 게스트하우스가 있을 때 첫 번째를 반환해야 합니다."""
        # Given
        city_id = Id(str(sync_sample_city.city_id))

        # When
        guest_house = guest_house_sync_service.get_guest_house_in_city(city_id)

        # Then
        assert guest_house is not None
        # 첫 번째 게스트하우스 반환 확인
        assert str(guest_house.city_id.value) == str(sync_sample_city.city_id)

    def test_get_guest_house_in_city_raises_error_when_not_found(
        self,
        guest_house_sync_service: GuestHouseSyncService,
    ):
        """도시에 게스트하우스가 없으면 에러가 발생해야 합니다."""
        # Given
        non_existent_city_id = Id(str(uuid7()))

        # When/Then
        with pytest.raises(NotFoundGuestHouseError):
            guest_house_sync_service.get_guest_house_in_city(non_existent_city_id)

    def test_get_guest_house_in_city_ignores_soft_deleted(
        self,
        guest_house_sync_service: GuestHouseSyncService,
        sync_sample_city: CityModel,
        sync_sample_guest_house: GuestHouseModel,
        test_sync_session: Session,
    ):
        """Soft delete된 게스트하우스는 조회되지 않아야 합니다."""
        # Given: 게스트하우스를 soft delete
        sync_sample_guest_house.deleted_at = datetime.now()
        test_sync_session.flush()

        city_id = Id(str(sync_sample_city.city_id))

        # When/Then
        with pytest.raises(NotFoundGuestHouseError):
            guest_house_sync_service.get_guest_house_in_city(city_id)
