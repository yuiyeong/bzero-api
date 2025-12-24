"""문답지 API E2E 테스트."""

from datetime import datetime, timedelta
from typing import Any

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from bzero.core.settings import get_settings
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.room_stay import RoomStayStatus
from bzero.domain.value_objects.ticket import TicketStatus
from bzero.infrastructure.db.airship_model import AirshipModel
from bzero.infrastructure.db.city_model import CityModel
from bzero.infrastructure.db.city_question_model import CityQuestionModel
from bzero.infrastructure.db.guest_house_model import GuestHouseModel
from bzero.infrastructure.db.questionnaire_model import QuestionnaireModel
from bzero.infrastructure.db.room_model import RoomModel
from bzero.infrastructure.db.room_stay_model import RoomStayModel
from bzero.infrastructure.db.ticket_model import TicketModel
from bzero.infrastructure.db.user_model import UserModel


# =============================================================================
# Fixtures
# =============================================================================


@pytest_asyncio.fixture
async def sample_city(test_session: AsyncSession) -> CityModel:
    """테스트용 도시 데이터 생성."""
    now = datetime.now(get_settings().timezone)
    city = CityModel(
        city_id=Id().value,
        name="세렌시아",
        theme="관계의 도시",
        description="관계에 대해 생각하는 도시",
        image_url="https://example.com/serencia.jpg",
        base_cost_points=100,
        base_duration_hours=1,
        is_active=True,
        display_order=1,
        created_at=now,
        updated_at=now,
    )
    test_session.add(city)
    await test_session.commit()
    await test_session.refresh(city)
    return city


