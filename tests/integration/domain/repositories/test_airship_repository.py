"""AirshipRepository Integration Tests."""

from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from bzero.domain.entities.airship import Airship
from bzero.domain.value_objects import Id
from bzero.infrastructure.db.airship_model import AirshipModel
from bzero.infrastructure.repositories.airship import SqlAlchemyAirshipRepository


@pytest.fixture
def airship_repository(test_session: AsyncSession) -> SqlAlchemyAirshipRepository:
    """AirshipRepository fixture를 생성합니다."""
    return SqlAlchemyAirshipRepository(test_session)


@pytest.fixture
async def sample_airships(test_session: AsyncSession) -> list[AirshipModel]:
    """테스트용 샘플 비행선 데이터를 생성합니다."""
    now = datetime.now()
    airships = [
        AirshipModel(
            airship_id=uuid7(),
            name="일반 비행선",
            description="편안하고 여유로운 여행을 원하는 여행자를 위한 비행선",
            image_url="https://example.com/normal.jpg",
            cost_factor=1,
            duration_factor=1,
            display_order=1,
            is_active=True,
            created_at=now,
            updated_at=now,
        ),
        AirshipModel(
            airship_id=uuid7(),
            name="쾌속 비행선",
            description="빠른 이동을 원하는 여행자를 위한 비행선",
            image_url="https://example.com/fast.jpg",
            cost_factor=2,
            duration_factor=1,
            display_order=2,
            is_active=True,
            created_at=now,
            updated_at=now,
        ),
        AirshipModel(
            airship_id=uuid7(),
            name="특급 비행선",
            description="가장 빠른 여행을 원하는 여행자를 위한 비행선",
            image_url="https://example.com/super-fast.jpg",
            cost_factor=3,
            duration_factor=1,
            display_order=3,
            is_active=False,
            created_at=now,
            updated_at=now,
        ),
        AirshipModel(
            airship_id=uuid7(),
            name="초고속 비행선",
            description="최고 속도의 여행",
            image_url=None,
            cost_factor=5,
            duration_factor=1,
            display_order=4,
            is_active=False,
            created_at=now,
            updated_at=now,
        ),
    ]

    test_session.add_all(airships)
    await test_session.flush()

    return airships


