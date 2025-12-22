"""DiaryRepository 핵심 로직.

쿼리 빌더, Entity/Model 변환, DB 작업 로직을 모두 포함합니다.
비동기 리포지토리는 run_sync로 호출합니다.

구조:
    DiaryRepositoryCore (쿼리 빌더 + 변환 + DB 작업)
         ↑
    SqlAlchemy
    DiaryRepo
    (run_sync)
"""

from sqlalchemy import Select, Update, func, select, update
from sqlalchemy.orm import Session

from bzero.domain.entities.diary import Diary
from bzero.domain.errors import NotFoundDiaryError
from bzero.domain.value_objects import DiaryMood, Id
from bzero.infrastructure.db.diary_model import DiaryModel


class DiaryRepositoryCore:
    """DiaryRepository 핵심 로직.

    쿼리 생성, Entity/Model 변환, DB 작업 로직을 모두 포함합니다.
    모든 DB 작업 메서드는 정적 메서드로, 첫 번째 인자로 Session을 받습니다.
    이 패턴을 통해 AsyncSession.run_sync()와 호환됩니다.
    """

    # ==================== 쿼리 빌더 ====================

    @staticmethod
    def _query_find_by_diary_id(diary_id: Id) -> Select[tuple[DiaryModel]]:
        """ID로 일기를 조회하는 쿼리를 생성합니다."""
        return select(DiaryModel).where(
            DiaryModel.diary_id == diary_id.value,
            DiaryModel.deleted_at.is_(None),
        )

    @staticmethod
    def _query_find_by_room_stay_id(room_stay_id: Id) -> Select[tuple[DiaryModel]]:
        """체류 ID로 일기를 조회하는 쿼리를 생성합니다."""
        return select(DiaryModel).where(
            DiaryModel.room_stay_id == room_stay_id.value,
            DiaryModel.deleted_at.is_(None),
        )

    @staticmethod
    def _query_find_all_by_user_id(
        user_id: Id,
        limit: int,
        offset: int,
    ) -> Select[tuple[DiaryModel]]:
        """사용자의 모든 일기를 조회하는 쿼리를 생성합니다."""
        return (
            select(DiaryModel)
            .where(
                DiaryModel.user_id == user_id.value,
                DiaryModel.deleted_at.is_(None),
            )
            .order_by(DiaryModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

    @staticmethod
    def _query_count_by_user_id(user_id: Id) -> Select[tuple[int]]:
        """사용자의 일기 총 개수를 조회하는 쿼리를 생성합니다."""
        return select(func.count(DiaryModel.diary_id)).where(
            DiaryModel.user_id == user_id.value,
            DiaryModel.deleted_at.is_(None),
        )

    @staticmethod
    def _query_exists_by_room_stay_id(room_stay_id: Id) -> Select[tuple[int]]:
        """체류 ID로 일기 존재 여부를 확인하는 쿼리를 생성합니다."""
        return select(func.count(DiaryModel.diary_id)).where(
            DiaryModel.room_stay_id == room_stay_id.value,
            DiaryModel.deleted_at.is_(None),
        )

    @staticmethod
    def _query_update(diary: Diary) -> Update:
        """일기를 업데이트하는 쿼리를 생성합니다."""
        return (
            update(DiaryModel)
            .where(
                DiaryModel.diary_id == diary.diary_id.value,
                DiaryModel.deleted_at.is_(None),
            )
            .values(
                title=diary.title,
                content=diary.content,
                mood=diary.mood.value,
                updated_at=diary.updated_at,
                deleted_at=diary.deleted_at,
            )
            .returning(DiaryModel)
        )

    # ==================== Entity/Model 변환 ====================

    @staticmethod
    def to_model(entity: Diary) -> DiaryModel:
        """Diary 엔티티를 DiaryModel(ORM)로 변환합니다."""
        return DiaryModel(
            diary_id=entity.diary_id.value,
            user_id=entity.user_id.value,
            room_stay_id=entity.room_stay_id.value,
            city_id=entity.city_id.value,
            guest_house_id=entity.guest_house_id.value,
            title=entity.title,
            content=entity.content,
            mood=entity.mood.value,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            deleted_at=entity.deleted_at,
        )

    @staticmethod
    def to_entity(model: DiaryModel) -> Diary:
        """DiaryModel(ORM)을 Diary 엔티티로 변환합니다."""
        return Diary(
            diary_id=Id(model.diary_id),
            user_id=Id(model.user_id),
            room_stay_id=Id(model.room_stay_id),
            city_id=Id(model.city_id),
            guest_house_id=Id(model.guest_house_id),
            title=model.title,
            content=model.content,
            mood=DiaryMood(model.mood),
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )

    # ==================== DB 작업 로직 ====================

    @staticmethod
    def create(session: Session, diary: Diary) -> Diary:
        """일기를 생성합니다."""
        model = DiaryRepositoryCore.to_model(diary)

        session.add(model)
        session.flush()
        session.refresh(model)

        return DiaryRepositoryCore.to_entity(model)

    @staticmethod
    def find_by_diary_id(session: Session, diary_id: Id) -> Diary | None:
        """ID로 일기를 조회합니다."""
        stmt = DiaryRepositoryCore._query_find_by_diary_id(diary_id)
        result = session.execute(stmt)
        model = result.scalar_one_or_none()
        return DiaryRepositoryCore.to_entity(model) if model else None

    @staticmethod
    def find_by_room_stay_id(session: Session, room_stay_id: Id) -> Diary | None:
        """체류 ID로 일기를 조회합니다."""
        stmt = DiaryRepositoryCore._query_find_by_room_stay_id(room_stay_id)
        result = session.execute(stmt)
        model = result.scalar_one_or_none()
        return DiaryRepositoryCore.to_entity(model) if model else None

    @staticmethod
    def find_all_by_user_id(
        session: Session,
        user_id: Id,
        limit: int,
        offset: int,
    ) -> list[Diary]:
        """사용자의 모든 일기를 조회합니다."""
        stmt = DiaryRepositoryCore._query_find_all_by_user_id(user_id, limit, offset)
        result = session.execute(stmt)
        models = result.scalars().all()
        return [DiaryRepositoryCore.to_entity(model) for model in models]

    @staticmethod
    def count_by_user_id(session: Session, user_id: Id) -> int:
        """사용자의 일기 총 개수를 조회합니다."""
        stmt = DiaryRepositoryCore._query_count_by_user_id(user_id)
        result = session.execute(stmt)
        return result.scalar_one()

    @staticmethod
    def update(session: Session, diary: Diary) -> Diary:
        """일기를 업데이트합니다.

        Raises:
            NotFoundDiaryError: 일기를 찾을 수 없는 경우
        """
        stmt = DiaryRepositoryCore._query_update(diary)
        result = session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise NotFoundDiaryError
        return DiaryRepositoryCore.to_entity(model)

    @staticmethod
    def exists_by_room_stay_id(session: Session, room_stay_id: Id) -> bool:
        """체류 ID로 일기 존재 여부를 확인합니다."""
        stmt = DiaryRepositoryCore._query_exists_by_room_stay_id(room_stay_id)
        result = session.execute(stmt)
        count = result.scalar_one()
        return count > 0
