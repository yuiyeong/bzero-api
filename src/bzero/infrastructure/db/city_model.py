from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from bzero.infrastructure.db.base import AuditMixin, Base, SoftDeleteMixin


class CityModel(Base, AuditMixin, SoftDeleteMixin):
    """도시 ORM 모델"""

    __tablename__ = "cities"

    city_id: Mapped[UUID] = mapped_column(UUID, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    theme: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
