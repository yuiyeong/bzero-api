"""DiaryRepository 통합 테스트"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from bzero.domain.entities.diary import Diary
from bzero.domain.errors import NotFoundDiaryError
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
def diary_repository(test_session: AsyncSession) -> SqlAlchemyDiaryRepository:
    """DiaryRepository fixture를 생성합니다."""
    return SqlAlchemyDiaryRepository(test_session)


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
        # 각 일기마다 새로운 ticket과 room_stay 생성
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


class TestDiaryRepositoryCreate:
    """DiaryRepository.create() 메서드 테스트"""

    async def test_create_diary_success(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
        sample_user: UserModel,
        sample_room_stay: RoomStayModel,
        sample_city: CityModel,
        sample_guest_house: GuestHouseModel,
    ):
        """새로운 일기를 생성할 수 있어야 합니다."""
        # Given
        now = datetime.now()
        diary = Diary.create(
            user_id=Id(str(sample_user.user_id)),
            room_stay_id=Id(str(sample_room_stay.room_stay_id)),
            city_id=Id(str(sample_city.city_id)),
            guest_house_id=Id(str(sample_guest_house.guest_house_id)),
            title="새 일기",
            content="새로운 일기 내용입니다.",
            mood=DiaryMood.HAPPY,
            created_at=now,
            updated_at=now,
        )

        # When
        created = await diary_repository.create(diary)

        # Then
        assert created is not None
        assert str(created.diary_id.value) == str(diary.diary_id.value)
        assert str(created.user_id.value) == str(sample_user.user_id)
        assert str(created.room_stay_id.value) == str(sample_room_stay.room_stay_id)
        assert created.title == "새 일기"
        assert created.content == "새로운 일기 내용입니다."
        assert created.mood == DiaryMood.HAPPY


class TestDiaryRepositoryFindByDiaryId:
    """DiaryRepository.find_by_diary_id() 메서드 테스트"""

    async def test_find_by_diary_id_success(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
        sample_diary: DiaryModel,
    ):
        """ID로 일기를 조회할 수 있어야 합니다."""
        # When
        diary = await diary_repository.find_by_diary_id(Id(str(sample_diary.diary_id)))

        # Then
        assert diary is not None
        assert str(diary.diary_id.value) == str(sample_diary.diary_id)
        assert diary.title == sample_diary.title
        assert diary.content == sample_diary.content
        assert diary.mood.value == sample_diary.mood

    async def test_find_by_diary_id_returns_none_when_not_found(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
    ):
        """존재하지 않는 ID로 조회 시 None을 반환해야 합니다."""
        # Given
        non_existent_id = Id()

        # When
        diary = await diary_repository.find_by_diary_id(non_existent_id)

        # Then
        assert diary is None

    async def test_find_by_diary_id_soft_deleted_excluded(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
        sample_diary: DiaryModel,
        test_session: AsyncSession,
    ):
        """Soft delete된 일기는 조회되지 않아야 합니다."""
        # Given: 일기를 soft delete
        sample_diary.deleted_at = datetime.now()
        await test_session.flush()

        # When
        diary = await diary_repository.find_by_diary_id(Id(str(sample_diary.diary_id)))

        # Then
        assert diary is None


class TestDiaryRepositoryFindByRoomStayId:
    """DiaryRepository.find_by_room_stay_id() 메서드 테스트"""

    async def test_find_by_room_stay_id_success(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
        sample_diary: DiaryModel,
        sample_room_stay: RoomStayModel,
    ):
        """체류 ID로 일기를 조회할 수 있어야 합니다."""
        # When
        diary = await diary_repository.find_by_room_stay_id(Id(str(sample_room_stay.room_stay_id)))

        # Then
        assert diary is not None
        assert str(diary.room_stay_id.value) == str(sample_room_stay.room_stay_id)

    async def test_find_by_room_stay_id_returns_none_when_not_found(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
    ):
        """일기가 없으면 None을 반환해야 합니다."""
        # Given
        non_existent_id = Id()

        # When
        diary = await diary_repository.find_by_room_stay_id(non_existent_id)

        # Then
        assert diary is None

    async def test_find_by_room_stay_id_soft_deleted_excluded(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
        sample_diary: DiaryModel,
        sample_room_stay: RoomStayModel,
        test_session: AsyncSession,
    ):
        """Soft delete된 일기는 조회되지 않아야 합니다."""
        # Given
        sample_diary.deleted_at = datetime.now()
        await test_session.flush()

        # When
        diary = await diary_repository.find_by_room_stay_id(Id(str(sample_room_stay.room_stay_id)))

        # Then
        assert diary is None


class TestDiaryRepositoryFindAllByUserId:
    """DiaryRepository.find_all_by_user_id() 메서드 테스트"""

    async def test_find_all_by_user_id_success(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
        sample_user: UserModel,
        sample_diaries: list[DiaryModel],
    ):
        """사용자 ID로 일기 목록을 조회할 수 있어야 합니다."""
        # When
        diaries = await diary_repository.find_all_by_user_id(Id(str(sample_user.user_id)), limit=20, offset=0)

        # Then
        assert len(diaries) == 5
        assert all(str(d.user_id.value) == str(sample_user.user_id) for d in diaries)

    async def test_find_all_by_user_id_ordered_by_created_at_desc(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
        sample_user: UserModel,
        sample_diaries: list[DiaryModel],
    ):
        """일기 목록은 created_at 내림차순으로 정렬되어야 합니다."""
        # When
        diaries = await diary_repository.find_all_by_user_id(Id(str(sample_user.user_id)), limit=20, offset=0)

        # Then
        assert len(diaries) == 5
        for i in range(len(diaries) - 1):
            assert diaries[i].created_at >= diaries[i + 1].created_at

    async def test_find_all_by_user_id_with_pagination(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
        sample_user: UserModel,
        sample_diaries: list[DiaryModel],
    ):
        """pagination 파라미터로 일기 목록을 조회할 수 있어야 합니다."""
        # When
        diaries = await diary_repository.find_all_by_user_id(Id(str(sample_user.user_id)), limit=2, offset=0)

        # Then
        assert len(diaries) == 2

    async def test_find_all_by_user_id_with_offset(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
        sample_user: UserModel,
        sample_diaries: list[DiaryModel],
    ):
        """offset 파라미터로 시작 위치를 지정할 수 있어야 합니다."""
        # When
        diaries = await diary_repository.find_all_by_user_id(Id(str(sample_user.user_id)), limit=10, offset=2)

        # Then
        assert len(diaries) == 3

    async def test_find_all_by_user_id_soft_deleted_excluded(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
        sample_user: UserModel,
        sample_diaries: list[DiaryModel],
        test_session: AsyncSession,
    ):
        """Soft delete된 일기는 조회되지 않아야 합니다."""
        # Given: 첫 번째 일기를 soft delete
        sample_diaries[0].deleted_at = datetime.now()
        await test_session.flush()

        # When
        diaries = await diary_repository.find_all_by_user_id(Id(str(sample_user.user_id)), limit=20, offset=0)

        # Then
        assert len(diaries) == 4
        assert all(str(d.diary_id.value) != str(sample_diaries[0].diary_id) for d in diaries)

    async def test_find_all_by_user_id_empty(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
    ):
        """일기가 없으면 빈 리스트를 반환해야 합니다."""
        # Given
        non_existent_user_id = Id()

        # When
        diaries = await diary_repository.find_all_by_user_id(non_existent_user_id, limit=20, offset=0)

        # Then
        assert diaries == []


class TestDiaryRepositoryCountByUserId:
    """DiaryRepository.count_by_user_id() 메서드 테스트"""

    async def test_count_by_user_id_success(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
        sample_user: UserModel,
        sample_diaries: list[DiaryModel],
    ):
        """사용자 ID로 일기 개수를 조회할 수 있어야 합니다."""
        # When
        count = await diary_repository.count_by_user_id(Id(str(sample_user.user_id)))

        # Then
        assert count == 5

    async def test_count_by_user_id_soft_deleted_excluded(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
        sample_user: UserModel,
        sample_diaries: list[DiaryModel],
        test_session: AsyncSession,
    ):
        """Soft delete된 일기는 카운트에서 제외되어야 합니다."""
        # Given
        sample_diaries[0].deleted_at = datetime.now()
        await test_session.flush()

        # When
        count = await diary_repository.count_by_user_id(Id(str(sample_user.user_id)))

        # Then
        assert count == 4

    async def test_count_by_user_id_returns_zero_when_no_results(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
    ):
        """일기가 없으면 0을 반환해야 합니다."""
        # Given
        non_existent_user_id = Id()

        # When
        count = await diary_repository.count_by_user_id(non_existent_user_id)

        # Then
        assert count == 0


class TestDiaryRepositoryUpdate:
    """DiaryRepository.update() 메서드 테스트"""

    async def test_update_diary_success(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
        sample_diary: DiaryModel,
    ):
        """일기를 업데이트할 수 있어야 합니다."""
        # Given
        diary = await diary_repository.find_by_diary_id(Id(str(sample_diary.diary_id)))
        assert diary is not None

        new_title = "수정된 제목"
        new_content = "수정된 내용입니다."
        new_mood = DiaryMood.HAPPY
        updated_at = datetime.now()

        diary.update_content(
            title=new_title,
            content=new_content,
            mood=new_mood,
            updated_at=updated_at,
        )

        # When
        updated = await diary_repository.update(diary)

        # Then
        assert updated is not None
        assert updated.title == "수정된 제목"
        assert updated.content == "수정된 내용입니다."
        assert updated.mood == DiaryMood.HAPPY

    async def test_update_non_existent_diary_raises_error(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
        sample_user: UserModel,
        sample_city: CityModel,
        sample_guest_house: GuestHouseModel,
    ):
        """존재하지 않는 일기 업데이트 시 NotFoundDiaryError 발생."""
        # Given
        now = datetime.now()
        non_existent_diary = Diary(
            diary_id=Id(),  # 새로운 ID (DB에 없음)
            user_id=Id(str(sample_user.user_id)),
            room_stay_id=Id(),
            city_id=Id(str(sample_city.city_id)),
            guest_house_id=Id(str(sample_guest_house.guest_house_id)),
            title="제목",
            content="내용",
            mood=DiaryMood.PEACEFUL,
            created_at=now,
            updated_at=now,
        )

        # When/Then
        with pytest.raises(NotFoundDiaryError):
            await diary_repository.update(non_existent_diary)


class TestDiaryRepositoryExistsByRoomStayId:
    """DiaryRepository.exists_by_room_stay_id() 메서드 테스트"""

    async def test_exists_by_room_stay_id_returns_true_when_exists(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
        sample_diary: DiaryModel,
        sample_room_stay: RoomStayModel,
    ):
        """일기가 존재하면 True를 반환해야 합니다."""
        # When
        exists = await diary_repository.exists_by_room_stay_id(Id(str(sample_room_stay.room_stay_id)))

        # Then
        assert exists is True

    async def test_exists_by_room_stay_id_returns_false_when_not_exists(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
    ):
        """일기가 존재하지 않으면 False를 반환해야 합니다."""
        # Given
        non_existent_id = Id()

        # When
        exists = await diary_repository.exists_by_room_stay_id(non_existent_id)

        # Then
        assert exists is False

    async def test_exists_by_room_stay_id_soft_deleted_excluded(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
        sample_diary: DiaryModel,
        sample_room_stay: RoomStayModel,
        test_session: AsyncSession,
    ):
        """Soft delete된 일기는 존재하지 않는 것으로 처리되어야 합니다."""
        # Given
        sample_diary.deleted_at = datetime.now()
        await test_session.flush()

        # When
        exists = await diary_repository.exists_by_room_stay_id(Id(str(sample_room_stay.room_stay_id)))

        # Then
        assert exists is False
