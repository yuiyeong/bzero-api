"""QuestionnaireRepository 통합 테스트."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from bzero.domain.entities.questionnaire import Questionnaire
from bzero.domain.errors import NotFoundQuestionnaireError
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
def questionnaire_repository(test_session: AsyncSession) -> SqlAlchemyQuestionnaireRepository:
    """QuestionnaireRepository fixture를 생성합니다."""
    return SqlAlchemyQuestionnaireRepository(test_session)


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
        base_duration_minutes=24,
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
        city_base_duration_minutes=sample_city.base_duration_minutes,
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
async def sample_room_stay(
    test_session: AsyncSession,
    sample_user: UserModel,
    sample_room: RoomModel,
    sample_ticket: TicketModel,
    sample_guest_house: GuestHouseModel,
    sample_city: CityModel,
) -> RoomStayModel:
    """테스트용 샘플 룸 스테이 데이터를 생성합니다."""
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
async def sample_city_question(
    test_session: AsyncSession,
    sample_city: CityModel,
) -> CityQuestionModel:
    """테스트용 샘플 도시 질문 데이터를 생성합니다."""
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
async def sample_questionnaire(
    test_session: AsyncSession,
    sample_user: UserModel,
    sample_room_stay: RoomStayModel,
    sample_city_question: CityQuestionModel,
    sample_city: CityModel,
    sample_guest_house: GuestHouseModel,
) -> QuestionnaireModel:
    """테스트용 샘플 문답지 데이터를 생성합니다."""
    now = datetime.now()
    questionnaire = QuestionnaireModel(
        questionnaire_id=uuid7(),
        user_id=sample_user.user_id,
        room_stay_id=sample_room_stay.room_stay_id,
        city_question_id=sample_city_question.city_question_id,
        city_question=sample_city_question.question,
        answer="오늘 아침에 친구가 커피를 사줬어요.",
        city_id=sample_city.city_id,
        guest_house_id=sample_guest_house.guest_house_id,
        created_at=now,
        updated_at=now,
    )
    test_session.add(questionnaire)
    await test_session.flush()
    return questionnaire


@pytest.fixture
async def sample_questionnaires(
    test_session: AsyncSession,
    sample_user: UserModel,
    sample_city: CityModel,
    sample_guest_house: GuestHouseModel,
    sample_room: RoomModel,
    sample_airship: AirshipModel,
) -> list[QuestionnaireModel]:
    """테스트용 샘플 문답지 목록을 생성합니다."""
    now = datetime.now()
    questionnaires = []

    for i in range(5):
        # 각 문답지마다 새로운 ticket, room_stay, city_question 생성
        ticket = TicketModel(
            ticket_id=uuid7(),
            user_id=sample_user.user_id,
            city_id=sample_city.city_id,
            city_name=sample_city.name,
            city_theme=sample_city.theme,
            city_description=sample_city.description,
            city_image_url=sample_city.image_url,
            city_base_cost_points=sample_city.base_cost_points,
            city_base_duration_minutes=sample_city.base_duration_minutes,
            airship_id=sample_airship.airship_id,
            airship_name=sample_airship.name,
            airship_description=sample_airship.description,
            airship_image_url=sample_airship.image_url,
            airship_cost_factor=sample_airship.cost_factor,
            airship_duration_factor=sample_airship.duration_factor,
            ticket_number=f"B0-2025-TEST{i:03d}",
            cost_points=300,
            status="completed",
            departure_datetime=now - timedelta(days=i + 1),
            arrival_datetime=now - timedelta(days=i),
            created_at=now - timedelta(days=i + 1),
            updated_at=now - timedelta(days=i),
        )
        test_session.add(ticket)
        await test_session.flush()

        room_stay = RoomStayModel(
            room_stay_id=uuid7(),
            user_id=sample_user.user_id,
            city_id=sample_city.city_id,
            room_id=sample_room.room_id,
            ticket_id=ticket.ticket_id,
            guest_house_id=sample_guest_house.guest_house_id,
            status=RoomStayStatus.CHECKED_OUT.value,
            check_in_at=now - timedelta(days=i + 1),
            scheduled_check_out_at=now - timedelta(days=i),
            actual_check_out_at=now - timedelta(days=i),
            created_at=now - timedelta(days=i + 1),
            updated_at=now - timedelta(days=i),
        )
        test_session.add(room_stay)
        await test_session.flush()

        city_question = CityQuestionModel(
            city_question_id=uuid7(),
            city_id=sample_city.city_id,
            question=f"질문 #{i + 1}",
            display_order=i + 1,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        test_session.add(city_question)
        await test_session.flush()

        questionnaire = QuestionnaireModel(
            questionnaire_id=uuid7(),
            user_id=sample_user.user_id,
            room_stay_id=room_stay.room_stay_id,
            city_question_id=city_question.city_question_id,
            city_question=city_question.question,
            answer=f"답변 #{i + 1}입니다.",
            city_id=sample_city.city_id,
            guest_house_id=sample_guest_house.guest_house_id,
            created_at=now - timedelta(days=i),
            updated_at=now - timedelta(days=i),
        )
        test_session.add(questionnaire)
        questionnaires.append(questionnaire)

    await test_session.flush()
    return questionnaires


# =============================================================================
# Tests
# =============================================================================


class TestQuestionnaireRepositoryCreate:
    """QuestionnaireRepository.create() 메서드 테스트."""

    async def test_create_questionnaire_success(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
        sample_user: UserModel,
        sample_room_stay: RoomStayModel,
        sample_city_question: CityQuestionModel,
        sample_city: CityModel,
        sample_guest_house: GuestHouseModel,
    ):
        """새로운 문답지를 생성할 수 있어야 합니다."""
        # Given
        now = datetime.now()
        questionnaire = Questionnaire.create(
            user_id=Id(str(sample_user.user_id)),
            room_stay_id=Id(str(sample_room_stay.room_stay_id)),
            city_question_id=Id(str(sample_city_question.city_question_id)),
            city_question=sample_city_question.question,
            answer="새로운 답변입니다.",
            city_id=Id(str(sample_city.city_id)),
            guest_house_id=Id(str(sample_guest_house.guest_house_id)),
            created_at=now,
            updated_at=now,
        )

        # When
        created = await questionnaire_repository.create(questionnaire)

        # Then
        assert created is not None
        assert str(created.questionnaire_id.value) == str(questionnaire.questionnaire_id.value)
        assert str(created.user_id.value) == str(sample_user.user_id)
        assert str(created.room_stay_id.value) == str(sample_room_stay.room_stay_id)
        assert created.city_question == sample_city_question.question
        assert created.answer == "새로운 답변입니다."


class TestQuestionnaireRepositoryFindById:
    """QuestionnaireRepository.find_by_id() 메서드 테스트."""

    async def test_find_by_id_success(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
        sample_questionnaire: QuestionnaireModel,
    ):
        """ID로 문답지를 조회할 수 있어야 합니다."""
        # When
        questionnaire = await questionnaire_repository.find_by_id(Id(str(sample_questionnaire.questionnaire_id)))

        # Then
        assert questionnaire is not None
        assert str(questionnaire.questionnaire_id.value) == str(sample_questionnaire.questionnaire_id)
        assert questionnaire.answer == sample_questionnaire.answer

    async def test_find_by_id_returns_none_when_not_found(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
    ):
        """존재하지 않는 ID로 조회 시 None을 반환해야 합니다."""
        # Given
        non_existent_id = Id()

        # When
        questionnaire = await questionnaire_repository.find_by_id(non_existent_id)

        # Then
        assert questionnaire is None

    async def test_find_by_id_soft_deleted_excluded(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
        sample_questionnaire: QuestionnaireModel,
        test_session: AsyncSession,
    ):
        """Soft delete된 문답지는 조회되지 않아야 합니다."""
        # Given: 문답지를 soft delete
        sample_questionnaire.deleted_at = datetime.now()
        await test_session.flush()

        # When
        questionnaire = await questionnaire_repository.find_by_id(Id(str(sample_questionnaire.questionnaire_id)))

        # Then
        assert questionnaire is None


class TestQuestionnaireRepositoryFindByRoomStayAndQuestion:
    """QuestionnaireRepository.find_by_room_stay_and_question() 메서드 테스트."""

    async def test_find_by_room_stay_and_question_success(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
        sample_questionnaire: QuestionnaireModel,
        sample_room_stay: RoomStayModel,
        sample_city_question: CityQuestionModel,
    ):
        """체류 ID와 질문 ID로 문답지를 조회할 수 있어야 합니다."""
        # When
        questionnaire = await questionnaire_repository.find_by_room_stay_and_question(
            room_stay_id=Id(str(sample_room_stay.room_stay_id)),
            city_question_id=Id(str(sample_city_question.city_question_id)),
        )

        # Then
        assert questionnaire is not None
        assert str(questionnaire.room_stay_id.value) == str(sample_room_stay.room_stay_id)
        assert str(questionnaire.city_question_id.value) == str(sample_city_question.city_question_id)

    async def test_find_by_room_stay_and_question_returns_none_when_not_found(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
    ):
        """문답지가 없으면 None을 반환해야 합니다."""
        # Given
        non_existent_room_stay_id = Id()
        non_existent_question_id = Id()

        # When
        questionnaire = await questionnaire_repository.find_by_room_stay_and_question(
            room_stay_id=non_existent_room_stay_id,
            city_question_id=non_existent_question_id,
        )

        # Then
        assert questionnaire is None


class TestQuestionnaireRepositoryFindAllByUserId:
    """QuestionnaireRepository.find_all_by_user_id() 메서드 테스트."""

    async def test_find_all_by_user_id_success(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
        sample_user: UserModel,
        sample_questionnaires: list[QuestionnaireModel],
    ):
        """사용자 ID로 문답지 목록을 조회할 수 있어야 합니다."""
        # When
        questionnaires = await questionnaire_repository.find_all_by_user_id(
            Id(str(sample_user.user_id)), limit=20, offset=0
        )

        # Then
        assert len(questionnaires) == 5
        assert all(str(q.user_id.value) == str(sample_user.user_id) for q in questionnaires)

    async def test_find_all_by_user_id_ordered_by_created_at_desc(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
        sample_user: UserModel,
        sample_questionnaires: list[QuestionnaireModel],
    ):
        """문답지 목록은 created_at 내림차순으로 정렬되어야 합니다."""
        # When
        questionnaires = await questionnaire_repository.find_all_by_user_id(
            Id(str(sample_user.user_id)), limit=20, offset=0
        )

        # Then
        assert len(questionnaires) == 5
        for i in range(len(questionnaires) - 1):
            assert questionnaires[i].created_at >= questionnaires[i + 1].created_at

    async def test_find_all_by_user_id_with_pagination(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
        sample_user: UserModel,
        sample_questionnaires: list[QuestionnaireModel],
    ):
        """pagination 파라미터로 문답지 목록을 조회할 수 있어야 합니다."""
        # When
        questionnaires = await questionnaire_repository.find_all_by_user_id(
            Id(str(sample_user.user_id)), limit=2, offset=0
        )

        # Then
        assert len(questionnaires) == 2

    async def test_find_all_by_user_id_soft_deleted_excluded(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
        sample_user: UserModel,
        sample_questionnaires: list[QuestionnaireModel],
        test_session: AsyncSession,
    ):
        """Soft delete된 문답지는 조회되지 않아야 합니다."""
        # Given: 첫 번째 문답지를 soft delete
        sample_questionnaires[0].deleted_at = datetime.now()
        await test_session.flush()

        # When
        questionnaires = await questionnaire_repository.find_all_by_user_id(
            Id(str(sample_user.user_id)), limit=20, offset=0
        )

        # Then
        assert len(questionnaires) == 4

    async def test_find_all_by_user_id_empty(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
    ):
        """문답지가 없으면 빈 리스트를 반환해야 합니다."""
        # Given
        non_existent_user_id = Id()

        # When
        questionnaires = await questionnaire_repository.find_all_by_user_id(non_existent_user_id, limit=20, offset=0)

        # Then
        assert questionnaires == []


class TestQuestionnaireRepositoryFindAllByRoomStayId:
    """QuestionnaireRepository.find_all_by_room_stay_id() 메서드 테스트."""

    async def test_find_all_by_room_stay_id_success(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
        sample_questionnaire: QuestionnaireModel,
        sample_room_stay: RoomStayModel,
    ):
        """체류 ID로 문답지 목록을 조회할 수 있어야 합니다."""
        # When
        questionnaires = await questionnaire_repository.find_all_by_room_stay_id(Id(str(sample_room_stay.room_stay_id)))

        # Then
        assert len(questionnaires) == 1
        assert str(questionnaires[0].room_stay_id.value) == str(sample_room_stay.room_stay_id)

    async def test_find_all_by_room_stay_id_returns_empty_list(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
    ):
        """문답지가 없으면 빈 리스트를 반환해야 합니다."""
        # Given
        non_existent_room_stay_id = Id()

        # When
        questionnaires = await questionnaire_repository.find_all_by_room_stay_id(non_existent_room_stay_id)

        # Then
        assert questionnaires == []


class TestQuestionnaireRepositoryCountByUserId:
    """QuestionnaireRepository.count_by_user_id() 메서드 테스트."""

    async def test_count_by_user_id_success(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
        sample_user: UserModel,
        sample_questionnaires: list[QuestionnaireModel],
    ):
        """사용자 ID로 문답지 개수를 조회할 수 있어야 합니다."""
        # When
        count = await questionnaire_repository.count_by_user_id(Id(str(sample_user.user_id)))

        # Then
        assert count == 5

    async def test_count_by_user_id_soft_deleted_excluded(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
        sample_user: UserModel,
        sample_questionnaires: list[QuestionnaireModel],
        test_session: AsyncSession,
    ):
        """Soft delete된 문답지는 카운트에서 제외되어야 합니다."""
        # Given
        sample_questionnaires[0].deleted_at = datetime.now()
        await test_session.flush()

        # When
        count = await questionnaire_repository.count_by_user_id(Id(str(sample_user.user_id)))

        # Then
        assert count == 4

    async def test_count_by_user_id_returns_zero_when_no_results(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
    ):
        """문답지가 없으면 0을 반환해야 합니다."""
        # Given
        non_existent_user_id = Id()

        # When
        count = await questionnaire_repository.count_by_user_id(non_existent_user_id)

        # Then
        assert count == 0


class TestQuestionnaireRepositoryUpdate:
    """QuestionnaireRepository.update() 메서드 테스트."""

    async def test_update_questionnaire_success(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
        sample_questionnaire: QuestionnaireModel,
    ):
        """문답지를 업데이트할 수 있어야 합니다."""
        # Given
        questionnaire = await questionnaire_repository.find_by_id(Id(str(sample_questionnaire.questionnaire_id)))
        assert questionnaire is not None

        new_answer = "수정된 답변입니다."
        updated_at = datetime.now()
        questionnaire.update_answer(answer_text=new_answer, updated_at=updated_at)

        # When
        updated = await questionnaire_repository.update(questionnaire)

        # Then
        assert updated is not None
        assert updated.answer == "수정된 답변입니다."

    async def test_update_non_existent_questionnaire_raises_error(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
        sample_user: UserModel,
        sample_city: CityModel,
        sample_guest_house: GuestHouseModel,
    ):
        """존재하지 않는 문답지 업데이트 시 NotFoundQuestionnaireError 발생."""
        # Given
        now = datetime.now()
        non_existent_questionnaire = Questionnaire(
            questionnaire_id=Id(),  # 새로운 ID (DB에 없음)
            user_id=Id(str(sample_user.user_id)),
            room_stay_id=Id(),
            city_question_id=Id(),
            city_question="오늘 가장 감사했던 순간은 언제인가요?",
            answer="답변",
            city_id=Id(str(sample_city.city_id)),
            guest_house_id=Id(str(sample_guest_house.guest_house_id)),
            created_at=now,
            updated_at=now,
        )

        # When/Then
        with pytest.raises(NotFoundQuestionnaireError):
            await questionnaire_repository.update(non_existent_questionnaire)


class TestQuestionnaireRepositoryExistsByRoomStayAndQuestion:
    """QuestionnaireRepository.exists_by_room_stay_and_question() 메서드 테스트."""

    async def test_exists_by_room_stay_and_question_returns_true_when_exists(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
        sample_questionnaire: QuestionnaireModel,
        sample_room_stay: RoomStayModel,
        sample_city_question: CityQuestionModel,
    ):
        """문답지가 존재하면 True를 반환해야 합니다."""
        # When
        exists = await questionnaire_repository.exists_by_room_stay_and_question(
            room_stay_id=Id(str(sample_room_stay.room_stay_id)),
            city_question_id=Id(str(sample_city_question.city_question_id)),
        )

        # Then
        assert exists is True

    async def test_exists_by_room_stay_and_question_returns_false_when_not_exists(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
    ):
        """문답지가 존재하지 않으면 False를 반환해야 합니다."""
        # Given
        non_existent_room_stay_id = Id()
        non_existent_question_id = Id()

        # When
        exists = await questionnaire_repository.exists_by_room_stay_and_question(
            room_stay_id=non_existent_room_stay_id,
            city_question_id=non_existent_question_id,
        )

        # Then
        assert exists is False

    async def test_exists_by_room_stay_and_question_soft_deleted_excluded(
        self,
        questionnaire_repository: SqlAlchemyQuestionnaireRepository,
        sample_questionnaire: QuestionnaireModel,
        sample_room_stay: RoomStayModel,
        sample_city_question: CityQuestionModel,
        test_session: AsyncSession,
    ):
        """Soft delete된 문답지는 존재하지 않는 것으로 처리되어야 합니다."""
        # Given
        sample_questionnaire.deleted_at = datetime.now()
        await test_session.flush()

        # When
        exists = await questionnaire_repository.exists_by_room_stay_and_question(
            room_stay_id=Id(str(sample_room_stay.room_stay_id)),
            city_question_id=Id(str(sample_city_question.city_question_id)),
        )

        # Then
        assert exists is False
