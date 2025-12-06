"""Airship 엔티티 단위 테스트"""

from datetime import datetime

from uuid_utils import uuid7

from bzero.domain.entities.airship import Airship
from bzero.domain.value_objects import Id


class TestAirship:
    """Airship 엔티티 단위 테스트"""

    def test_create_airship(self):
        """비행선을 생성할 수 있다"""
        # Given
        airship_id = Id(uuid7())
        name = "일반 비행선"
        description = "편안하고 여유로운 여행을 원하는 여행자를 위한 비행선"
        image_url = "https://example.com/normal-airship.jpg"
        cost_factor = 1
        duration_factor = 1
        display_order = 1
        is_active = True
        now = datetime.now()

        # When
        airship = Airship(
            airship_id=airship_id,
            name=name,
            description=description,
            image_url=image_url,
            cost_factor=cost_factor,
            duration_factor=duration_factor,
            display_order=display_order,
            is_active=is_active,
            created_at=now,
            updated_at=now,
        )

        # Then
        assert airship.airship_id == airship_id
        assert airship.name == name
        assert airship.description == description
        assert airship.image_url == image_url
        assert airship.cost_factor == cost_factor
        assert airship.duration_factor == duration_factor
        assert airship.display_order == display_order
        assert airship.is_active is True
        assert airship.deleted_at is None

    def test_activate_airship(self):
        """비행선을 활성화할 수 있다"""
        # Given
        airship = Airship(
            airship_id=Id(uuid7()),
            name="쾌속 비행선",
            description="빠른 이동을 원하는 여행자를 위한 비행선",
            image_url=None,
            cost_factor=2,
            duration_factor=1,
            display_order=2,
            is_active=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # When
        airship.activate()

        # Then
        assert airship.is_active is True

    def test_deactivate_airship(self):
        """비행선을 비활성화할 수 있다"""
        # Given
        airship = Airship(
            airship_id=Id(uuid7()),
            name="일반 비행선",
            description="편안하고 여유로운 여행을 원하는 여행자를 위한 비행선",
            image_url=None,
            cost_factor=1,
            duration_factor=1,
            display_order=1,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # When
        airship.deactivate()

        # Then
        assert airship.is_active is False

    def test_create_airship_with_image_url_none(self):
        """image_url이 None인 비행선을 생성할 수 있다"""
        # Given & When
        airship = Airship(
            airship_id=Id(uuid7()),
            name="특급 비행선",
            description="가장 빠른 여행을 원하는 여행자를 위한 비행선",
            image_url=None,
            cost_factor=3,
            duration_factor=1,
            display_order=3,
            is_active=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Then
        assert airship.image_url is None
        assert airship.cost_factor == 3
        assert airship.duration_factor == 1
        assert airship.is_active is False

    def test_create_airship_with_different_factors(self):
        """다양한 비용 및 시간 배율로 비행선을 생성할 수 있다"""
        # Given & When
        airship = Airship(
            airship_id=Id(uuid7()),
            name="초고속 비행선",
            description="최고 속도의 여행",
            image_url="https://example.com/super-fast.jpg",
            cost_factor=5,
            duration_factor=1,
            display_order=4,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Then
        assert airship.cost_factor == 5
        assert airship.duration_factor == 1
