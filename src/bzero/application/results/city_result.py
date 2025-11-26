from dataclasses import dataclass
from datetime import datetime

from bzero.domain.entities import City


@dataclass
class CityResult:
    """UseCase에서 반환하는 City 결과 객체"""

    city_id: str
    name: str
    theme: str
    description: str | None
    image_url: str | None
    is_active: bool
    display_order: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create_from(cls, entity: City) -> "CityResult":
        return cls(
            city_id=entity.city_id.value.hex,
            name=entity.name,
            theme=entity.theme,
            description=entity.description,
            image_url=entity.image_url,
            is_active=entity.is_active,
            display_order=entity.display_order,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