@pytest_asyncio.fixture
async def sample_airship(test_session: AsyncSession) -> AirshipModel:
    """테스트용 비행선 데이터 생성."""
    now = datetime.now(get_settings().timezone)
    airship = AirshipModel(
        airship_id=Id().value,
        name="일반 비행선",
        description="편안한 속도로 여행하는 일반 비행선입니다.",
        image_url="https://example.com/normal_airship.jpg",
        cost_factor=1,
        duration_factor=1,
        display_order=1,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    test_session.add(airship)
    await test_session.commit()
    await test_session.refresh(airship)
    return airship


@pytest_asyncio.fixture
async def sample_guest_house(
    test_session: AsyncSession,
    sample_city: CityModel,
) -> GuestHouseModel:
    """테스트용 게스트하우스 데이터 생성."""
    now = datetime.now(get_settings().timezone)
    guest_house = GuestHouseModel(
        guest_house_id=Id().value,
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
    await test_session.commit()
    await test_session.refresh(guest_house)
    return guest_house


@pytest_asyncio.fixture
async def sample_room(
    test_session: AsyncSession,
    sample_guest_house: GuestHouseModel,
) -> RoomModel:
    """테스트용 룸 데이터 생성."""
    now = datetime.now(get_settings().timezone)
    room = RoomModel(
        room_id=Id().value,
        guest_house_id=sample_guest_house.guest_house_id,
        max_capacity=6,
        current_capacity=0,
        created_at=now,
        updated_at=now,
    )
    test_session.add(room)
    await test_session.commit()
    await test_session.refresh(room)
    return room


@pytest_asyncio.fixture
async def sample_city_question(
    test_session: AsyncSession,
    sample_city: CityModel,
) -> CityQuestionModel:
    """테스트용 도시 질문 데이터 생성."""
    now = datetime.now(get_settings().timezone)
    question = CityQuestionModel(
        city_question_id=Id().value,
        city_id=sample_city.city_id,
        question="오늘 가장 감사했던 순간은 언제인가요?",
        display_order=1,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    test_session.add(question)
    await test_session.commit()
    await test_session.refresh(question)
    return question


@pytest_asyncio.fixture
async def sample_city_questions(
    test_session: AsyncSession,
    sample_city: CityModel,
) -> list[CityQuestionModel]:
    """테스트용 도시 질문 목록 생성."""
    now = datetime.now(get_settings().timezone)
    questions = []
    question_texts = [
        "오늘 가장 감사했던 순간은 언제인가요?",
        "최근에 누군가에게 받은 따뜻한 말이 있나요?",
        "오늘 하루 중 가장 기억에 남는 순간은?",
    ]

    for i, text in enumerate(question_texts):
        question = CityQuestionModel(
            city_question_id=Id().value,
            city_id=sample_city.city_id,
            question=text,
            display_order=i + 1,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        test_session.add(question)
        questions.append(question)

    await test_session.commit()
    for q in questions:
        await test_session.refresh(q)
    return questions


async def create_user_with_room_stay(
    test_session: AsyncSession,
    user_model: UserModel,
    sample_city: CityModel,
    sample_airship: AirshipModel,
    sample_guest_house: GuestHouseModel,
    sample_room: RoomModel,
) -> RoomStayModel:
    """사용자에 대한 체류 데이터를 생성합니다."""
    now = datetime.now(get_settings().timezone)

    # 완료된 티켓 생성
    ticket = TicketModel(
        ticket_id=Id().value,
        user_id=user_model.user_id,
        ticket_number=f"B0-TEST-{uuid7().hex[:13]}",
        # City snapshot fields
        city_id=sample_city.city_id,
        city_name=sample_city.name,
        city_theme=sample_city.theme,
        city_description=sample_city.description,
        city_image_url=sample_city.image_url,
        city_base_cost_points=sample_city.base_cost_points,
        city_base_duration_hours=sample_city.base_duration_hours,
        # Airship snapshot fields
        airship_id=sample_airship.airship_id,
        airship_name=sample_airship.name,
        airship_description=sample_airship.description,
        airship_image_url=sample_airship.image_url,
        airship_cost_factor=sample_airship.cost_factor,
        airship_duration_factor=sample_airship.duration_factor,
        # Ticket fields
        cost_points=100,
        status=TicketStatus.COMPLETED.value,
        departure_datetime=now - timedelta(hours=1),
        arrival_datetime=now,
        created_at=now,
        updated_at=now,
    )
    test_session.add(ticket)
    await test_session.flush()

    # 체류 생성
    room_stay = RoomStayModel(
        room_stay_id=Id().value,
        user_id=user_model.user_id,
        city_id=sample_city.city_id,
        guest_house_id=sample_guest_house.guest_house_id,
        room_id=sample_room.room_id,
        ticket_id=ticket.ticket_id,
        status=RoomStayStatus.CHECKED_IN.value,
        check_in_at=now,
        scheduled_check_out_at=now + timedelta(hours=24),
        actual_check_out_at=None,
        extension_count=0,
        created_at=now,
        updated_at=now,
    )
    test_session.add(room_stay)
    await test_session.commit()
    await test_session.refresh(room_stay)
    return room_stay


# =============================================================================
# Tests: POST /api/v1/questionnaires
# =============================================================================


class TestCreateQuestionnaire:
    """POST /api/v1/questionnaires 테스트."""

    async def test_create_questionnaire_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
        sample_city_question: CityQuestionModel,
    ):
        """문답지 작성 성공."""
        # Given: 사용자 생성
        response = await client.post("/api/v1/users/me", headers=auth_headers)
        user_id = response.json()["data"]["user_id"]

        # 사용자 모델 조회
        result = await test_session.execute(select(UserModel).where(UserModel.user_id == Id.from_hex(user_id).value))
        user_model = result.scalar_one()

        # 체류 생성
        room_stay = await create_user_with_room_stay(
            test_session,
            user_model,
            sample_city,
            sample_airship,
            sample_guest_house,
            sample_room,
        )

        # When
        response = await client.post(
            "/api/v1/questionnaires",
            headers=auth_headers,
            json={
                "city_question_id": sample_city_question.city_question_id.hex,
                "answer": "오늘 아침에 친구가 커피를 사줬어요.",
            },
        )

        # Then
        assert response.status_code == 201
        data = response.json()["data"]

        assert "questionnaire_id" in data
        assert data["user_id"] == user_id
        assert data["room_stay_id"] == room_stay.room_stay_id.hex
        assert data["city_id"] == sample_city.city_id.hex
        assert data["guest_house_id"] == sample_guest_house.guest_house_id.hex
        assert data["city_question_id"] == sample_city_question.city_question_id.hex
        assert data["answer"] == "오늘 아침에 친구가 커피를 사줬어요."
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_questionnaire_earns_points(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
        sample_city_question: CityQuestionModel,
    ):
        """문답지 작성 시 50P 지급."""
        # Given: 사용자 생성 (초기 1000P)
        response = await client.post("/api/v1/users/me", headers=auth_headers)
        user_id = response.json()["data"]["user_id"]
        initial_points = response.json()["data"]["current_points"]

        # 사용자 모델 조회
        result = await test_session.execute(select(UserModel).where(UserModel.user_id == Id.from_hex(user_id).value))
        user_model = result.scalar_one()

        # 체류 생성
        await create_user_with_room_stay(
            test_session,
            user_model,
            sample_city,
            sample_airship,
            sample_guest_house,
            sample_room,
        )

        # When: 문답지 작성
        await client.post(
            "/api/v1/questionnaires",
            headers=auth_headers,
            json={
                "city_question_id": sample_city_question.city_question_id.hex,
                "answer": "오늘 아침에 친구가 커피를 사줬어요.",
            },
        )

        # Then: 50P 지급 확인
        user_response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert user_response.json()["data"]["current_points"] == initial_points + 50

    async def test_create_questionnaire_fails_when_not_staying(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        sample_city_question: CityQuestionModel,
    ):
        """체류 중이 아닐 때 문답지 작성 실패."""
        # Given: 사용자 생성 (체류 없음)
        await client.post("/api/v1/users/me", headers=auth_headers)

        # When
        response = await client.post(
            "/api/v1/questionnaires",
            headers=auth_headers,
            json={
                "city_question_id": sample_city_question.city_question_id.hex,
                "answer": "답변입니다.",
            },
        )

        # Then
        assert response.status_code == 404

    async def test_create_questionnaire_fails_when_already_answered(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
        sample_city_question: CityQuestionModel,
    ):
        """이미 해당 체류에서 해당 질문에 답변한 경우 실패."""
        # Given: 사용자 생성 및 체류 생성
        response = await client.post("/api/v1/users/me", headers=auth_headers)
        user_id = response.json()["data"]["user_id"]

        result = await test_session.execute(select(UserModel).where(UserModel.user_id == Id.from_hex(user_id).value))
        user_model = result.scalar_one()

        await create_user_with_room_stay(
            test_session,
            user_model,
            sample_city,
            sample_airship,
            sample_guest_house,
            sample_room,
        )

        # 첫 번째 문답지 작성
        await client.post(
            "/api/v1/questionnaires",
            headers=auth_headers,
            json={
                "city_question_id": sample_city_question.city_question_id.hex,
                "answer": "첫 번째 답변입니다.",
            },
        )

        # When: 같은 질문에 두 번째 답변 시도
        response = await client.post(
            "/api/v1/questionnaires",
            headers=auth_headers,
            json={
                "city_question_id": sample_city_question.city_question_id.hex,
                "answer": "두 번째 답변입니다.",
            },
        )

        # Then
        assert response.status_code == 409

    async def test_create_questionnaire_multiple_questions_in_same_stay(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
        sample_city_questions: list[CityQuestionModel],
    ):
        """같은 체류에서 여러 질문에 답변 가능."""
        # Given: 사용자 생성 및 체류 생성
        response = await client.post("/api/v1/users/me", headers=auth_headers)
        user_id = response.json()["data"]["user_id"]

        result = await test_session.execute(select(UserModel).where(UserModel.user_id == Id.from_hex(user_id).value))
        user_model = result.scalar_one()

        await create_user_with_room_stay(
            test_session,
            user_model,
            sample_city,
            sample_airship,
            sample_guest_house,
            sample_room,
        )

        # When: 여러 질문에 답변
        for i, question in enumerate(sample_city_questions):
            response = await client.post(
                "/api/v1/questionnaires",
                headers=auth_headers,
                json={
                    "city_question_id": question.city_question_id.hex,
                    "answer": f"답변 {i + 1}입니다.",
                },
            )

            # Then: 각 답변은 성공해야 함
            assert response.status_code == 201

    async def test_create_questionnaire_user_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        sample_city_question: CityQuestionModel,
    ):
        """사용자가 없으면 404 에러."""
        # When: 사용자 생성 없이 문답지 작성 시도
        response = await client.post(
            "/api/v1/questionnaires",
            headers=auth_headers,
            json={
                "city_question_id": sample_city_question.city_question_id.hex,
                "answer": "답변입니다.",
            },
        )

        # Then
        assert response.status_code == 404

    async def test_create_questionnaire_unauthorized(
        self,
        client: AsyncClient,
        sample_city_question: CityQuestionModel,
    ):
        """인증 없이 요청하면 403 에러."""
        # When
        response = await client.post(
            "/api/v1/questionnaires",
            json={
                "city_question_id": sample_city_question.city_question_id.hex,
                "answer": "답변입니다.",
            },
        )

        # Then
        assert response.status_code == 403

    async def test_create_questionnaire_question_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
    ):
        """존재하지 않는 질문 ID로 작성 시도하면 에러."""
        # Given: 사용자 생성 및 체류 생성
        response = await client.post("/api/v1/users/me", headers=auth_headers)
        user_id = response.json()["data"]["user_id"]

        result = await test_session.execute(select(UserModel).where(UserModel.user_id == Id.from_hex(user_id).value))
        user_model = result.scalar_one()

        await create_user_with_room_stay(
            test_session,
            user_model,
            sample_city,
            sample_airship,
            sample_guest_house,
            sample_room,
        )

        # When: 존재하지 않는 질문 ID로 작성 시도
        nonexistent_question_id = Id().value.hex
        response = await client.post(
            "/api/v1/questionnaires",
            headers=auth_headers,
            json={
                "city_question_id": nonexistent_question_id,
                "answer": "답변입니다.",
            },
        )

        # Then
        assert response.status_code == 404


# =============================================================================
# Tests: GET /api/v1/questionnaires
# =============================================================================


class TestGetMyQuestionnaires:
    """GET /api/v1/questionnaires 테스트."""

    async def test_get_my_questionnaires_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
        sample_city_question: CityQuestionModel,
    ):
        """내 문답지 목록 조회 성공."""
        # Given: 사용자 생성 및 문답지 작성
        response = await client.post("/api/v1/users/me", headers=auth_headers)
        user_id = response.json()["data"]["user_id"]

        result = await test_session.execute(select(UserModel).where(UserModel.user_id == Id.from_hex(user_id).value))
        user_model = result.scalar_one()

        await create_user_with_room_stay(
            test_session,
            user_model,
            sample_city,
            sample_airship,
            sample_guest_house,
            sample_room,
        )

        await client.post(
            "/api/v1/questionnaires",
            headers=auth_headers,
            json={
                "city_question_id": sample_city_question.city_question_id.hex,
                "answer": "오늘 아침에 친구가 커피를 사줬어요.",
            },
        )

        # When
        response = await client.get("/api/v1/questionnaires", headers=auth_headers)

        # Then
        assert response.status_code == 200
        data = response.json()

        assert "list" in data
        assert "pagination" in data

        assert len(data["list"]) == 1
        assert data["list"][0]["answer"] == "오늘 아침에 친구가 커피를 사줬어요."
        assert data["pagination"]["total"] == 1
        assert data["pagination"]["offset"] == 0
        assert data["pagination"]["limit"] == 20

    async def test_get_my_questionnaires_empty_list(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """문답지가 없으면 빈 리스트 반환."""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        # When
        response = await client.get("/api/v1/questionnaires", headers=auth_headers)

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["list"] == []
        assert data["pagination"]["total"] == 0

    async def test_get_my_questionnaires_with_pagination(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
        sample_city_questions: list[CityQuestionModel],
    ):
        """페이지네이션으로 문답지 목록 조회."""
        # Given: 사용자 생성 및 여러 문답지 작성
        response = await client.post("/api/v1/users/me", headers=auth_headers)
        user_id = response.json()["data"]["user_id"]

        result = await test_session.execute(select(UserModel).where(UserModel.user_id == Id.from_hex(user_id).value))
        user_model = result.scalar_one()

        now = datetime.now(get_settings().timezone)
        room = RoomModel(
            room_id=Id().value,
            guest_house_id=sample_guest_house.guest_house_id,
            max_capacity=6,
            current_capacity=0,
            created_at=now,
            updated_at=now,
        )
        test_session.add(room)
        await test_session.commit()
        await test_session.refresh(room)

        room_stay = await create_user_with_room_stay(
            test_session,
            user_model,
            sample_city,
            sample_airship,
            sample_guest_house,
            room,
        )

        # DB에 직접 문답지 생성 (여러 개)
        for i, question in enumerate(sample_city_questions):
            questionnaire = QuestionnaireModel(
                questionnaire_id=Id().value,
                user_id=user_model.user_id,
                room_stay_id=room_stay.room_stay_id,
                city_question_id=question.city_question_id,
                city_question=question.question,
                answer=f"답변 {i + 1}",
                city_id=sample_city.city_id,
                guest_house_id=sample_guest_house.guest_house_id,
                created_at=now + timedelta(minutes=i),
                updated_at=now + timedelta(minutes=i),
            )
            test_session.add(questionnaire)

        await test_session.commit()

        # When
        response = await client.get(
            "/api/v1/questionnaires?offset=0&limit=2",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 200
        data = response.json()

        assert len(data["list"]) == 2
        assert data["pagination"]["total"] == 3
        assert data["pagination"]["offset"] == 0
        assert data["pagination"]["limit"] == 2

    async def test_get_my_questionnaires_user_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """사용자가 없으면 404 에러."""
        # When: 사용자 생성 없이 조회
        response = await client.get("/api/v1/questionnaires", headers=auth_headers)

        # Then
        assert response.status_code == 404

    async def test_get_my_questionnaires_unauthorized(self, client: AsyncClient):
        """인증 없이 요청하면 403 에러."""
        # When
        response = await client.get("/api/v1/questionnaires")

        # Then
        assert response.status_code == 403


# =============================================================================
# Tests: GET /api/v1/questionnaires/{questionnaire_id}
# =============================================================================


class TestGetQuestionnaireDetail:
    """GET /api/v1/questionnaires/{questionnaire_id} 테스트."""

    async def test_get_questionnaire_detail_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
        sample_city_question: CityQuestionModel,
    ):
        """문답지 상세 조회 성공."""
        # Given: 사용자 생성 및 문답지 작성
        response = await client.post("/api/v1/users/me", headers=auth_headers)
        user_id = response.json()["data"]["user_id"]

        result = await test_session.execute(select(UserModel).where(UserModel.user_id == Id.from_hex(user_id).value))
        user_model = result.scalar_one()

        await create_user_with_room_stay(
            test_session,
            user_model,
            sample_city,
            sample_airship,
            sample_guest_house,
            sample_room,
        )

        create_response = await client.post(
            "/api/v1/questionnaires",
            headers=auth_headers,
            json={
                "city_question_id": sample_city_question.city_question_id.hex,
                "answer": "오늘 아침에 친구가 커피를 사줬어요.",
            },
        )
        questionnaire_id = create_response.json()["data"]["questionnaire_id"]

        # When
        response = await client.get(
            f"/api/v1/questionnaires/{questionnaire_id}",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 200
        data = response.json()["data"]

        assert data["questionnaire_id"] == questionnaire_id
        assert data["answer"] == "오늘 아침에 친구가 커피를 사줬어요."

    async def test_get_questionnaire_detail_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """문답지가 없으면 404 에러."""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        nonexistent_questionnaire_id = Id().value.hex

        # When
        response = await client.get(
            f"/api/v1/questionnaires/{nonexistent_questionnaire_id}",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 404

    async def test_get_questionnaire_detail_forbidden_other_user(
        self,
        client: AsyncClient,
        auth_headers_factory: Any,
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
        sample_city_question: CityQuestionModel,
    ):
        """다른 사용자의 문답지 조회 시 403 에러."""
        # Given: 사용자1 생성 및 문답지 작성
        headers_user1 = auth_headers_factory(
            provider_user_id="user-1",
            email="user1@example.com",
        )
        response = await client.post("/api/v1/users/me", headers=headers_user1)
        user1_id = response.json()["data"]["user_id"]

        result = await test_session.execute(select(UserModel).where(UserModel.user_id == Id.from_hex(user1_id).value))
        user1_model = result.scalar_one()

        await create_user_with_room_stay(
            test_session,
            user1_model,
            sample_city,
            sample_airship,
            sample_guest_house,
            sample_room,
        )

        create_response = await client.post(
            "/api/v1/questionnaires",
            headers=headers_user1,
            json={
                "city_question_id": sample_city_question.city_question_id.hex,
                "answer": "사용자1의 답변입니다.",
            },
        )
        questionnaire_id = create_response.json()["data"]["questionnaire_id"]

        # Given: 사용자2 생성
        headers_user2 = auth_headers_factory(
            provider_user_id="user-2",
            email="user2@example.com",
        )
        await client.post("/api/v1/users/me", headers=headers_user2)

        # When: 사용자2가 사용자1의 문답지 조회 시도
        response = await client.get(
            f"/api/v1/questionnaires/{questionnaire_id}",
            headers=headers_user2,
        )

        # Then
        assert response.status_code == 403

    async def test_get_questionnaire_detail_user_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """사용자가 없으면 404 에러."""
        # When: 사용자 생성 없이 조회
        nonexistent_questionnaire_id = Id().value.hex
        response = await client.get(
            f"/api/v1/questionnaires/{nonexistent_questionnaire_id}",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 404

    async def test_get_questionnaire_detail_unauthorized(self, client: AsyncClient):
        """인증 없이 요청하면 403 에러."""
        # When
        questionnaire_id = Id().value.hex
        response = await client.get(f"/api/v1/questionnaires/{questionnaire_id}")

        # Then
        assert response.status_code == 403


# =============================================================================
# Tests: PATCH /api/v1/questionnaires/{questionnaire_id}
# =============================================================================


class TestUpdateQuestionnaire:
    """PATCH /api/v1/questionnaires/{questionnaire_id} 테스트."""

    async def test_update_questionnaire_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
        sample_city_question: CityQuestionModel,
    ):
        """문답지 수정 성공."""
        # Given: 사용자 생성 및 문답지 작성
        response = await client.post("/api/v1/users/me", headers=auth_headers)
        user_id = response.json()["data"]["user_id"]

        result = await test_session.execute(select(UserModel).where(UserModel.user_id == Id.from_hex(user_id).value))
        user_model = result.scalar_one()

        await create_user_with_room_stay(
            test_session,
            user_model,
            sample_city,
            sample_airship,
            sample_guest_house,
            sample_room,
        )

        create_response = await client.post(
            "/api/v1/questionnaires",
            headers=auth_headers,
            json={
                "city_question_id": sample_city_question.city_question_id.hex,
                "answer": "원래 답변입니다.",
            },
        )
        questionnaire_id = create_response.json()["data"]["questionnaire_id"]

        # When
        response = await client.patch(
            f"/api/v1/questionnaires/{questionnaire_id}",
            headers=auth_headers,
            json={
                "answer": "수정된 답변입니다.",
            },
        )

        # Then
        assert response.status_code == 200
        data = response.json()["data"]

        assert data["questionnaire_id"] == questionnaire_id
        assert data["answer"] == "수정된 답변입니다."

    async def test_update_questionnaire_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """문답지가 없으면 404 에러."""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        nonexistent_questionnaire_id = Id().value.hex

        # When
        response = await client.patch(
            f"/api/v1/questionnaires/{nonexistent_questionnaire_id}",
            headers=auth_headers,
            json={
                "answer": "수정된 답변입니다.",
            },
        )

        # Then
        assert response.status_code == 404

    async def test_update_questionnaire_forbidden_other_user(
        self,
        client: AsyncClient,
        auth_headers_factory: Any,
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
        sample_city_question: CityQuestionModel,
    ):
        """다른 사용자의 문답지 수정 시 403 에러."""
        # Given: 사용자1 생성 및 문답지 작성
        headers_user1 = auth_headers_factory(
            provider_user_id="user-1",
            email="user1@example.com",
        )
        response = await client.post("/api/v1/users/me", headers=headers_user1)
        user1_id = response.json()["data"]["user_id"]

        result = await test_session.execute(select(UserModel).where(UserModel.user_id == Id.from_hex(user1_id).value))
        user1_model = result.scalar_one()

        await create_user_with_room_stay(
            test_session,
            user1_model,
            sample_city,
            sample_airship,
            sample_guest_house,
            sample_room,
        )

        create_response = await client.post(
            "/api/v1/questionnaires",
            headers=headers_user1,
            json={
                "city_question_id": sample_city_question.city_question_id.hex,
                "answer": "사용자1의 답변입니다.",
            },
        )
        questionnaire_id = create_response.json()["data"]["questionnaire_id"]

        # Given: 사용자2 생성
        headers_user2 = auth_headers_factory(
            provider_user_id="user-2",
            email="user2@example.com",
        )
        await client.post("/api/v1/users/me", headers=headers_user2)

        # When: 사용자2가 사용자1의 문답지 수정 시도
        response = await client.patch(
            f"/api/v1/questionnaires/{questionnaire_id}",
            headers=headers_user2,
            json={
                "answer": "수정된 답변입니다.",
            },
        )

        # Then
        assert response.status_code == 403

    async def test_update_questionnaire_user_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """사용자가 없으면 404 에러."""
        # When: 사용자 생성 없이 수정 시도
        nonexistent_questionnaire_id = Id().value.hex
        response = await client.patch(
            f"/api/v1/questionnaires/{nonexistent_questionnaire_id}",
            headers=auth_headers,
            json={
                "answer": "수정된 답변입니다.",
            },
        )

        # Then
        assert response.status_code == 404

    async def test_update_questionnaire_unauthorized(self, client: AsyncClient):
        """인증 없이 요청하면 403 에러."""
        # When
        questionnaire_id = Id().value.hex
        response = await client.patch(
            f"/api/v1/questionnaires/{questionnaire_id}",
            json={
                "answer": "수정된 답변입니다.",
            },
        )

        # Then
        assert response.status_code == 403


# =============================================================================
# Tests: DELETE /api/v1/questionnaires/{questionnaire_id}
# =============================================================================


class TestDeleteQuestionnaire:
    """DELETE /api/v1/questionnaires/{questionnaire_id} 테스트."""

    async def test_delete_questionnaire_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
        sample_city_question: CityQuestionModel,
    ):
        """문답지 삭제 성공 (soft delete)."""
        # Given: 사용자 생성 및 문답지 작성
        response = await client.post("/api/v1/users/me", headers=auth_headers)
        user_id = response.json()["data"]["user_id"]

        result = await test_session.execute(select(UserModel).where(UserModel.user_id == Id.from_hex(user_id).value))
        user_model = result.scalar_one()

        await create_user_with_room_stay(
            test_session,
            user_model,
            sample_city,
            sample_airship,
            sample_guest_house,
            sample_room,
        )

        create_response = await client.post(
            "/api/v1/questionnaires",
            headers=auth_headers,
            json={
                "city_question_id": sample_city_question.city_question_id.hex,
                "answer": "삭제할 답변입니다.",
            },
        )
        questionnaire_id = create_response.json()["data"]["questionnaire_id"]

        # When
        response = await client.delete(
            f"/api/v1/questionnaires/{questionnaire_id}",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 204

        # 삭제 후 조회 불가 확인
        get_response = await client.get(
            f"/api/v1/questionnaires/{questionnaire_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    async def test_delete_questionnaire_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """문답지가 없으면 404 에러."""
        # Given: 사용자 생성
        await client.post("/api/v1/users/me", headers=auth_headers)

        nonexistent_questionnaire_id = Id().value.hex

        # When
        response = await client.delete(
            f"/api/v1/questionnaires/{nonexistent_questionnaire_id}",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 404

    async def test_delete_questionnaire_forbidden_other_user(
        self,
        client: AsyncClient,
        auth_headers_factory: Any,
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
        sample_city_question: CityQuestionModel,
    ):
        """다른 사용자의 문답지 삭제 시 403 에러."""
        # Given: 사용자1 생성 및 문답지 작성
        headers_user1 = auth_headers_factory(
            provider_user_id="user-1",
            email="user1@example.com",
        )
        response = await client.post("/api/v1/users/me", headers=headers_user1)
        user1_id = response.json()["data"]["user_id"]

        result = await test_session.execute(select(UserModel).where(UserModel.user_id == Id.from_hex(user1_id).value))
        user1_model = result.scalar_one()

        await create_user_with_room_stay(
            test_session,
            user1_model,
            sample_city,
            sample_airship,
            sample_guest_house,
            sample_room,
        )

        create_response = await client.post(
            "/api/v1/questionnaires",
            headers=headers_user1,
            json={
                "city_question_id": sample_city_question.city_question_id.hex,
                "answer": "사용자1의 답변입니다.",
            },
        )
        questionnaire_id = create_response.json()["data"]["questionnaire_id"]

        # Given: 사용자2 생성
        headers_user2 = auth_headers_factory(
            provider_user_id="user-2",
            email="user2@example.com",
        )
        await client.post("/api/v1/users/me", headers=headers_user2)

        # When: 사용자2가 사용자1의 문답지 삭제 시도
        response = await client.delete(
            f"/api/v1/questionnaires/{questionnaire_id}",
            headers=headers_user2,
        )

        # Then
        assert response.status_code == 403

    async def test_delete_questionnaire_user_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """사용자가 없으면 404 에러."""
        # When: 사용자 생성 없이 삭제 시도
        nonexistent_questionnaire_id = Id().value.hex
        response = await client.delete(
            f"/api/v1/questionnaires/{nonexistent_questionnaire_id}",
            headers=auth_headers,
        )

        # Then
        assert response.status_code == 404

    async def test_delete_questionnaire_unauthorized(self, client: AsyncClient):
        """인증 없이 요청하면 403 에러."""
        # When
        questionnaire_id = Id().value.hex
        response = await client.delete(f"/api/v1/questionnaires/{questionnaire_id}")

        # Then
        assert response.status_code == 403


# =============================================================================
# Tests: 문답지 플로우 통합 테스트
# =============================================================================


class TestQuestionnaireFlow:
    """문답지 플로우 통합 테스트."""

    async def test_full_questionnaire_flow(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
        sample_room: RoomModel,
        sample_city_question: CityQuestionModel,
    ):
        """전체 문답지 플로우 테스트: 생성 -> 조회 -> 수정 -> 삭제."""
        # 1. 사용자 생성
        user_response = await client.post("/api/v1/users/me", headers=auth_headers)
        assert user_response.status_code == 201
        user_id = user_response.json()["data"]["user_id"]
        initial_points = user_response.json()["data"]["current_points"]

        # 체류 생성
        result = await test_session.execute(select(UserModel).where(UserModel.user_id == Id.from_hex(user_id).value))
        user_model = result.scalar_one()

        await create_user_with_room_stay(
            test_session,
            user_model,
            sample_city,
            sample_airship,
            sample_guest_house,
            sample_room,
        )

        # 2. 문답지 작성
        create_response = await client.post(
            "/api/v1/questionnaires",
            headers=auth_headers,
            json={
                "city_question_id": sample_city_question.city_question_id.hex,
                "answer": "오늘 아침에 친구가 커피를 사줬어요.",
            },
        )
        assert create_response.status_code == 201
        questionnaire_id = create_response.json()["data"]["questionnaire_id"]

        # 3. 포인트 지급 확인
        user_response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert user_response.json()["data"]["current_points"] == initial_points + 50

        # 4. 문답지 목록 조회
        list_response = await client.get("/api/v1/questionnaires", headers=auth_headers)
        assert list_response.status_code == 200
        assert len(list_response.json()["list"]) == 1

        # 5. 문답지 상세 조회
        detail_response = await client.get(
            f"/api/v1/questionnaires/{questionnaire_id}",
            headers=auth_headers,
        )
        assert detail_response.status_code == 200
        assert detail_response.json()["data"]["questionnaire_id"] == questionnaire_id

        # 6. 문답지 수정
        update_response = await client.patch(
            f"/api/v1/questionnaires/{questionnaire_id}",
            headers=auth_headers,
            json={
                "answer": "수정된 답변입니다.",
            },
        )
        assert update_response.status_code == 200
        assert update_response.json()["data"]["answer"] == "수정된 답변입니다."

        # 7. 문답지 삭제
        delete_response = await client.delete(
            f"/api/v1/questionnaires/{questionnaire_id}",
            headers=auth_headers,
        )
        assert delete_response.status_code == 204

        # 8. 삭제 후 조회 불가 확인
        get_response = await client.get(
            f"/api/v1/questionnaires/{questionnaire_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    async def test_multiple_users_questionnaire_isolation(
        self,
        client: AsyncClient,
        auth_headers_factory: Any,
        test_session: AsyncSession,
        sample_city: CityModel,
        sample_airship: AirshipModel,
        sample_guest_house: GuestHouseModel,
        sample_city_question: CityQuestionModel,
    ):
        """다른 사용자의 문답지는 서로 격리됨."""
        now = datetime.now(get_settings().timezone)

        # Given: 두 명의 사용자 생성
        headers_user1 = auth_headers_factory(
            provider_user_id="user-1",
            email="user1@example.com",
        )
        headers_user2 = auth_headers_factory(
            provider_user_id="user-2",
            email="user2@example.com",
        )

        response1 = await client.post("/api/v1/users/me", headers=headers_user1)
        response2 = await client.post("/api/v1/users/me", headers=headers_user2)

        user1_id = response1.json()["data"]["user_id"]
        user2_id = response2.json()["data"]["user_id"]

        # 각 사용자 모델 조회
        result1 = await test_session.execute(select(UserModel).where(UserModel.user_id == Id.from_hex(user1_id).value))
        user1_model = result1.scalar_one()

        result2 = await test_session.execute(select(UserModel).where(UserModel.user_id == Id.from_hex(user2_id).value))
        user2_model = result2.scalar_one()

        # 각 사용자별 룸 및 체류 생성
        room1 = RoomModel(
            room_id=Id().value,
            guest_house_id=sample_guest_house.guest_house_id,
            max_capacity=6,
            current_capacity=0,
            created_at=now,
            updated_at=now,
        )
        room2 = RoomModel(
            room_id=Id().value,
            guest_house_id=sample_guest_house.guest_house_id,
            max_capacity=6,
            current_capacity=0,
            created_at=now,
            updated_at=now,
        )
        test_session.add(room1)
        test_session.add(room2)
        await test_session.commit()
        await test_session.refresh(room1)
        await test_session.refresh(room2)

        await create_user_with_room_stay(
            test_session,
            user1_model,
            sample_city,
            sample_airship,
            sample_guest_house,
            room1,
        )

        await create_user_with_room_stay(
            test_session,
            user2_model,
            sample_city,
            sample_airship,
            sample_guest_house,
            room2,
        )

        # When: 사용자1만 문답지 작성
        await client.post(
            "/api/v1/questionnaires",
            headers=headers_user1,
            json={
                "city_question_id": sample_city_question.city_question_id.hex,
                "answer": "사용자1의 답변입니다.",
            },
        )

        # Then: 각 사용자는 자신의 문답지만 조회 가능
        list_response1 = await client.get("/api/v1/questionnaires", headers=headers_user1)
        list_response2 = await client.get("/api/v1/questionnaires", headers=headers_user2)

        assert len(list_response1.json()["list"]) == 1
        assert len(list_response2.json()["list"]) == 0
