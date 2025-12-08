from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import Mapped, mapped_column

from bzero.infrastructure.db.base import AuditMixin, Base, SoftDeleteMixin


class TicketModel(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = "tickets"

    ticket_id: Mapped[UUID] = mapped_column(UUID, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("users.user_id"), nullable=False)

    city_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("cities.city_id"), nullable=False)
    city_name: Mapped[str] = mapped_column(String(100), nullable=False)
    city_theme: Mapped[str] = mapped_column(String(100), nullable=False)
    city_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    city_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city_base_cost_points: Mapped[int] = mapped_column(Integer, nullable=False)
    city_base_duration_hours: Mapped[int] = mapped_column(Integer, nullable=False)

    airship_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("airships.airship_id"), nullable=False)
    airship_name: Mapped[str] = mapped_column(String(100), nullable=False)
    airship_description: Mapped[str] = mapped_column(Text, nullable=False)
    airship_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    airship_cost_factor: Mapped[int] = mapped_column(Integer, nullable=False)
    airship_duration_factor: Mapped[int] = mapped_column(Integer, nullable=False)

    ticket_number: Mapped[str] = mapped_column(String(50), nullable=False)
    cost_points: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    departure_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    arrival_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index(
            "idx_tickets_user_status",
            "user_id",
            "status",
            "departure_datetime",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )
