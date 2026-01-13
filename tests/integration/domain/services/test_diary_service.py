"""DiaryService 통합 테스트"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from bzero.core.settings import get_settings
from bzero.domain.errors import DuplicatedDiaryError, NotFoundDiaryError
from bzero.domain.services.diary import DiaryService
from bzero.domain.value_objects import Id, RoomStayStatus
from bzero.domain.value_objects.diary import DiaryMood
from bzero.infrastructure.db.airship_model import AirshipModel
from bzero.infrastructure.db.city_model import CityModel
from bzero.infrastructure.db.diary_model import DiaryModel
from bzero.infrastructure.db.guest_house_model import GuestHouseModel
from bzero.infrastructure.db.room_model import RoomModel
from bzero.infrastructure.db.room_stay_model import RoomStayModel
from bzero.infrastructure.db.ticket_model import TicketModel
from bzero.infrastructure.db.user_model import UserModel
from bzero.infrastructure.repositories.diary import SqlAlchemyDiaryRepository


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def timezone() -> ZoneInfo:
    """Seoul timezone"""
    return get_settings().timezone


@pytest.fixture
def diary_service(test_session: AsyncSession, timezone: ZoneInfo) -> DiaryService:
    """DiaryService fixture를 생성합니다."""
    repository = SqlAlchemyDiaryRepository(test_session)
    return DiaryService(repository, timezone)


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
async def sample_diary(
    test_session: AsyncSession,
    sample_user: UserModel,
    sample_room_stay: RoomStayModel,
    sample_city: CityModel,
    sample_guest_house: GuestHouseModel,
) -> DiaryModel:
    """테스트용 샘플 일기 데이터를 생성합니다."""
    now = datetime.now()
    diary = DiaryModel(
        diary_id=uuid7(),
        user_id=sample_user.user_id,
        room_stay_id=sample_room_stay.room_stay_id,
        city_id=sample_city.city_id,
        guest_house_id=sample_guest_house.guest_house_id,
        title="오늘의 일기",
        content="오늘 하루도 평화로웠다.",
        mood=DiaryMood.PEACEFUL.value,
        created_at=now,
        updated_at=now,
    )
    test_session.add(diary)
    await test_session.flush()
    return diary


@pytest.fixture
async def sample_diaries(
    test_session: AsyncSession,
    sample_user: UserModel,
    sample_city: CityModel,
    sample_guest_house: GuestHouseModel,
    sample_room: RoomModel,
    sample_airship: AirshipModel,
) -> list[DiaryModel]:
    """테스트용 샘플 일기 데이터 목록을 생성합니다."""
    now = datetime.now()
    diaries = []

    for i in range(5):
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

        diary = DiaryModel(
            diary_id=uuid7(),
            user_id=sample_user.user_id,
            room_stay_id=room_stay.room_stay_id,
            city_id=sample_city.city_id,
            guest_house_id=sample_guest_house.guest_house_id,
            title=f"일기 #{i + 1}",
            content=f"일기 내용 #{i + 1}입니다.",
            mood=DiaryMood.PEACEFUL.value,
            created_at=now - timedelta(days=i),
            updated_at=now - timedelta(days=i),
        )
        test_session.add(diary)
        diaries.append(diary)

    await test_session.flush()
    return diaries


# =============================================================================
# Tests
# =============================================================================


class TestDiaryServiceCreateDiary:
    """DiaryService.create_diary() 통합 테스트"""

    async def test_create_diary_success(
        self,
        diary_service: DiaryService,
        sample_user: UserModel,
        sample_room_stay: RoomStayModel,
        sample_city: CityModel,
        sample_guest_house: GuestHouseModel,
        sample_airship: AirshipModel,
        sample_room: RoomModel,
        test_session: AsyncSession,
    ):
        """일기를 성공적으로 생성할 수 있다"""
        # Given
        # sample_room_stay fixture는 이미 생성되어 있음 (일기 없음)
        # 새로운 room_stay를 만들어야 함
        now = datetime.now()

        # 새 티켓 생성
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
            ticket_number="B0-2025-NEW001",
            cost_points=300,
            status="boarding",
            departure_datetime=now,
            arrival_datetime=now + timedelta(hours=24),
            created_at=now,
            updated_at=now,
        )
        test_session.add(ticket)
        await test_session.flush()

        # 새 room_stay 생성 (일기가 없는)
        new_room_stay = RoomStayModel(
            room_stay_id=uuid7(),
            user_id=sample_user.user_id,
            city_id=sample_city.city_id,
            room_id=sample_room.room_id,
            ticket_id=ticket.ticket_id,
            guest_house_id=sample_guest_house.guest_house_id,
            status=RoomStayStatus.CHECKED_IN.value,
            check_in_at=now,
            scheduled_check_out_at=now + timedelta(hours=24),
            created_at=now,
            updated_at=now,
        )
        test_session.add(new_room_stay)
        await test_session.flush()

        # When
        diary = await diary_service.create_diary(
            user_id=Id(str(sample_user.user_id)),
            room_stay_id=Id(str(new_room_stay.room_stay_id)),
            city_id=Id(str(sample_city.city_id)),
            guest_house_id=Id(str(sample_guest_house.guest_house_id)),
            title="새 일기",
            content="새로운 일기 내용입니다.",
            mood=DiaryMood.HAPPY,
        )

        # Then
        assert diary is not None
        assert diary.diary_id is not None
        assert str(diary.user_id.value) == str(sample_user.user_id)
        assert str(diary.room_stay_id.value) == str(new_room_stay.room_stay_id)
        assert diary.title == "새 일기"
        assert diary.mood == DiaryMood.HAPPY

    async def test_create_diary_raises_error_when_diary_already_exists(
        self,
        diary_service: DiaryService,
        sample_user: UserModel,
        sample_room_stay: RoomStayModel,
        sample_city: CityModel,
        sample_guest_house: GuestHouseModel,
        sample_diary: DiaryModel,
    ):
        """이미 해당 체류에 일기가 존재하면 에러가 발생한다"""
        # Given/When/Then
        with pytest.raises(DuplicatedDiaryError):
            await diary_service.create_diary(
                user_id=Id(str(sample_user.user_id)),
                room_stay_id=Id(str(sample_room_stay.room_stay_id)),
                city_id=Id(str(sample_city.city_id)),
                guest_house_id=Id(str(sample_guest_house.guest_house_id)),
                title="중복 일기",
                content="중복 일기 내용입니다.",
                mood=DiaryMood.PEACEFUL,
            )


class TestDiaryServiceGetDiaryById:
    """DiaryService.get_diary_by_id() 통합 테스트"""

    async def test_get_diary_by_id_success(
        self,
        diary_service: DiaryService,
        sample_diary: DiaryModel,
    ):
        """일기 ID로 일기를 조회할 수 있다"""
        # When
        diary = await diary_service.get_diary_by_id(Id(str(sample_diary.diary_id)))

        # Then
        assert diary is not None
        assert str(diary.diary_id.value) == str(sample_diary.diary_id)
        assert diary.title == sample_diary.title

    async def test_get_diary_by_id_raises_error_when_not_found(
        self,
        diary_service: DiaryService,
    ):
        """일기를 찾을 수 없으면 에러가 발생한다"""
        # Given
        non_existent_id = Id()

        # When/Then
        with pytest.raises(NotFoundDiaryError):
            await diary_service.get_diary_by_id(non_existent_id)


class TestDiaryServiceGetDiaryByRoomStayId:
    """DiaryService.get_diary_by_room_stay_id() 통합 테스트"""

    async def test_get_diary_by_room_stay_id_success(
        self,
        diary_service: DiaryService,
        sample_diary: DiaryModel,
        sample_room_stay: RoomStayModel,
    ):
        """체류 ID로 일기를 조회할 수 있다"""
        # When
        diary = await diary_service.get_diary_by_room_stay_id(Id(str(sample_room_stay.room_stay_id)))

        # Then
        assert diary is not None
        assert str(diary.room_stay_id.value) == str(sample_room_stay.room_stay_id)

    async def test_get_diary_by_room_stay_id_returns_none_when_not_found(
        self,
        diary_service: DiaryService,
    ):
        """일기가 없으면 None을 반환한다"""
        # Given
        non_existent_id = Id()

        # When
        diary = await diary_service.get_diary_by_room_stay_id(non_existent_id)

        # Then
        assert diary is None


class TestDiaryServiceGetDiariesByUserId:
    """DiaryService.get_diaries_by_user_id() 통합 테스트"""

    async def test_get_diaries_by_user_id_success(
        self,
        diary_service: DiaryService,
        sample_user: UserModel,
        sample_diaries: list[DiaryModel],
    ):
        """사용자의 모든 일기를 조회할 수 있다"""
        # When
        diaries, total = await diary_service.get_diaries_by_user_id(Id(str(sample_user.user_id)))

        # Then
        assert len(diaries) == 5
        assert total == 5
        assert all(str(d.user_id.value) == str(sample_user.user_id) for d in diaries)

    async def test_get_diaries_by_user_id_with_pagination(
        self,
        diary_service: DiaryService,
        sample_user: UserModel,
        sample_diaries: list[DiaryModel],
    ):
        """pagination 파라미터로 일기 목록을 조회할 수 있다"""
        # When
        diaries, total = await diary_service.get_diaries_by_user_id(Id(str(sample_user.user_id)), limit=2, offset=0)

        # Then
        assert len(diaries) == 2
        assert total == 5

    async def test_get_diaries_by_user_id_returns_empty_list(
        self,
        diary_service: DiaryService,
    ):
        """일기가 없으면 빈 리스트를 반환한다"""
        # Given
        non_existent_user_id = Id()

        # When
        diaries, total = await diary_service.get_diaries_by_user_id(non_existent_user_id)

        # Then
        assert diaries == []
        assert total == 0


class TestDiaryServiceUpdateDiary:
    """DiaryService.update_diary() 통합 테스트"""

    async def test_update_diary_success(
        self,
        diary_service: DiaryService,
        sample_diary: DiaryModel,
    ):
        """일기를 성공적으로 수정할 수 있다"""
        # Given
        new_title = "수정된 제목"
        new_content = "수정된 내용입니다."
        new_mood = DiaryMood.HAPPY

        # When
        updated_diary = await diary_service.update_diary(
            diary_id=Id(str(sample_diary.diary_id)),
            title=new_title,
            content=new_content,
            mood=new_mood,
        )

        # Then
        assert updated_diary.title == "수정된 제목"
        assert updated_diary.content == "수정된 내용입니다."
        assert updated_diary.mood == DiaryMood.HAPPY

    async def test_update_diary_raises_error_when_not_found(
        self,
        diary_service: DiaryService,
    ):
        """일기를 찾을 수 없으면 에러가 발생한다"""
        # Given
        non_existent_id = Id()
        new_title = "수정된 제목"
        new_content = "수정된 내용입니다."
        new_mood = DiaryMood.HAPPY

        # When/Then
        with pytest.raises(NotFoundDiaryError):
            await diary_service.update_diary(
                diary_id=non_existent_id,
                title=new_title,
                content=new_content,
                mood=new_mood,
            )


class TestDiaryServiceDeleteDiary:
    """DiaryService.delete_diary() 통합 테스트"""

    async def test_delete_diary_success(
        self,
        diary_service: DiaryService,
        sample_diary: DiaryModel,
    ):
        """일기를 성공적으로 삭제할 수 있다 (soft delete)"""
        # When
        deleted_diary = await diary_service.delete_diary(Id(str(sample_diary.diary_id)))

        # Then
        assert deleted_diary.deleted_at is not None

        # 삭제 후 조회되지 않아야 함
        with pytest.raises(NotFoundDiaryError):
            await diary_service.get_diary_by_id(Id(str(sample_diary.diary_id)))

    async def test_delete_diary_raises_error_when_not_found(
        self,
        diary_service: DiaryService,
    ):
        """일기를 찾을 수 없으면 에러가 발생한다"""
        # Given
        non_existent_id = Id()

        # When/Then
        with pytest.raises(NotFoundDiaryError):
            await diary_service.delete_diary(non_existent_id)
