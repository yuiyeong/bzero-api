import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bzero.domain.entities.diary import Diary
from bzero.domain.repositories.diary import DiaryRepository
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.diary import DiaryContent, DiaryMood
from bzero.infrastructure.db.diary_model import DiaryModel


class SqlAlchemyDiaryRepository(DiaryRepository):
    """SQLAlchemy 기반 일기 리포지토리 구현체"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def find_by_id(self, diary_id: Id) -> Diary | None:
        stmt = select(DiaryModel).where(
            DiaryModel.diary_id == uuid.UUID(diary_id.value),
            DiaryModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_user_and_date(self, user_id: Id, diary_date: date) -> Diary | None:
        stmt = select(DiaryModel).where(
            DiaryModel.user_id == uuid.UUID(user_id.value),
            DiaryModel.diary_date == diary_date,
            DiaryModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_user_id(
        self,
        user_id: Id,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Diary], int]:
        # 전체 개수 조회
        count_stmt = (
            select(func.count())
            .select_from(DiaryModel)
            .where(
                DiaryModel.user_id == uuid.UUID(user_id.value),
                DiaryModel.deleted_at.is_(None),
            )
        )
        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar_one()

        # 일기 목록 조회 (최신순 정렬)
        stmt = (
            select(DiaryModel)
            .where(
                DiaryModel.user_id == uuid.UUID(user_id.value),
                DiaryModel.deleted_at.is_(None),
            )
            .order_by(DiaryModel.diary_date.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        diaries = [self._to_entity(model) for model in models]

        return diaries, total

    async def count_by_user_id(self, user_id: Id) -> int:
        stmt = (
            select(func.count())
            .select_from(DiaryModel)
            .where(
                DiaryModel.user_id == uuid.UUID(user_id.value),
                DiaryModel.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def save(self, diary: Diary) -> Diary:
        model = self._to_model(diary)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    @staticmethod
    def _to_model(entity: Diary) -> DiaryModel:
        """도메인 엔티티를 ORM 모델로 변환합니다."""
        return DiaryModel(
            diary_id=uuid.UUID(entity.diary_id.value),
            user_id=uuid.UUID(entity.user_id.value),
            title=entity.title,
            content=entity.content.value,
            mood=entity.mood.value,
            diary_date=entity.diary_date,
            city_id=uuid.UUID(entity.city_id.value) if entity.city_id else None,
            has_earned_points=entity.has_earned_points,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            deleted_at=entity.deleted_at,
        )

    @staticmethod
    def _to_entity(model: DiaryModel) -> Diary:
        """ORM 모델을 도메인 엔티티로 변환합니다."""
        return Diary(
            diary_id=Id(str(model.diary_id)),
            user_id=Id(str(model.user_id)),
            title=model.title,
            content=DiaryContent(model.content),
            mood=DiaryMood(model.mood),
            diary_date=model.diary_date,
            city_id=Id(str(model.city_id)) if model.city_id else None,
            has_earned_points=model.has_earned_points,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )
