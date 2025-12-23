"""QuestionnaireRepository 핵심 로직.

쿼리 빌더, Entity/Model 변환, DB 작업 로직을 모두 포함합니다.
비동기 리포지토리는 run_sync로 호출합니다.
"""

from sqlalchemy import Select, Update, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from bzero.domain.entities.questionnaire import Questionnaire
from bzero.domain.errors import DuplicatedQuestionnaireError, NotFoundQuestionnaireError
from bzero.domain.value_objects import Id
from bzero.infrastructure.db.questionnaire_model import QuestionnaireModel


class QuestionnaireRepositoryCore:
    """QuestionnaireRepository 핵심 로직.

    쿼리 생성, Entity/Model 변환, DB 작업 로직을 모두 포함합니다.
    모든 DB 작업 메서드는 정적 메서드로, 첫 번째 인자로 Session을 받습니다.
    이 패턴을 통해 AsyncSession.run_sync()와 호환됩니다.
    """

    # ==================== 쿼리 빌더 ====================

    @staticmethod
    def _query_find_by_id(questionnaire_id: Id) -> Select[tuple[QuestionnaireModel]]:
        """ID로 문답지를 조회하는 쿼리를 생성합니다."""
        return select(QuestionnaireModel).where(
            QuestionnaireModel.questionnaire_id == questionnaire_id.value,
            QuestionnaireModel.deleted_at.is_(None),
        )

    @staticmethod
    def _query_find_by_room_stay_and_question(
        room_stay_id: Id,
        city_question_id: Id,
    ) -> Select[tuple[QuestionnaireModel]]:
        """체류 ID와 질문 ID로 문답지를 조회하는 쿼리를 생성합니다."""
        return select(QuestionnaireModel).where(
            QuestionnaireModel.room_stay_id == room_stay_id.value,
            QuestionnaireModel.city_question_id == city_question_id.value,
            QuestionnaireModel.deleted_at.is_(None),
        )

    @staticmethod
    def _query_find_all_by_user_id(
        user_id: Id,
        limit: int,
        offset: int,
    ) -> Select[tuple[QuestionnaireModel]]:
        """사용자의 모든 문답지를 조회하는 쿼리를 생성합니다."""
        return (
            select(QuestionnaireModel)
            .where(
                QuestionnaireModel.user_id == user_id.value,
                QuestionnaireModel.deleted_at.is_(None),
            )
            .order_by(QuestionnaireModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

    @staticmethod
    def _query_find_all_by_room_stay_id(room_stay_id: Id) -> Select[tuple[QuestionnaireModel]]:
        """체류 ID로 모든 문답지를 조회하는 쿼리를 생성합니다."""
        return (
            select(QuestionnaireModel)
            .where(
                QuestionnaireModel.room_stay_id == room_stay_id.value,
                QuestionnaireModel.deleted_at.is_(None),
            )
            .order_by(QuestionnaireModel.created_at.asc())
        )

    @staticmethod
    def _query_count_by_user_id(user_id: Id) -> Select[tuple[int]]:
        """사용자의 문답지 총 개수를 조회하는 쿼리를 생성합니다."""
        return select(func.count(QuestionnaireModel.questionnaire_id)).where(
            QuestionnaireModel.user_id == user_id.value,
            QuestionnaireModel.deleted_at.is_(None),
        )

    @staticmethod
    def _query_exists_by_room_stay_and_question(
        room_stay_id: Id,
        city_question_id: Id,
    ) -> Select[tuple[int]]:
        """체류 ID와 질문 ID로 존재 여부를 확인하는 쿼리를 생성합니다."""
        return select(func.count(QuestionnaireModel.questionnaire_id)).where(
            QuestionnaireModel.room_stay_id == room_stay_id.value,
            QuestionnaireModel.city_question_id == city_question_id.value,
            QuestionnaireModel.deleted_at.is_(None),
        )

    @staticmethod
    def _query_update(questionnaire: Questionnaire) -> Update:
        """문답지를 업데이트하는 쿼리를 생성합니다."""
        return (
            update(QuestionnaireModel)
            .where(
                QuestionnaireModel.questionnaire_id == questionnaire.questionnaire_id.value,
                QuestionnaireModel.deleted_at.is_(None),
            )
            .values(
                answer=questionnaire.answer,
                updated_at=questionnaire.updated_at,
                deleted_at=questionnaire.deleted_at,
            )
            .returning(QuestionnaireModel)
        )

    # ==================== Entity/Model 변환 ====================

    @staticmethod
    def to_model(entity: Questionnaire) -> QuestionnaireModel:
        """Questionnaire 엔티티를 QuestionnaireModel(ORM)로 변환합니다."""
        return QuestionnaireModel(
            questionnaire_id=entity.questionnaire_id.value,
            user_id=entity.user_id.value,
            room_stay_id=entity.room_stay_id.value,
            city_question_id=entity.city_question_id.value,
            city_question=entity.city_question,
            answer=entity.answer,
            city_id=entity.city_id.value,
            guest_house_id=entity.guest_house_id.value,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            deleted_at=entity.deleted_at,
        )

    @staticmethod
    def to_entity(model: QuestionnaireModel) -> Questionnaire:
        """QuestionnaireModel(ORM)을 Questionnaire 엔티티로 변환합니다."""
        return Questionnaire(
            questionnaire_id=Id(model.questionnaire_id),
            user_id=Id(model.user_id),
            room_stay_id=Id(model.room_stay_id),
            city_question_id=Id(model.city_question_id),
            city_question=model.city_question,
            answer=model.answer,
            city_id=Id(model.city_id),
            guest_house_id=Id(model.guest_house_id),
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )

    # ==================== DB 작업 로직 ====================

    # PostgreSQL unique violation error code
    _PG_UNIQUE_VIOLATION = "23505"

    @staticmethod
    def create(session: Session, questionnaire: Questionnaire) -> Questionnaire:
        """문답지를 생성합니다.

        Raises:
            DuplicatedQuestionnaireError: 동일한 체류에서 동일한 질문에 이미 답변이 존재하는 경우
        """
        model = QuestionnaireRepositoryCore.to_model(questionnaire)

        session.add(model)
        try:
            session.flush()
        except IntegrityError as e:
            session.rollback()
            # PostgreSQL unique violation 처리
            if hasattr(e.orig, "pgcode") and e.orig.pgcode == QuestionnaireRepositoryCore._PG_UNIQUE_VIOLATION:
                raise DuplicatedQuestionnaireError from e
            raise
        session.refresh(model)

        return QuestionnaireRepositoryCore.to_entity(model)

    @staticmethod
    def find_by_id(session: Session, questionnaire_id: Id) -> Questionnaire | None:
        """ID로 문답지를 조회합니다."""
        stmt = QuestionnaireRepositoryCore._query_find_by_id(questionnaire_id)
        result = session.execute(stmt)
        model = result.scalar_one_or_none()
        return QuestionnaireRepositoryCore.to_entity(model) if model else None

    @staticmethod
    def find_by_room_stay_and_question(
        session: Session,
        room_stay_id: Id,
        city_question_id: Id,
    ) -> Questionnaire | None:
        """체류 ID와 질문 ID로 문답지를 조회합니다."""
        stmt = QuestionnaireRepositoryCore._query_find_by_room_stay_and_question(room_stay_id, city_question_id)
        result = session.execute(stmt)
        model = result.scalar_one_or_none()
        return QuestionnaireRepositoryCore.to_entity(model) if model else None

    @staticmethod
    def find_all_by_user_id(
        session: Session,
        user_id: Id,
        limit: int,
        offset: int,
    ) -> list[Questionnaire]:
        """사용자의 모든 문답지를 조회합니다."""
        stmt = QuestionnaireRepositoryCore._query_find_all_by_user_id(user_id, limit, offset)
        result = session.execute(stmt)
        models = result.scalars().all()
        return [QuestionnaireRepositoryCore.to_entity(model) for model in models]

    @staticmethod
    def find_all_by_room_stay_id(session: Session, room_stay_id: Id) -> list[Questionnaire]:
        """체류 ID로 모든 문답지를 조회합니다."""
        stmt = QuestionnaireRepositoryCore._query_find_all_by_room_stay_id(room_stay_id)
        result = session.execute(stmt)
        models = result.scalars().all()
        return [QuestionnaireRepositoryCore.to_entity(model) for model in models]

    @staticmethod
    def count_by_user_id(session: Session, user_id: Id) -> int:
        """사용자의 문답지 총 개수를 조회합니다."""
        stmt = QuestionnaireRepositoryCore._query_count_by_user_id(user_id)
        result = session.execute(stmt)
        return result.scalar_one()

    @staticmethod
    def update(session: Session, questionnaire: Questionnaire) -> Questionnaire:
        """문답지를 업데이트합니다.

        Raises:
            NotFoundQuestionnaireError: 문답지를 찾을 수 없는 경우
        """
        stmt = QuestionnaireRepositoryCore._query_update(questionnaire)
        result = session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise NotFoundQuestionnaireError
        return QuestionnaireRepositoryCore.to_entity(model)

    @staticmethod
    def exists_by_room_stay_and_question(
        session: Session,
        room_stay_id: Id,
        city_question_id: Id,
    ) -> bool:
        """체류 ID와 질문 ID로 존재 여부를 확인합니다."""
        stmt = QuestionnaireRepositoryCore._query_exists_by_room_stay_and_question(room_stay_id, city_question_id)
        result = session.execute(stmt)
        count = result.scalar_one()
        return count > 0
