"""CityRepository Integration Tests."""

from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from bzero.domain.value_objects import Id
from bzero.infrastructure.db.city_model import CityModel
from bzero.infrastructure.repositories.city import SqlAlchemyCityRepository


@pytest.fixture
def city_repository(test_session: AsyncSession) -> SqlAlchemyCityRepository:
    """CityRepository fixture를 생성합니다."""
    return SqlAlchemyCityRepository(test_session)


@pytest.fixture
async def sample_cities(test_session: AsyncSession) -> list[CityModel]:
    """테스트용 샘플 도시 데이터를 생성합니다."""
    now = datetime.now()
    cities = [
        CityModel(
            city_id=uuid7(),
            name="세렌시아",
            theme="관계의 도시",
            description="사람과의 연결을 회복하는 공간",
            image_url="https://example.com/serencia.jpg",
            is_active=True,
            phase=1,
            display_order=1,
            created_at=now,
            updated_at=now,
        ),
        CityModel(
            city_id=uuid7(),
            name="로렌시아",
            theme="회복의 도시",
            description="지친 마음을 회복하는 공간",
            image_url="https://example.com/lorencia.jpg",
            is_active=True,
            phase=1,
            display_order=2,
            created_at=now,
            updated_at=now,
        ),
        CityModel(
            city_id=uuid7(),
            name="에테리아",
            theme="꿈의 도시",
            description="꿈과 희망을 찾는 공간",
            image_url="https://example.com/etheria.jpg",
            is_active=False,
            phase=2,
            display_order=3,
            created_at=now,
            updated_at=now,
        ),
        CityModel(
            city_id=uuid7(),
            name="드리모스",
            theme="상상의 도시",
            description="상상력을 펼치는 공간",
            image_url="https://example.com/drimos.jpg",
            is_active=False,
            phase=2,
            display_order=4,
            created_at=now,
            updated_at=now,
        ),
    ]

    test_session.add_all(cities)
    await test_session.flush()

    return cities


class TestCityRepositoryFindById:
    """CityRepository.find_by_id() 메서드 테스트."""

    async def test_find_by_id_success(
        self,
        city_repository: SqlAlchemyCityRepository,
        sample_cities: list[CityModel],
    ):
        """존재하는 도시를 ID로 조회할 수 있어야 합니다."""
        # Given: 샘플 도시 데이터
        city_model = sample_cities[0]
        city_id = Id(city_model.city_id)

        # When: 도시 ID로 조회
        city = await city_repository.find_by_id(city_id)

        # Then: 도시가 조회됨
        assert city is not None
        assert city.city_id.value == city_model.city_id
        assert city.name == "세렌시아"
        assert city.theme == "관계의 도시"
        assert city.is_active is True
        assert city.phase == 1

    async def test_find_by_id_not_found(
        self,
        city_repository: SqlAlchemyCityRepository,
    ):
        """존재하지 않는 도시 ID로 조회하면 None을 반환해야 합니다."""
        # Given: 존재하지 않는 도시 ID
        nonexistent_id = Id(uuid7())

        # When: 도시 ID로 조회
        city = await city_repository.find_by_id(nonexistent_id)

        # Then: None이 반환됨
        assert city is None

    async def test_find_by_id_soft_deleted(
        self,
        city_repository: SqlAlchemyCityRepository,
        sample_cities: list[CityModel],
        test_session: AsyncSession,
    ):
        """Soft delete된 도시는 조회되지 않아야 합니다."""
        # Given: 도시를 soft delete
        city_model = sample_cities[0]
        city_model.deleted_at = datetime.now()
        await test_session.flush()

        # When: 도시 ID로 조회
        city = await city_repository.find_by_id(Id(city_model.city_id))

        # Then: None이 반환됨
        assert city is None


class TestCityRepositoryFindActiveCities:
    """CityRepository.find_active_cities() 메서드 테스트."""

    async def test_find_active_cities(
        self,
        city_repository: SqlAlchemyCityRepository,
        sample_cities: list[CityModel],
    ):
        """활성화된 도시 목록을 조회할 수 있어야 합니다."""
        # When: 활성화된 도시 목록 조회
        cities = await city_repository.find_active_cities()

        # Then: 2개의 활성 도시가 조회됨 (세렌시아, 로렌시아)
        assert len(cities) == 2
        assert cities[0].name == "세렌시아"
        assert cities[1].name == "로렌시아"
        assert all(city.is_active for city in cities)

    async def test_find_active_cities_ordered_by_display_order(
        self,
        city_repository: SqlAlchemyCityRepository,
        sample_cities: list[CityModel],
    ):
        """활성화된 도시는 display_order 순으로 정렬되어야 합니다."""
        # When: 활성화된 도시 목록 조회
        cities = await city_repository.find_active_cities()

        # Then: display_order 순으로 정렬됨
        assert cities[0].display_order == 1
        assert cities[1].display_order == 2

    async def test_find_active_cities_empty(
        self,
        city_repository: SqlAlchemyCityRepository,
    ):
        """활성화된 도시가 없으면 빈 리스트를 반환해야 합니다."""
        # When: 활성화된 도시 목록 조회 (샘플 데이터 없음)
        cities = await city_repository.find_active_cities()

        # Then: 빈 리스트 반환
        assert cities == []


class TestCityRepositoryFindCitiesByPhase:
    """CityRepository.find_cities_by_phase() 메서드 테스트."""

    async def test_find_cities_by_phase_1(
        self,
        city_repository: SqlAlchemyCityRepository,
        sample_cities: list[CityModel],
    ):
        """Phase 1 도시 목록을 조회할 수 있어야 합니다."""
        # When: Phase 1 도시 조회
        cities = await city_repository.find_cities_by_phase(1)

        # Then: 2개의 Phase 1 도시가 조회됨
        assert len(cities) == 2
        assert all(city.phase == 1 for city in cities)
        assert cities[0].name == "세렌시아"
        assert cities[1].name == "로렌시아"

    async def test_find_cities_by_phase_2(
        self,
        city_repository: SqlAlchemyCityRepository,
        sample_cities: list[CityModel],
    ):
        """Phase 2 도시 목록을 조회할 수 있어야 합니다."""
        # When: Phase 2 도시 조회
        cities = await city_repository.find_cities_by_phase(2)

        # Then: 2개의 Phase 2 도시가 조회됨
        assert len(cities) == 2
        assert all(city.phase == 2 for city in cities)
        assert cities[0].name == "에테리아"
        assert cities[1].name == "드리모스"

    async def test_find_cities_by_phase_ordered_by_display_order(
        self,
        city_repository: SqlAlchemyCityRepository,
        sample_cities: list[CityModel],
    ):
        """Phase별 도시는 display_order 순으로 정렬되어야 합니다."""
        # When: Phase 2 도시 조회
        cities = await city_repository.find_cities_by_phase(2)

        # Then: display_order 순으로 정렬됨
        assert cities[0].display_order == 3
        assert cities[1].display_order == 4

    async def test_find_cities_by_phase_empty(
        self,
        city_repository: SqlAlchemyCityRepository,
    ):
        """해당 Phase 도시가 없으면 빈 리스트를 반환해야 합니다."""
        # When: Phase 3 도시 조회 (존재하지 않음)
        cities = await city_repository.find_cities_by_phase(3)

        # Then: 빈 리스트 반환
        assert cities == []
