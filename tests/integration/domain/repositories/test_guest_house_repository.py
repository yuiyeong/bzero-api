from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from uuid_utils import uuid7

from bzero.domain.entities.guest_house import GuestHouse
from bzero.domain.value_objects import GuestHouseType, Id
from bzero.infrastructure.db.city_model import CityModel
from bzero.infrastructure.db.guest_house_model import GuestHouseModel
from bzero.infrastructure.repositories.guest_house import (
    SqlAlchemyGuestHouseRepository,
    SqlAlchemyGuestHouseSyncRepository,
)


# =============================================================================
# 비동기 리포지토리 테스트
# =============================================================================


@pytest.fixture
def guest_house_repository(test_session: AsyncSession) -> SqlAlchemyGuestHouseRepository:
    """GuestHouseRepository fixture를 생성합니다."""
    return SqlAlchemyGuestHouseRepository(test_session)


@pytest.fixture
async def sample_city(test_session: AsyncSession) -> CityModel:
    """테스트용 샘플 도시 데이터를 생성합니다."""
    now = datetime.now()
    city = CityModel(
        city_id=uuid7(),
        name="세렌시아",
        theme="관계",
        description="노을빛 항구 마을",
        image_url="https://example.com/serentia.jpg",
        base_cost_points=300,
        base_duration_hours=24,
        is_active=True,
        display_order=1,
        created_at=now,
        updated_at=now,
    )
    test_session.add(city)
    await test_session.flush()
    return city


@pytest.fixture
async def sample_guest_houses(
    test_session: AsyncSession,
    sample_city: CityModel,
) -> list[GuestHouseModel]:
    """테스트용 샘플 게스트하우스 데이터를 생성합니다."""
    now = datetime.now()
    guest_houses = [
        GuestHouseModel(
            guest_house_id=uuid7(),
            city_id=sample_city.city_id,
            guest_house_type=GuestHouseType.MIXED.value,
            name="편안한 게스트하우스",
            description="조용하고 편안한 공간",
            image_url="https://example.com/guesthouse1.jpg",
            is_active=True,
            created_at=now,
            updated_at=now,
        ),
        GuestHouseModel(
            guest_house_id=uuid7(),
            city_id=sample_city.city_id,
            guest_house_type=GuestHouseType.MIXED.value,
            name="따뜻한 게스트하우스",
            description="따뜻한 분위기의 공간",
            image_url="https://example.com/guesthouse2.jpg",
            is_active=True,
            created_at=now,
            updated_at=now,
        ),
    ]

    test_session.add_all(guest_houses)
    await test_session.flush()

    return guest_houses


class TestAsyncGuestHouseRepositoryCreate:
    """SqlAlchemyGuestHouseRepository.create() 메서드 테스트."""

    async def test_create_success(
        self,
        guest_house_repository: SqlAlchemyGuestHouseRepository,
        sample_city: CityModel,
    ):
        """게스트하우스를 생성할 수 있어야 합니다."""
        # Given: 새 게스트하우스 엔티티
        now = datetime.now()
        guest_house = GuestHouse.create(
            city_id=Id(str(sample_city.city_id)),
            name="새로운 게스트하우스",
            description="테스트 게스트하우스",
            image_url="https://example.com/new.jpg",
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        # When: 게스트하우스 생성
        created_guest_house = await guest_house_repository.create(guest_house)

        # Then: 게스트하우스가 생성됨
        assert created_guest_house is not None
        assert str(created_guest_house.guest_house_id.value) == str(guest_house.guest_house_id.value)
        assert str(created_guest_house.city_id.value) == str(sample_city.city_id)
        assert created_guest_house.name == "새로운 게스트하우스"
        assert created_guest_house.description == "테스트 게스트하우스"
        assert created_guest_house.guest_house_type == GuestHouseType.MIXED
        assert created_guest_house.is_active is True

    async def test_create_with_nullable_fields(
        self,
        guest_house_repository: SqlAlchemyGuestHouseRepository,
        sample_city: CityModel,
    ):
        """nullable 필드가 None인 게스트하우스를 생성할 수 있어야 합니다."""
        # Given: description과 image_url이 None인 게스트하우스
        now = datetime.now()
        guest_house = GuestHouse.create(
            city_id=Id(str(sample_city.city_id)),
            name="미니멀 게스트하우스",
            description=None,
            image_url=None,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        # When: 게스트하우스 생성
        created_guest_house = await guest_house_repository.create(guest_house)

        # Then: nullable 필드가 None으로 저장됨
        assert created_guest_house.description is None
        assert created_guest_house.image_url is None


class TestAsyncGuestHouseRepositoryFindByGuestHouseId:
    """SqlAlchemyGuestHouseRepository.find_by_guesthouse_id() 메서드 테스트."""

    async def test_find_by_guesthouse_id_success(
        self,
        guest_house_repository: SqlAlchemyGuestHouseRepository,
        sample_guest_houses: list[GuestHouseModel],
    ):
        """존재하는 게스트하우스를 ID로 조회할 수 있어야 합니다."""
        # Given: 샘플 게스트하우스 데이터
        guest_house_model = sample_guest_houses[0]
        guest_house_id = Id(str(guest_house_model.guest_house_id))

        # When: 게스트하우스 ID로 조회
        guest_house = await guest_house_repository.find_by_guesthouse_id(guest_house_id)

        # Then: 게스트하우스가 조회됨
        assert guest_house is not None
        assert str(guest_house.guest_house_id.value) == str(guest_house_model.guest_house_id)
        assert guest_house.name == "편안한 게스트하우스"
        assert guest_house.description == "조용하고 편안한 공간"
        assert guest_house.guest_house_type == GuestHouseType.MIXED
        assert guest_house.is_active is True

    async def test_find_by_guesthouse_id_not_found(
        self,
        guest_house_repository: SqlAlchemyGuestHouseRepository,
    ):
        """존재하지 않는 게스트하우스 ID로 조회하면 None을 반환해야 합니다."""
        # Given: 존재하지 않는 게스트하우스 ID
        nonexistent_id = Id(str(uuid7()))

        # When: 게스트하우스 ID로 조회
        guest_house = await guest_house_repository.find_by_guesthouse_id(nonexistent_id)

        # Then: None이 반환됨
        assert guest_house is None

    async def test_find_by_guesthouse_id_soft_deleted(
        self,
        guest_house_repository: SqlAlchemyGuestHouseRepository,
        sample_guest_houses: list[GuestHouseModel],
        test_session: AsyncSession,
    ):
        """Soft delete된 게스트하우스는 조회되지 않아야 합니다."""
        # Given: 게스트하우스를 soft delete
        guest_house_model = sample_guest_houses[0]
        guest_house_model.deleted_at = datetime.now()
        await test_session.flush()

        # When: 게스트하우스 ID로 조회
        guest_house = await guest_house_repository.find_by_guesthouse_id(Id(str(guest_house_model.guest_house_id)))

        # Then: None이 반환됨
        assert guest_house is None


# =============================================================================
# 동기 리포지토리 테스트
# =============================================================================


@pytest.fixture
def guest_house_sync_repository(test_sync_session: Session) -> SqlAlchemyGuestHouseSyncRepository:
    """GuestHouseSyncRepository fixture를 생성합니다."""
    return SqlAlchemyGuestHouseSyncRepository(test_sync_session)


@pytest.fixture
def sync_sample_city(test_sync_session: Session) -> CityModel:
    """테스트용 샘플 도시 데이터를 생성합니다 (동기)."""
    now = datetime.now()
    city_id = str(uuid7())
    city = CityModel(
        city_id=city_id,
        name="로렌시아",
        theme="회복",
        description="숲 속 오두막",
        image_url="https://example.com/lorencia.jpg",
        base_cost_points=300,
        base_duration_hours=24,
        is_active=True,
        display_order=2,
        created_at=now,
        updated_at=now,
    )
    test_sync_session.add(city)
    test_sync_session.flush()
    return city


@pytest.fixture
def sync_sample_guest_houses(
    test_sync_session: Session,
    sync_sample_city: CityModel,
) -> list[GuestHouseModel]:
    """테스트용 샘플 게스트하우스 데이터를 생성합니다 (동기)."""
    now = datetime.now()
    guest_houses = [
        GuestHouseModel(
            guest_house_id=str(uuid7()),
            city_id=sync_sample_city.city_id,
            guest_house_type=GuestHouseType.MIXED.value,
            name="고요한 게스트하우스",
            description="고요한 숲 속 공간",
            image_url="https://example.com/sync_guesthouse1.jpg",
            is_active=True,
            created_at=now,
            updated_at=now,
        ),
        GuestHouseModel(
            guest_house_id=str(uuid7()),
            city_id=sync_sample_city.city_id,
            guest_house_type=GuestHouseType.MIXED.value,
            name="평화로운 게스트하우스",
            description="평화로운 분위기",
            image_url="https://example.com/sync_guesthouse2.jpg",
            is_active=False,
            created_at=now,
            updated_at=now,
        ),
    ]

    test_sync_session.add_all(guest_houses)
    test_sync_session.flush()

    return guest_houses


class TestSyncGuestHouseRepositoryCreate:
    """SqlAlchemyGuestHouseSyncRepository.create() 메서드 테스트."""

    def test_create_success(
        self,
        guest_house_sync_repository: SqlAlchemyGuestHouseSyncRepository,
        sync_sample_city: CityModel,
    ):
        """게스트하우스를 생성할 수 있어야 합니다 (동기)."""
        # Given: 새 게스트하우스 엔티티
        now = datetime.now()
        guest_house = GuestHouse.create(
            city_id=Id(str(sync_sample_city.city_id)),
            name="동기 게스트하우스",
            description="동기 테스트용",
            image_url="https://example.com/sync_new.jpg",
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        # When: 게스트하우스 생성
        created_guest_house = guest_house_sync_repository.create(guest_house)

        # Then: 게스트하우스가 생성됨
        assert created_guest_house is not None
        assert str(created_guest_house.guest_house_id.value) == str(guest_house.guest_house_id.value)
        assert str(created_guest_house.city_id.value) == str(sync_sample_city.city_id)
        assert created_guest_house.name == "동기 게스트하우스"
        assert created_guest_house.description == "동기 테스트용"
        assert created_guest_house.guest_house_type == GuestHouseType.MIXED
        assert created_guest_house.is_active is True

    def test_create_with_nullable_fields(
        self,
        guest_house_sync_repository: SqlAlchemyGuestHouseSyncRepository,
        sync_sample_city: CityModel,
    ):
        """nullable 필드가 None인 게스트하우스를 생성할 수 있어야 합니다 (동기)."""
        # Given: description과 image_url이 None인 게스트하우스
        now = datetime.now()
        guest_house = GuestHouse.create(
            city_id=Id(str(sync_sample_city.city_id)),
            name="심플 게스트하우스",
            description=None,
            image_url=None,
            is_active=False,
            created_at=now,
            updated_at=now,
        )

        # When: 게스트하우스 생성
        created_guest_house = guest_house_sync_repository.create(guest_house)

        # Then: nullable 필드가 None으로 저장됨
        assert created_guest_house.description is None
        assert created_guest_house.image_url is None
        assert created_guest_house.is_active is False


class TestSyncGuestHouseRepositoryFindByGuestHouseId:
    """SqlAlchemyGuestHouseSyncRepository.find_by_guesthouse_id() 메서드 테스트."""

    def test_find_by_guesthouse_id_success(
        self,
        guest_house_sync_repository: SqlAlchemyGuestHouseSyncRepository,
        sync_sample_guest_houses: list[GuestHouseModel],
    ):
        """존재하는 게스트하우스를 ID로 조회할 수 있어야 합니다 (동기)."""
        # Given: 샘플 게스트하우스 데이터
        guest_house_model = sync_sample_guest_houses[0]
        guest_house_id = Id(str(guest_house_model.guest_house_id))

        # When: 게스트하우스 ID로 조회
        guest_house = guest_house_sync_repository.find_by_guesthouse_id(guest_house_id)

        # Then: 게스트하우스가 조회됨
        assert guest_house is not None
        assert str(guest_house.guest_house_id.value) == str(guest_house_model.guest_house_id)
        assert guest_house.name == "고요한 게스트하우스"
        assert guest_house.description == "고요한 숲 속 공간"
        assert guest_house.guest_house_type == GuestHouseType.MIXED
        assert guest_house.is_active is True

    def test_find_by_guesthouse_id_not_found(
        self,
        guest_house_sync_repository: SqlAlchemyGuestHouseSyncRepository,
    ):
        """존재하지 않는 게스트하우스 ID로 조회하면 None을 반환해야 합니다 (동기)."""
        # Given: 존재하지 않는 게스트하우스 ID
        nonexistent_id = Id(str(uuid7()))

        # When: 게스트하우스 ID로 조회
        guest_house = guest_house_sync_repository.find_by_guesthouse_id(nonexistent_id)

        # Then: None이 반환됨
        assert guest_house is None

    def test_find_by_guesthouse_id_soft_deleted(
        self,
        guest_house_sync_repository: SqlAlchemyGuestHouseSyncRepository,
        sync_sample_guest_houses: list[GuestHouseModel],
        test_sync_session: Session,
    ):
        """Soft delete된 게스트하우스는 조회되지 않아야 합니다 (동기)."""
        # Given: 게스트하우스를 soft delete
        guest_house_model = sync_sample_guest_houses[0]
        guest_house_model.deleted_at = datetime.now()
        test_sync_session.flush()

        # When: 게스트하우스 ID로 조회
        guest_house = guest_house_sync_repository.find_by_guesthouse_id(Id(str(guest_house_model.guest_house_id)))

        # Then: None이 반환됨
        assert guest_house is None
