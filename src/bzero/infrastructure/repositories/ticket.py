from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bzero.domain.entities import Ticket
from bzero.domain.errors import NotFoundTicketError
from bzero.domain.repositories.ticket import TicketRepository
from bzero.domain.value_objects import AirshipSnapshot, CitySnapshot, Id, TicketStatus
from bzero.infrastructure.db.ticket_model import TicketModel


class SqlAlchemyTicketRepository(TicketRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, ticket: Ticket) -> Ticket:
        model = self._to_model(ticket)

        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)

        return self._to_entity(model)

    async def update(self, ticket: Ticket) -> Ticket:
        stmt = (
            update(TicketModel)
            .where(
                TicketModel.ticket_id == ticket.ticket_id.value,
                TicketModel.deleted_at.is_(None),
            )
            .values(status=ticket.status.value)
            .returning(TicketModel)
        )

        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            raise NotFoundTicketError
        return self._to_entity(model)

    async def find_by_id(self, ticket_id: Id) -> Ticket | None:
        stmt = select(TicketModel).where(
            TicketModel.ticket_id == ticket_id.value,
            TicketModel.deleted_at.is_(None),
        )

        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_all_by_user_id(self, user_id: Id, offset: int = 0, limit: int = 100) -> list[Ticket]:
        stmt = (
            select(TicketModel)
            .where(
                TicketModel.user_id == user_id.value,
                TicketModel.deleted_at.is_(None),
            )
            .offset(offset)
            .limit(limit)
            .order_by(TicketModel.departure_datetime.desc())
        )

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def find_all_by_user_id_and_status(
        self, user_id: Id, status: TicketStatus, offset: int = 0, limit: int = 100
    ) -> list[Ticket]:
        stmt = (
            select(TicketModel)
            .where(
                TicketModel.user_id == user_id.value,
                TicketModel.status == status.value,
                TicketModel.deleted_at.is_(None),
            )
            .offset(offset)
            .limit(limit)
            .order_by(TicketModel.arrival_datetime.desc())
        )

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def count_by(self, user_id: Id | None = None, status: TicketStatus | None = None) -> int:
        stmt = select(func.count()).select_from(TicketModel).where(TicketModel.deleted_at.is_(None))
        if user_id is not None:
            stmt = stmt.where(TicketModel.user_id == user_id.value)
        if status is not None:
            stmt = stmt.where(TicketModel.status == status.value)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    @staticmethod
    def _to_model(entity: Ticket) -> TicketModel:
        return TicketModel(
            ticket_id=entity.ticket_id.value,
            user_id=entity.user_id.value,
            ticket_number=entity.ticket_number,
            cost_points=entity.cost_points,
            status=entity.status.value,
            departure_datetime=entity.departure_datetime,
            arrival_datetime=entity.arrival_datetime,
            # City 스냅샷 펼치기
            city_id=entity.city_snapshot.city_id.value,
            city_name=entity.city_snapshot.name,
            city_theme=entity.city_snapshot.theme,
            city_image_url=entity.city_snapshot.image_url,
            city_description=entity.city_snapshot.description,
            city_base_cost_points=entity.city_snapshot.base_cost_points,
            city_base_duration_hours=entity.city_snapshot.base_duration_hours,
            # Airship 스냅샷 펼치기
            airship_id=entity.airship_snapshot.airship_id.value,
            airship_name=entity.airship_snapshot.name,
            airship_image_url=entity.airship_snapshot.image_url,
            airship_description=entity.airship_snapshot.description,
            airship_cost_factor=entity.airship_snapshot.cost_factor,
            airship_duration_factor=entity.airship_snapshot.duration_factor,
        )

    @staticmethod
    def _to_entity(model) -> Ticket:
        return Ticket(
            ticket_id=Id(model.ticket_id),
            user_id=Id(model.user_id),
            ticket_number=model.ticket_number,
            cost_points=model.cost_points,
            status=TicketStatus(model.status),
            departure_datetime=model.departure_datetime,
            arrival_datetime=model.arrival_datetime,
            # City 스냅샷 조립
            city_snapshot=CitySnapshot(
                city_id=Id(model.city_id),
                name=model.city_name,
                theme=model.city_theme,
                image_url=model.city_image_url,
                description=model.city_description,
                base_cost_points=model.city_base_cost_points,
                base_duration_hours=model.city_base_duration_hours,
            ),
            # Airship 스냅샷 조립
            airship_snapshot=AirshipSnapshot(
                airship_id=Id(model.airship_id),
                name=model.airship_name,
                image_url=model.airship_image_url,
                description=model.airship_description,
                cost_factor=model.airship_cost_factor,
                duration_factor=model.airship_duration_factor,
            ),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
