from datetime import datetime

import pytest
from uuid_utils import uuid7

from bzero.domain.entities.city import City
from bzero.domain.value_objects import Id


class TestCity:
    """City 엔티티 단위 테스트"""

    def test_create_city(self):
        """도시를 생성할 수 있다"""
        # Given
        city_id = Id(uuid7())
        name = "세렌시아"
        theme = "관계의 도시"
        description = "사람과의 연결을 회복하는 공간"
        image_url = "https://example.com/serencia.jpg"
        is_active = True
        phase = 1
        display_order = 1
        now = datetime.now()

        # When
        city = City(
            city_id=city_id,
            name=name,
            theme=theme,
            description=description,
            image_url=image_url,
            is_active=is_active,
            phase=phase,
            display_order=display_order,
            created_at=now,
            updated_at=now,
        )

        # Then
        assert city.city_id == city_id
        assert city.name == name
        assert city.theme == theme
        assert city.description == description
        assert city.image_url == image_url
        assert city.is_active is True
        assert city.phase == phase
        assert city.display_order == display_order
        assert city.deleted_at is None

    def test_activate_city(self):
        """도시를 활성화할 수 있다"""
        # Given
        city = City(
            city_id=Id(uuid7()),
            name="세렌시아",
            theme="관계의 도시",
            description=None,
            image_url=None,
            is_active=False,
            phase=1,
            display_order=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # When
        city.activate()

        # Then
        assert city.is_active is True

    def test_deactivate_city(self):
        """도시를 비활성화할 수 있다"""
        # Given
        city = City(
            city_id=Id(uuid7()),
            name="세렌시아",
            theme="관계의 도시",
            description=None,
            image_url=None,
            is_active=True,
            phase=1,
            display_order=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # When
        city.deactivate()

        # Then
        assert city.is_active is False

    def test_create_city_with_optional_fields_none(self):
        """description과 image_url이 None인 도시를 생성할 수 있다"""
        # Given & When
        city = City(
            city_id=Id(uuid7()),
            name="로렌시아",
            theme="회복의 도시",
            description=None,
            image_url=None,
            is_active=False,
            phase=2,
            display_order=2,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Then
        assert city.description is None
        assert city.image_url is None
        assert city.is_active is False
