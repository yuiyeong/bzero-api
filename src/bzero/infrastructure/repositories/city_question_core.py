"""CityQuestionRepository 핵심 로직.

쿼리 빌더, Entity/Model 변환, DB 작업 로직을 모두 포함합니다.
비동기 리포지토리는 run_sync로 호출합니다.
"""

from sqlalchemy import Select, Update, select, update
from sqlalchemy.orm import Session

from bzero.domain.entities.city_question import CityQuestion
from bzero.domain.errors import NotFoundCityQuestionError
from bzero.domain.value_objects import Id
from bzero.infrastructure.db.city_question_model import CityQuestionModel


class CityQuestionRepositoryCore:
    """CityQuestionRepository 핵심 로직.

    쿼리 생성, Entity/Model 변환, DB 작업 로직을 모두 포함합니다.
    모든 DB 작업 메서드는 정적 메서드로, 첫 번째 인자로 Session을 받습니다.
    이 패턴을 통해 AsyncSession.run_sync()와 호환됩니다.
    """

    # ==================== 쿼리 빌더 ====================

    @staticmethod
    def _query_find_by_id(city_question_id: Id) -> Select[tuple[CityQuestionModel]]:
        """ID로 질문을 조회하는 쿼리를 생성합니다."""
        return select(CityQuestionModel).where(
            CityQuestionModel.city_question_id == city_question_id.value,
            CityQuestionModel.deleted_at.is_(None),
        )

    @staticmethod
    def _query_find_active_by_city_id(city_id: Id) -> Select[tuple[CityQuestionModel]]:
        """도시의 활성화된 질문을 조회하는 쿼리를 생성합니다."""
        return (
            select(CityQuestionModel)
            .where(
                CityQuestionModel.city_id == city_id.value,
                CityQuestionModel.is_active.is_(True),
                CityQuestionModel.deleted_at.is_(None),
            )
            .order_by(CityQuestionModel.display_order.asc())
        )

    @staticmethod
    def _query_update(city_question: CityQuestion) -> Update:
        """질문을 업데이트하는 쿼리를 생성합니다."""
        return (
            update(CityQuestionModel)
            .where(
                CityQuestionModel.city_question_id == city_question.city_question_id.value,
                CityQuestionModel.deleted_at.is_(None),
            )
            .values(
                question=city_question.question,
                display_order=city_question.display_order,
                is_active=city_question.is_active,
                updated_at=city_question.updated_at,
                deleted_at=city_question.deleted_at,
            )
            .returning(CityQuestionModel)
        )

    # ==================== Entity/Model 변환 ====================

    @staticmethod
    def to_model(entity: CityQuestion) -> CityQuestionModel:
        """CityQuestion 엔티티를 CityQuestionModel(ORM)로 변환합니다."""
        return CityQuestionModel(
            city_question_id=entity.city_question_id.value,
            city_id=entity.city_id.value,
            question=entity.question,
            display_order=entity.display_order,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            deleted_at=entity.deleted_at,
        )

    @staticmethod
    def to_entity(model: CityQuestionModel) -> CityQuestion:
        """CityQuestionModel(ORM)을 CityQuestion 엔티티로 변환합니다."""
        return CityQuestion(
            city_question_id=Id(model.city_question_id),
            city_id=Id(model.city_id),
            question=model.question,
            display_order=model.display_order,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )

    # ==================== DB 작업 로직 ====================

    @staticmethod
    def create(session: Session, city_question: CityQuestion) -> CityQuestion:
        """질문을 생성합니다."""
        model = CityQuestionRepositoryCore.to_model(city_question)

        session.add(model)
        session.flush()
        session.refresh(model)

        return CityQuestionRepositoryCore.to_entity(model)

    @staticmethod
    def find_by_id(session: Session, city_question_id: Id) -> CityQuestion | None:
        """ID로 질문을 조회합니다."""
        stmt = CityQuestionRepositoryCore._query_find_by_id(city_question_id)
        result = session.execute(stmt)
        model = result.scalar_one_or_none()
        return CityQuestionRepositoryCore.to_entity(model) if model else None

    @staticmethod
    def find_active_by_city_id(session: Session, city_id: Id) -> list[CityQuestion]:
        """도시의 활성화된 질문을 조회합니다."""
        stmt = CityQuestionRepositoryCore._query_find_active_by_city_id(city_id)
        result = session.execute(stmt)
        models = result.scalars().all()
        return [CityQuestionRepositoryCore.to_entity(model) for model in models]

    @staticmethod
    def update(session: Session, city_question: CityQuestion) -> CityQuestion:
        """질문을 업데이트합니다.

        Raises:
            NotFoundCityQuestionError: 질문을 찾을 수 없는 경우
        """
        stmt = CityQuestionRepositoryCore._query_update(city_question)
        result = session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise NotFoundCityQuestionError
        return CityQuestionRepositoryCore.to_entity(model)
