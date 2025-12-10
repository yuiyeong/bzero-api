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
    base_cost_points: int
    base_duration_hours: int
    is_active: bool
    display_order: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create_from(cls, entity: City) -> "CityResult":
        return cls(
            city_id=entity.city_id.to_hex(),
            name=entity.name,
            theme=entity.theme,
            description=entity.description,
            image_url=entity.image_url,
            base_cost_points=entity.base_cost_points,
            base_duration_hours=entity.base_duration_hours,
            is_active=entity.is_active,
            display_order=entity.display_order,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
