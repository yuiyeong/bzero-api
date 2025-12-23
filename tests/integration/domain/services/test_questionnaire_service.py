"""QuestionnaireService 통합 테스트."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from bzero.domain.entities.city_question import CityQuestion
from bzero.domain.entities.room_stay import RoomStay
from bzero.domain.errors import DuplicatedQuestionnaireError, NotFoundQuestionnaireError
from bzero.domain.services.questionnaire import QuestionnaireService
from bzero.domain.value_objects import Id, RoomStayStatus
from bzero.infrastructure.db.airship_model import AirshipModel
from bzero.infrastructure.db.city_model import CityModel
from bzero.infrastructure.db.city_question_model import CityQuestionModel
from bzero.infrastructure.db.guest_house_model import GuestHouseModel
from bzero.infrastructure.db.questionnaire_model import QuestionnaireModel
from bzero.infrastructure.db.room_model import RoomModel
from bzero.infrastructure.db.room_stay_model import RoomStayModel
from bzero.infrastructure.db.ticket_model import TicketModel
from bzero.infrastructure.db.user_model import UserModel
from bzero.infrastructure.repositories.questionnaire import SqlAlchemyQuestionnaireRepository


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def timezone() -> ZoneInfo:
    """Seoul timezone."""
    return ZoneInfo("Asia/Seoul")


@pytest.fixture
def questionnaire_service(test_session: AsyncSession, timezone: ZoneInfo) -> QuestionnaireService:
    """QuestionnaireService fixture를 생성합니다."""
    repository = SqlAlchemyQuestionnaireRepository(test_session)
    return QuestionnaireService(questionnaire_repository=repository, timezone=timezone)


@pytest.fixture
async def sample_user(test_session: AsyncSession) -> UserModel:
    """테스트용 샘플 유저 데이터를 생성합니다."""
    now = datetime.now()
    user = UserModel(
        user_id=uuid7(),
        email="test@example.com",
        nickname="테스트유저",
        profile_emoji="👤",
        current_points=10000,
        created_at=now,
        updated_at=now,
    )
    test_session.add(user)
    await test_session.flush()
    return user


@pytest.fixture
async def sample_city(test_session: AsyncSession) -> CityModel:
    """테스트용 샘플 도시 데이터를 생성합니다."""
    now = datetime.now()
    city = CityModel(
        city_id=uuid7(),
        name="세렌시아",
        theme="관계",
        description="노을빛 항구 마을",
        image_url="https://example.com/serentia.jpg",
        base_cost_points=300,
        base_duration_hours=24,
        is_active=True,
        display_order=1,
        created_at=now,
        updated_at=now,
    )
    test_session.add(city)
    await test_session.flush()
    return city


@pytest.fixture
async def sample_guest_house(test_session: AsyncSession, sample_city: CityModel) -> GuestHouseModel:
    """테스트용 샘플 게스트하우스 데이터를 생성합니다."""
    now = datetime.now()
    guest_house = GuestHouseModel(
        guest_house_id=uuid7(),
        city_id=sample_city.city_id,
        guest_house_type="mixed",
        name="혼합형 게스트하우스",
        description="대화를 나눌 수 있는 공간",
        image_url="https://example.com/mixed.jpg",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    test_session.add(guest_house)
    await test_session.flush()
    return guest_house


@pytest.fixture
async def sample_room(test_session: AsyncSession, sample_guest_house: GuestHouseModel) -> RoomModel:
    """테스트용 샘플 룸 데이터를 생성합니다."""
    now = datetime.now()
    room = RoomModel(
        room_id=uuid7(),
        guest_house_id=sample_guest_house.guest_house_id,
        max_capacity=6,
        current_capacity=1,
        created_at=now,
        updated_at=now,
    )
    test_session.add(room)
    await test_session.flush()
    return room


@pytest.fixture
async def sample_airship(test_session: AsyncSession) -> AirshipModel:
    """테스트용 샘플 비행선 데이터를 생성합니다."""
    now = datetime.now()
    airship = AirshipModel(
        airship_id=uuid7(),
        name="일반 비행선",
        description="편안하고 여유로운 여행을 원하는 여행자를 위한 비행선",
        image_url="https://example.com/normal.jpg",
        cost_factor=1,
        duration_factor=1,
        display_order=1,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    test_session.add(airship)
    await test_session.flush()
    return airship


@pytest.fixture
async def sample_ticket(
    test_session: AsyncSession,
    sample_user: UserModel,
    sample_city: CityModel,
    sample_airship: AirshipModel,
) -> TicketModel:
    """테스트용 샘플 티켓 데이터를 생성합니다."""
    now = datetime.now()
    ticket = TicketModel(
        ticket_id=uuid7(),
        user_id=sample_user.user_id,
        city_id=sample_city.city_id,
        city_name=sample_city.name,
        city_theme=sample_city.theme,
        city_description=sample_city.description,
        city_image_url=sample_city.image_url,
        city_base_cost_points=sample_city.base_cost_points,
        city_base_duration_hours=sample_city.base_duration_hours,
        airship_id=sample_airship.airship_id,
        airship_name=sample_airship.name,
        airship_description=sample_airship.description,
        airship_image_url=sample_airship.image_url,
        airship_cost_factor=sample_airship.cost_factor,
        airship_duration_factor=sample_airship.duration_factor,
        ticket_number="B0-2025-TEST001",
        cost_points=300,
        status="boarding",
        departure_datetime=now - timedelta(hours=1),
        arrival_datetime=now + timedelta(hours=23),
        created_at=now,
        updated_at=now,
    )
    test_session.add(ticket)
    await test_session.flush()
    return ticket


@pytest.fixture
async def sample_room_stay_model(
    test_session: AsyncSession,
    sample_user: UserModel,
    sample_room: RoomModel,
    sample_ticket: TicketModel,
    sample_guest_house: GuestHouseModel,
    sample_city: CityModel,
) -> RoomStayModel:
    """테스트용 샘플 룸 스테이 모델을 생성합니다."""
    now = datetime.now()
    room_stay = RoomStayModel(
        room_stay_id=uuid7(),
        user_id=sample_user.user_id,
        city_id=sample_city.city_id,
        room_id=sample_room.room_id,
        ticket_id=sample_ticket.ticket_id,
        guest_house_id=sample_guest_house.guest_house_id,
        status=RoomStayStatus.CHECKED_IN.value,
        check_in_at=now,
        scheduled_check_out_at=now + timedelta(hours=24),
        created_at=now,
        updated_at=now,
    )
    test_session.add(room_stay)
    await test_session.flush()
    return room_stay


@pytest.fixture
def sample_room_stay_entity(sample_room_stay_model: RoomStayModel) -> RoomStay:
    """RoomStayModel을 RoomStay 엔티티로 변환합니다."""
    return RoomStay(
        room_stay_id=Id(str(sample_room_stay_model.room_stay_id)),
        user_id=Id(str(sample_room_stay_model.user_id)),
        city_id=Id(str(sample_room_stay_model.city_id)),
        guest_house_id=Id(str(sample_room_stay_model.guest_house_id)),
        room_id=Id(str(sample_room_stay_model.room_id)),
        ticket_id=Id(str(sample_room_stay_model.ticket_id)),
        status=RoomStayStatus(sample_room_stay_model.status),
        check_in_at=sample_room_stay_model.check_in_at,
        scheduled_check_out_at=sample_room_stay_model.scheduled_check_out_at,
        actual_check_out_at=sample_room_stay_model.actual_check_out_at,
        extension_count=sample_room_stay_model.extension_count or 0,
        created_at=sample_room_stay_model.created_at,
        updated_at=sample_room_stay_model.updated_at,
    )


@pytest.fixture
async def sample_city_question_model(
    test_session: AsyncSession,
    sample_city: CityModel,
) -> CityQuestionModel:
    """테스트용 샘플 도시 질문 모델을 생성합니다."""
    now = datetime.now()
    question = CityQuestionModel(
        city_question_id=uuid7(),
        city_id=sample_city.city_id,
        question="오늘 가장 감사했던 순간은 언제인가요?",
        display_order=1,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    test_session.add(question)
    await test_session.flush()
    return question


@pytest.fixture
def sample_city_question_entity(sample_city_question_model: CityQuestionModel) -> CityQuestion:
    """CityQuestionModel을 CityQuestion 엔티티로 변환합니다."""
    return CityQuestion(
        city_question_id=Id(str(sample_city_question_model.city_question_id)),
        city_id=Id(str(sample_city_question_model.city_id)),
        question=sample_city_question_model.question,
        display_order=sample_city_question_model.display_order,
        is_active=sample_city_question_model.is_active,
        created_at=sample_city_question_model.created_at,
        updated_at=sample_city_question_model.updated_at,
        deleted_at=sample_city_question_model.deleted_at,
    )


@pytest.fixture
async def sample_questionnaire(
    test_session: AsyncSession,
    sample_user: UserModel,
    sample_room_stay_model: RoomStayModel,
    sample_city_question_model: CityQuestionModel,
    sample_city: CityModel,
    sample_guest_house: GuestHouseModel,
) -> QuestionnaireModel:
    """테스트용 샘플 문답지 데이터를 생성합니다."""
    now = datetime.now()
    questionnaire = QuestionnaireModel(
        questionnaire_id=uuid7(),
        user_id=sample_user.user_id,
        room_stay_id=sample_room_stay_model.room_stay_id,
        city_question_id=sample_city_question_model.city_question_id,
        city_question=sample_city_question_model.question,
        answer="오늘 아침에 친구가 커피를 사줬어요.",
        city_id=sample_city.city_id,
        guest_house_id=sample_guest_house.guest_house_id,
        created_at=now,
        updated_at=now,
    )
    test_session.add(questionnaire)
    await test_session.flush()
    return questionnaire


# =============================================================================
# Tests
# =============================================================================


class TestQuestionnaireServiceCreateQuestionnaire:
    """create_questionnaire 메서드 통합 테스트."""

    async def test_create_questionnaire_success(
        self,
        questionnaire_service: QuestionnaireService,
        sample_room_stay_entity: RoomStay,
        sample_city: CityModel,
        test_session: AsyncSession,
    ):
        """새로운 문답지를 생성할 수 있다."""
        # Given: 새로운 질문 생성
        now = datetime.now()
        question_model = CityQuestionModel(
            city_question_id=uuid7(),
            city_id=sample_city.city_id,
            question="새 질문입니다.",
            display_order=2,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        test_session.add(question_model)
        await test_session.flush()

        # 엔티티로 변환
        city_question_entity = CityQuestion(
            city_question_id=Id(str(question_model.city_question_id)),
            city_id=Id(str(question_model.city_id)),
            question=question_model.question,
            display_order=question_model.display_order,
            is_active=question_model.is_active,
            created_at=question_model.created_at,
            updated_at=question_model.updated_at,
        )

        # When
        questionnaire = await questionnaire_service.create_questionnaire(
            room_stay=sample_room_stay_entity,
            city_question=city_question_entity,
            answer="새로운 답변입니다.",
        )

        # Then
        assert questionnaire is not None
        assert questionnaire.user_id == sample_room_stay_entity.user_id
        assert questionnaire.answer == "새로운 답변입니다."
        assert questionnaire.city_question == city_question_entity.question

    async def test_create_questionnaire_raises_error_when_already_exists(
        self,
        questionnaire_service: QuestionnaireService,
        sample_room_stay_entity: RoomStay,
        sample_city_question_entity: CityQuestion,
        sample_questionnaire: QuestionnaireModel,  # 이미 존재
    ):
        """이미 해당 체류에서 해당 질문에 답변이 존재하면 에러가 발생한다."""
        # When/Then
        with pytest.raises(DuplicatedQuestionnaireError):
            await questionnaire_service.create_questionnaire(
                room_stay=sample_room_stay_entity,
                city_question=sample_city_question_entity,
                answer="중복 답변입니다.",
            )


class TestQuestionnaireServiceGetQuestionnaireById:
    """get_questionnaire_by_id 메서드 통합 테스트."""

    async def test_get_questionnaire_by_id_success(
        self,
        questionnaire_service: QuestionnaireService,
        sample_questionnaire: QuestionnaireModel,
    ):
        """ID로 문답지를 조회할 수 있다."""
        # When
        questionnaire = await questionnaire_service.get_questionnaire_by_id(
            Id(str(sample_questionnaire.questionnaire_id))
        )

        # Then
        assert questionnaire is not None
        assert str(questionnaire.questionnaire_id.value) == str(sample_questionnaire.questionnaire_id)
        assert questionnaire.answer == sample_questionnaire.answer

    async def test_get_questionnaire_by_id_raises_error_when_not_found(
        self,
        questionnaire_service: QuestionnaireService,
    ):
        """존재하지 않는 문답지 조회 시 NotFoundQuestionnaireError 발생."""
        # Given
        non_existent_id = Id()

        # When/Then
        with pytest.raises(NotFoundQuestionnaireError):
            await questionnaire_service.get_questionnaire_by_id(non_existent_id)


class TestQuestionnaireServiceGetQuestionnairesByUserId:
    """get_questionnaires_by_user_id 메서드 통합 테스트."""

    async def test_get_questionnaires_by_user_id_success(
        self,
        questionnaire_service: QuestionnaireService,
        sample_user: UserModel,
        sample_questionnaire: QuestionnaireModel,
    ):
        """사용자의 문답지 목록을 조회할 수 있다."""
        # When
        questionnaires, total = await questionnaire_service.get_questionnaires_by_user_id(Id(str(sample_user.user_id)))

        # Then
        assert len(questionnaires) == 1
        assert total == 1

    async def test_get_questionnaires_by_user_id_returns_empty_when_no_results(
        self,
        questionnaire_service: QuestionnaireService,
    ):
        """문답지가 없으면 빈 리스트를 반환한다."""
        # Given
        non_existent_user_id = Id()

        # When
        questionnaires, total = await questionnaire_service.get_questionnaires_by_user_id(non_existent_user_id)

        # Then
        assert questionnaires == []
        assert total == 0


class TestQuestionnaireServiceUpdateQuestionnaire:
    """update_questionnaire 메서드 통합 테스트."""

    async def test_update_questionnaire_success(
        self,
        questionnaire_service: QuestionnaireService,
        sample_questionnaire: QuestionnaireModel,
    ):
        """문답지를 수정할 수 있다."""
        # When
        updated = await questionnaire_service.update_questionnaire(
            questionnaire_id=Id(str(sample_questionnaire.questionnaire_id)),
            answer_text="수정된 답변입니다.",
        )

        # Then
        assert updated.answer == "수정된 답변입니다."

    async def test_update_questionnaire_raises_error_when_not_found(
        self,
        questionnaire_service: QuestionnaireService,
    ):
        """존재하지 않는 문답지 수정 시 NotFoundQuestionnaireError 발생."""
        # Given
        non_existent_id = Id()

        # When/Then
        with pytest.raises(NotFoundQuestionnaireError):
            await questionnaire_service.update_questionnaire(
                questionnaire_id=non_existent_id,
                answer_text="수정된 답변입니다.",
            )


class TestQuestionnaireServiceDeleteQuestionnaire:
    """delete_questionnaire 메서드 통합 테스트."""

    async def test_delete_questionnaire_success(
        self,
        questionnaire_service: QuestionnaireService,
        sample_questionnaire: QuestionnaireModel,
    ):
        """문답지를 삭제할 수 있다 (soft delete)."""
        # When
        deleted = await questionnaire_service.delete_questionnaire(Id(str(sample_questionnaire.questionnaire_id)))

        # Then
        assert deleted.deleted_at is not None

    async def test_delete_questionnaire_raises_error_when_not_found(
        self,
        questionnaire_service: QuestionnaireService,
    ):
        """존재하지 않는 문답지 삭제 시 NotFoundQuestionnaireError 발생."""
        # Given
        non_existent_id = Id()

        # When/Then
        with pytest.raises(NotFoundQuestionnaireError):
            await questionnaire_service.delete_questionnaire(non_existent_id)
