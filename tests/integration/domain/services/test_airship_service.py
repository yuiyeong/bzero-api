"""AirshipService Integration Tests."""

from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from bzero.domain.services.airship import AirshipService
from bzero.infrastructure.db.airship_model import AirshipModel
from bzero.infrastructure.repositories.airship import SqlAlchemyAirshipRepository


@pytest.fixture
def airship_service(test_session: AsyncSession) -> AirshipService:
    """AirshipService fixture를 생성합니다."""
    airship_repository = SqlAlchemyAirshipRepository(test_session)
    return AirshipService(airship_repository)


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
    ]

    test_session.add_all(airships)
    await test_session.flush()

    return airships


class TestAirshipServiceGetAvailableAirships:
    """get_available_airships 메서드 통합 테스트"""

    async def test_get_available_airships_success(
        self,
        airship_service: AirshipService,
        sample_airships: list[AirshipModel],
    ):
        """활성화된 비행선 목록을 조회할 수 있어야 합니다."""
        # When
        airships, total = await airship_service.get_available_airships()

        # Then
        assert len(airships) == 2
        assert total == 2
        assert airships[0].name == "일반 비행선"
        assert airships[1].name == "쾌속 비행선"
        assert all(a.is_active for a in airships)

    async def test_get_available_airships_ordered_by_display_order(
        self,
        airship_service: AirshipService,
        sample_airships: list[AirshipModel],
    ):
        """비행선은 display_order 순으로 정렬되어야 합니다."""
        # When
        airships, _ = await airship_service.get_available_airships()

        # Then
        assert airships[0].display_order == 1
        assert airships[1].display_order == 2

    async def test_get_available_airships_with_pagination(
        self,
        airship_service: AirshipService,
        sample_airships: list[AirshipModel],
    ):
        """pagination 파라미터로 비행선 목록을 조회할 수 있어야 합니다."""
        # When
        airships, total = await airship_service.get_available_airships(offset=0, limit=1)

        # Then
        assert len(airships) == 1
        assert total == 2
        assert airships[0].name == "일반 비행선"

    async def test_get_available_airships_with_offset(
        self,
        airship_service: AirshipService,
        sample_airships: list[AirshipModel],
    ):
        """offset 파라미터로 시작 위치를 지정할 수 있어야 합니다."""
        # When
        airships, total = await airship_service.get_available_airships(offset=1, limit=10)

        # Then
        assert len(airships) == 1
        assert total == 2
        assert airships[0].name == "쾌속 비행선"

    async def test_get_available_airships_filters_inactive(
        self,
        airship_service: AirshipService,
        sample_airships: list[AirshipModel],
    ):
        """비활성화된 비행선은 필터링되어야 합니다."""
        # When
        airships, total = await airship_service.get_available_airships()

        # Then: 활성화된 비행선 2개만 반환 (특급 비행선은 제외)
        assert len(airships) == 2
        assert total == 2
        assert all(a.name != "특급 비행선" for a in airships)

    async def test_get_available_airships_empty(
        self,
        airship_service: AirshipService,
    ):
        """활성화된 비행선이 없으면 빈 리스트를 반환해야 합니다."""
        # When
        airships, total = await airship_service.get_available_airships()

        # Then
        assert airships == []
        assert total == 0

    async def test_get_available_airships_soft_deleted_excluded(
        self,
        airship_service: AirshipService,
        sample_airships: list[AirshipModel],
        test_session: AsyncSession,
    ):
        """Soft delete된 비행선은 조회되지 않아야 합니다."""
        # Given: 활성화된 비행선을 soft delete
        airship_model = sample_airships[0]
        airship_model.deleted_at = datetime.now()
        await test_session.flush()

        # When
        airships, total = await airship_service.get_available_airships()

        # Then: 1개만 조회됨
        assert len(airships) == 1
        assert total == 1
        assert airships[0].name == "쾌속 비행선"