class TestAirshipRepositoryCreate:
    """AirshipRepository.create() 메서드 테스트."""

    async def test_create_airship_success(
        self,
        airship_repository: SqlAlchemyAirshipRepository,
        test_session: AsyncSession,
    ):
        """새로운 비행선을 생성할 수 있어야 합니다."""
        # Given
        airship = Airship(
            airship_id=Id(uuid7()),
            name="테스트 비행선",
            description="테스트용 비행선",
            image_url="https://example.com/test.jpg",
            cost_factor=1,
            duration_factor=1,
            display_order=1,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # When
        created = await airship_repository.create(airship)

        # Then
        assert created is not None
        assert str(created.airship_id.value) == str(airship.airship_id.value)
        assert created.name == "테스트 비행선"
        assert created.cost_factor == 1
        assert created.is_active is True

    async def test_create_airship_with_image_url_none(
        self,
        airship_repository: SqlAlchemyAirshipRepository,
    ):
        """image_url이 None인 비행선을 생성할 수 있어야 합니다."""
        # Given
        airship = Airship(
            airship_id=Id(uuid7()),
            name="이미지 없는 비행선",
            description="이미지 URL이 없는 비행선",
            image_url=None,
            cost_factor=2,
            duration_factor=1,
            display_order=1,
            is_active=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # When
        created = await airship_repository.create(airship)

        # Then
        assert created.image_url is None
        assert created.name == "이미지 없는 비행선"


class TestAirshipRepositoryFindAll:
    """AirshipRepository.find_all() 메서드 테스트."""

    async def test_find_all_success(
        self,
        airship_repository: SqlAlchemyAirshipRepository,
        sample_airships: list[AirshipModel],
    ):
        """모든 비행선을 조회할 수 있어야 합니다."""
        # When
        airships = await airship_repository.find_all()

        # Then
        assert len(airships) == 4
        assert airships[0].name == "일반 비행선"
        assert airships[1].name == "쾌속 비행선"

    async def test_find_all_ordered_by_display_order(
        self,
        airship_repository: SqlAlchemyAirshipRepository,
        sample_airships: list[AirshipModel],
    ):
        """비행선은 display_order 순으로 정렬되어야 합니다."""
        # When
        airships = await airship_repository.find_all()

        # Then
        assert airships[0].display_order == 1
        assert airships[1].display_order == 2
        assert airships[2].display_order == 3
        assert airships[3].display_order == 4

    async def test_find_all_with_pagination(
        self,
        airship_repository: SqlAlchemyAirshipRepository,
        sample_airships: list[AirshipModel],
    ):
        """pagination 파라미터로 비행선 목록을 조회할 수 있어야 합니다."""
        # When
        airships = await airship_repository.find_all(offset=0, limit=2)

        # Then
        assert len(airships) == 2
        assert airships[0].name == "일반 비행선"
        assert airships[1].name == "쾌속 비행선"

    async def test_find_all_with_offset(
        self,
        airship_repository: SqlAlchemyAirshipRepository,
        sample_airships: list[AirshipModel],
    ):
        """offset 파라미터로 시작 위치를 지정할 수 있어야 합니다."""
        # When
        airships = await airship_repository.find_all(offset=2, limit=10)

        # Then
        assert len(airships) == 2
        assert airships[0].name == "특급 비행선"
        assert airships[1].name == "초고속 비행선"

    async def test_find_all_soft_deleted_excluded(
        self,
        airship_repository: SqlAlchemyAirshipRepository,
        sample_airships: list[AirshipModel],
        test_session: AsyncSession,
    ):
        """Soft delete된 비행선은 조회되지 않아야 합니다."""
        # Given: 비행선을 soft delete
        airship_model = sample_airships[0]
        airship_model.deleted_at = datetime.now()
        await test_session.flush()

        # When
        airships = await airship_repository.find_all()

        # Then: 3개만 조회됨
        assert len(airships) == 3
        assert all(a.name != "일반 비행선" for a in airships)

    async def test_find_all_empty(
        self,
        airship_repository: SqlAlchemyAirshipRepository,
    ):
        """비행선이 없으면 빈 리스트를 반환해야 합니다."""
        # When
        airships = await airship_repository.find_all()

        # Then
        assert airships == []


class TestAirshipRepositoryFindAllByActiveState:
    """AirshipRepository.find_all_by_active_state() 메서드 테스트."""

    async def test_find_all_by_active_state_true(
        self,
        airship_repository: SqlAlchemyAirshipRepository,
        sample_airships: list[AirshipModel],
    ):
        """활성화된 비행선 목록을 조회할 수 있어야 합니다."""
        # When
        airships = await airship_repository.find_all_by_active_state(is_active=True)

        # Then
        assert len(airships) == 2
        assert airships[0].name == "일반 비행선"
        assert airships[1].name == "쾌속 비행선"
        assert all(a.is_active for a in airships)

    async def test_find_all_by_active_state_false(
        self,
        airship_repository: SqlAlchemyAirshipRepository,
        sample_airships: list[AirshipModel],
    ):
        """비활성화된 비행선 목록을 조회할 수 있어야 합니다."""
        # When
        airships = await airship_repository.find_all_by_active_state(is_active=False)

        # Then
        assert len(airships) == 2
        assert airships[0].name == "특급 비행선"
        assert airships[1].name == "초고속 비행선"
        assert all(not a.is_active for a in airships)

    async def test_find_all_by_active_state_ordered_by_display_order(
        self,
        airship_repository: SqlAlchemyAirshipRepository,
        sample_airships: list[AirshipModel],
    ):
        """활성화된 비행선은 display_order 순으로 정렬되어야 합니다."""
        # When
        airships = await airship_repository.find_all_by_active_state(is_active=True)

        # Then
        assert airships[0].display_order == 1
        assert airships[1].display_order == 2

    async def test_find_all_by_active_state_with_pagination(
        self,
        airship_repository: SqlAlchemyAirshipRepository,
        sample_airships: list[AirshipModel],
    ):
        """pagination 파라미터로 활성화된 비행선을 조회할 수 있어야 합니다."""
        # When
        airships = await airship_repository.find_all_by_active_state(is_active=True, offset=0, limit=1)

        # Then
        assert len(airships) == 1
        assert airships[0].name == "일반 비행선"

    async def test_find_all_by_active_state_with_offset(
        self,
        airship_repository: SqlAlchemyAirshipRepository,
        sample_airships: list[AirshipModel],
    ):
        """offset 파라미터로 시작 위치를 지정할 수 있어야 합니다."""
        # When
        airships = await airship_repository.find_all_by_active_state(is_active=True, offset=1, limit=10)

        # Then
        assert len(airships) == 1
        assert airships[0].name == "쾌속 비행선"

    async def test_find_all_by_active_state_soft_deleted_excluded(
        self,
        airship_repository: SqlAlchemyAirshipRepository,
        sample_airships: list[AirshipModel],
        test_session: AsyncSession,
    ):
        """Soft delete된 비행선은 조회되지 않아야 합니다."""
        # Given: 활성화된 비행선을 soft delete
        airship_model = sample_airships[0]
        airship_model.deleted_at = datetime.now()
        await test_session.flush()

        # When
        airships = await airship_repository.find_all_by_active_state(is_active=True)

        # Then: 1개만 조회됨
        assert len(airships) == 1
        assert airships[0].name == "쾌속 비행선"

    async def test_find_all_by_active_state_empty(
        self,
        airship_repository: SqlAlchemyAirshipRepository,
    ):
        """활성화된 비행선이 없으면 빈 리스트를 반환해야 합니다."""
        # When
        airships = await airship_repository.find_all_by_active_state(is_active=True)

        # Then
        assert airships == []


class TestAirshipRepositoryCountBy:
    """AirshipRepository.count_by() 메서드 테스트."""

    async def test_count_by_active_true(
        self,
        airship_repository: SqlAlchemyAirshipRepository,
        sample_airships: list[AirshipModel],
    ):
        """활성화된 비행선의 총 개수를 조회할 수 있어야 합니다."""
        # When
        count = await airship_repository.count_by(is_active=True)

        # Then
        assert count == 2

    async def test_count_by_active_false(
        self,
        airship_repository: SqlAlchemyAirshipRepository,
        sample_airships: list[AirshipModel],
    ):
        """비활성화된 비행선의 총 개수를 조회할 수 있어야 합니다."""
        # When
        count = await airship_repository.count_by(is_active=False)

        # Then
        assert count == 2

    async def test_count_by_active_none(
        self,
        airship_repository: SqlAlchemyAirshipRepository,
        sample_airships: list[AirshipModel],
    ):
        """is_active가 None이면 모든 비행선의 개수를 반환해야 합니다."""
        # When
        count = await airship_repository.count_by(is_active=None)

        # Then
        assert count == 4

    async def test_count_by_soft_deleted_excluded(
        self,
        airship_repository: SqlAlchemyAirshipRepository,
        sample_airships: list[AirshipModel],
        test_session: AsyncSession,
    ):
        """Soft delete된 비행선은 개수에 포함되지 않아야 합니다."""
        # Given: 비행선을 soft delete
        airship_model = sample_airships[0]
        airship_model.deleted_at = datetime.now()
        await test_session.flush()

        # When
        count = await airship_repository.count_by(is_active=True)

        # Then: 1개만 카운트됨
        assert count == 1

    async def test_count_by_empty(
        self,
        airship_repository: SqlAlchemyAirshipRepository,
    ):
        """비행선이 없으면 0을 반환해야 합니다."""
        # When
        count = await airship_repository.count_by(is_active=True)

        # Then
        assert count == 0
