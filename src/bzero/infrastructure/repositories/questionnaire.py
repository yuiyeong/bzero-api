from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bzero.domain.entities.questionnaire import Questionnaire
from bzero.domain.repositories.questionnaire import QuestionnaireRepository
from bzero.domain.value_objects import Id, QuestionAnswer
from bzero.infrastructure.db.questionnaire_model import QuestionnaireModel


class SqlAlchemyQuestionnaireRepository(QuestionnaireRepository):
    """SQLAlchemy 기반 문답지 리포지토리 구현체"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def find_by_id(self, questionnaire_id: Id) -> Questionnaire | None:
        stmt = select(QuestionnaireModel).where(
            QuestionnaireModel.questionnaire_id == questionnaire_id.value,
            QuestionnaireModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_user_and_city(self, user_id: Id, city_id: Id) -> Questionnaire | None:
        stmt = select(QuestionnaireModel).where(
            QuestionnaireModel.user_id == user_id.value,
            QuestionnaireModel.city_id == city_id.value,
            QuestionnaireModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_user_id(self, user_id: Id, offset: int = 0, limit: int = 20) -> list[Questionnaire]:
        stmt = (
            select(QuestionnaireModel)
            .where(
                QuestionnaireModel.user_id == user_id.value,
                QuestionnaireModel.deleted_at.is_(None),
            )
            .order_by(QuestionnaireModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def count_by_user_id(self, user_id: Id) -> int:
        stmt = (
            select(func.count())
            .select_from(QuestionnaireModel)
            .where(
                QuestionnaireModel.user_id == user_id.value,
                QuestionnaireModel.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def save(self, questionnaire: Questionnaire) -> Questionnaire:
        # 기존 엔티티 찾기
        stmt = select(QuestionnaireModel).where(
            QuestionnaireModel.questionnaire_id == questionnaire.questionnaire_id.value,
            QuestionnaireModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        existing_model = result.scalar_one_or_none()

        if existing_model:
            # 업데이트
            existing_model.city_id = questionnaire.city_id.value
            existing_model.question_1_answer = questionnaire.question_1_answer.value
            existing_model.question_2_answer = questionnaire.question_2_answer.value
            existing_model.question_3_answer = questionnaire.question_3_answer.value
            existing_model.has_earned_points = questionnaire.has_earned_points
            existing_model.updated_at = questionnaire.updated_at
        else:
            # 생성
            model = self._to_model(questionnaire)
            self._session.add(model)

        await self._session.flush()
        return questionnaire

    @staticmethod
    def _to_model(entity: Questionnaire) -> QuestionnaireModel:
        return QuestionnaireModel(
            questionnaire_id=entity.questionnaire_id.value,
            user_id=entity.user_id.value,
            city_id=entity.city_id.value,
            question_1_answer=entity.question_1_answer.value,
            question_2_answer=entity.question_2_answer.value,
            question_3_answer=entity.question_3_answer.value,
            has_earned_points=entity.has_earned_points,
            deleted_at=entity.deleted_at,
        )

    @staticmethod
    def _to_entity(model: QuestionnaireModel) -> Questionnaire:
        """ORM 모델을 도메인 엔티티로 변환합니다."""
        return Questionnaire(
            questionnaire_id=Id(model.questionnaire_id),
            user_id=Id(model.user_id),
            city_id=Id(model.city_id),
            question_1_answer=QuestionAnswer(model.question_1_answer),
            question_2_answer=QuestionAnswer(model.question_2_answer),
            question_3_answer=QuestionAnswer(model.question_3_answer),
            has_earned_points=model.has_earned_points,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )
