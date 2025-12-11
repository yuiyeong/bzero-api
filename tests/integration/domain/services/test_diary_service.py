"""DiaryService Integration Tests - 모든 메서드 테스트"""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bzero.domain.entities.diary import Diary
from bzero.domain.entities.ticket import Ticket
from bzero.domain.errors import DuplicatedDiaryError, NotFoundDiaryError
from bzero.domain.services.diary import DiaryService
from bzero.domain.value_objects import (
    AirshipSnapshot,
    CitySnapshot,
    DiaryContent,
    DiaryMood,
    Id,
    TicketStatus,
)
from bzero.infrastructure.repositories.diary import SqlAlchemyDiaryRepository
from bzero.infrastructure.repositories.ticket import SqlAlchemyTicketRepository


@pytest.fixture
def diary_service(test_session: AsyncSession) -> DiaryService:
    """DiaryService fixture를 생성합니다."""
    diary_repo = SqlAlchemyDiaryRepository(test_session)
    timezone = ZoneInfo("Asia/Seoul")
    return DiaryService(diary_repo, timezone)


@pytest.fixture
def ticket_repo(test_session: AsyncSession) -> SqlAlchemyTicketRepository:
    """TicketRepository fixture를 생성합니다."""
    return SqlAlchemyTicketRepository(test_session)


class TestDiaryServiceCalculateDiaryDate:
    """DiaryService.calculate_diary_date() 메서드 테스트"""

    def test_calculate_diary_date_without_ticket(self, diary_service: DiaryService):
        """완료된 티켓이 없으면 현재 날짜를 반환한다"""
        # Given: 티켓 없음
        ticket = None

        # When
        result = diary_service.calculate_diary_date(ticket)

        # Then: 오늘 날짜 반환
        assert result == date.today()

    async def test_calculate_diary_date_with_completed_ticket_same_day(
        self, diary_service: DiaryService, ticket_repo: SqlAlchemyTicketRepository
    ):
        """완료된 티켓이 있고 도착한 지 24시간 이내면 도착일 반환"""
        # Given: 오늘 도착한 티켓
        now = datetime.now(ZoneInfo("Asia/Seoul"))
        arrival_time = now - timedelta(hours=5)  # 5시간 전 도착
        ticket = Ticket(
            ticket_id=Id(),
            user_id=Id(),
            ticket_number="TEST-001",
            cost_points=100,
            status=TicketStatus.COMPLETED,
            departure_datetime=arrival_time - timedelta(hours=1),
            arrival_datetime=arrival_time,
            city_snapshot=CitySnapshot(
                city_id=Id(),
                name="세렌시아",
                theme="관계의 도시",
                image_url=None,
                description=None,
                base_cost_points=100,
                base_duration_hours=1,
            ),
            airship_snapshot=AirshipSnapshot(
                airship_id=Id(),
                name="기본 비행선",
                image_url=None,
                description=None,
                cost_factor=1.0,
                duration_factor=1.0,
            ),
            created_at=now,
            updated_at=now,
        )
        await ticket_repo.create(ticket)

        # When
        result = diary_service.calculate_diary_date(ticket)

        # Then: 도착일 반환
        assert result == arrival_time.date()

    async def test_calculate_diary_date_with_completed_ticket_next_day(
        self, diary_service: DiaryService, ticket_repo: SqlAlchemyTicketRepository
    ):
        """완료된 티켓이 있고 도착한 지 24시간 이상이면 경과 일수만큼 더한 날짜 반환"""
        # Given: 2일 전 도착한 티켓
        now = datetime.now(ZoneInfo("Asia/Seoul"))
        arrival_time = now - timedelta(hours=50)  # 50시간 전 도착 (2일 경과)
        ticket = Ticket(
            ticket_id=Id(),
            user_id=Id(),
            ticket_number="TEST-002",
            cost_points=100,
            status=TicketStatus.COMPLETED,
            departure_datetime=arrival_time - timedelta(hours=1),
            arrival_datetime=arrival_time,
            city_snapshot=CitySnapshot(
                city_id=Id(),
                name="세렌시아",
                theme="관계의 도시",
                image_url=None,
                description=None,
                base_cost_points=100,
                base_duration_hours=1,
            ),
            airship_snapshot=AirshipSnapshot(
                airship_id=Id(),
                name="기본 비행선",
                image_url=None,
                description=None,
                cost_factor=1.0,
                duration_factor=1.0,
            ),
            created_at=now,
            updated_at=now,
        )
        await ticket_repo.create(ticket)

        # When
        result = diary_service.calculate_diary_date(ticket)

        # Then: 도착일 + 2일
        expected = arrival_time.date() + timedelta(days=2)
        assert result == expected


class TestDiaryServiceCreateDiary:
    """DiaryService.create_diary() 메서드 테스트"""

    async def test_create_diary_success(self, diary_service: DiaryService):
        """일기를 성공적으로 생성할 수 있다"""
        # Given
        user_id = Id()
        content = DiaryContent("오늘은 좋은 하루였다.")
        mood = DiaryMood("😊")
        diary_date = date(2025, 12, 10)

        # When
        diary = await diary_service.create_diary(
            user_id=user_id,
            content=content,
            mood=mood,
            diary_date=diary_date,
        )

        # Then
        assert diary is not None
        assert diary.user_id == user_id
        assert diary.content == content
        assert diary.mood == mood
        assert diary.diary_date == diary_date
        assert diary.has_earned_points is False

    async def test_create_diary_with_title_and_city(self, diary_service: DiaryService):
        """제목과 도시 ID를 포함한 일기를 생성할 수 있다"""
        # Given
        user_id = Id()
        content = DiaryContent("좋은 하루")
        mood = DiaryMood("😊")
        diary_date = date(2025, 12, 10)
        title = "행복한 하루"
        city_id = Id()

        # When
        diary = await diary_service.create_diary(
            user_id=user_id,
            content=content,
            mood=mood,
            diary_date=diary_date,
            title=title,
            city_id=city_id,
        )

        # Then
        assert diary.title == title
        assert diary.city_id == city_id

    async def test_create_diary_duplicate_error(self, diary_service: DiaryService):
        """같은 날짜에 일기를 중복 생성하면 에러 발생"""
        # Given: 일기를 이미 생성
        user_id = Id()
        diary_date = date(2025, 12, 10)
        await diary_service.create_diary(
            user_id=user_id,
            content=DiaryContent("첫 번째 일기"),
            mood=DiaryMood("😊"),
            diary_date=diary_date,
        )

        # When & Then: 같은 날짜에 다시 생성하면 에러
        with pytest.raises(DuplicatedDiaryError):
            await diary_service.create_diary(
                user_id=user_id,
                content=DiaryContent("두 번째 일기"),
                mood=DiaryMood("😊"),
                diary_date=diary_date,
            )


class TestDiaryServiceGetDiaryById:
    """DiaryService.get_diary_by_id() 메서드 테스트"""

    async def test_get_diary_by_id_success(self, diary_service: DiaryService):
        """일기를 ID로 조회할 수 있다"""
        # Given: 일기 생성
        user_id = Id()
        created_diary = await diary_service.create_diary(
            user_id=user_id,
            content=DiaryContent("테스트 일기"),
            mood=DiaryMood("😊"),
            diary_date=date(2025, 12, 10),
        )

        # When: ID로 조회
        found_diary = await diary_service.get_diary_by_id(created_diary.diary_id)

        # Then
        assert found_diary is not None
        assert found_diary.diary_id == created_diary.diary_id
        assert found_diary.content == created_diary.content

    async def test_get_diary_by_id_not_found(self, diary_service: DiaryService):
        """존재하지 않는 ID로 조회하면 NotFoundDiaryError 발생"""
        # Given: 존재하지 않는 ID
        non_existent_id = Id()

        # When & Then
        with pytest.raises(NotFoundDiaryError):
            await diary_service.get_diary_by_id(non_existent_id)


class TestDiaryServiceGetDiaryByUserAndDate:
    """DiaryService.get_diary_by_user_and_date() 메서드 테스트"""

    async def test_get_diary_by_user_and_date_success(self, diary_service: DiaryService):
        """사용자 ID와 날짜로 일기를 조회할 수 있다"""
        # Given: 일기 생성
        user_id = Id()
        diary_date = date(2025, 12, 10)
        created_diary = await diary_service.create_diary(
            user_id=user_id,
            content=DiaryContent("테스트 일기"),
            mood=DiaryMood("😊"),
            diary_date=diary_date,
        )

        # When: 사용자 ID와 날짜로 조회
        found_diary = await diary_service.get_diary_by_user_and_date(user_id, diary_date)

        # Then
        assert found_diary is not None
        assert found_diary.diary_id == created_diary.diary_id

    async def test_get_diary_by_user_and_date_not_found(self, diary_service: DiaryService):
        """존재하지 않는 사용자/날짜로 조회하면 None 반환"""
        # Given: 존재하지 않는 사용자 ID와 날짜
        non_existent_user_id = Id()
        non_existent_date = date(2025, 1, 1)

        # When
        found_diary = await diary_service.get_diary_by_user_and_date(non_existent_user_id, non_existent_date)

        # Then
        assert found_diary is None


class TestDiaryServiceGetDiariesByUser:
    """DiaryService.get_diaries_by_user() 메서드 테스트"""

    async def test_get_diaries_by_user_success(self, diary_service: DiaryService):
        """사용자의 일기 목록을 조회할 수 있다"""
        # Given: 같은 사용자의 일기 3개 생성
        user_id = Id()
        for i in range(3):
            await diary_service.create_diary(
                user_id=user_id,
                content=DiaryContent(f"일기 {i+1}"),
                mood=DiaryMood("😊"),
                diary_date=date(2025, 12, 10 + i),
            )

        # When: 일기 목록 조회
        diaries, total = await diary_service.get_diaries_by_user(user_id)

        # Then
        assert len(diaries) == 3
        assert total == 3
        # 최신순 정렬 확인
        assert diaries[0].diary_date > diaries[1].diary_date
        assert diaries[1].diary_date > diaries[2].diary_date

    async def test_get_diaries_by_user_with_pagination(self, diary_service: DiaryService):
        """페이지네이션이 정상 작동한다"""
        # Given: 5개의 일기 생성
        user_id = Id()
        for i in range(5):
            await diary_service.create_diary(
                user_id=user_id,
                content=DiaryContent(f"일기 {i+1}"),
                mood=DiaryMood("😊"),
                diary_date=date(2025, 12, 10 + i),
            )

        # When: offset=1, limit=2로 조회
        diaries, total = await diary_service.get_diaries_by_user(user_id, offset=1, limit=2)

        # Then
        assert len(diaries) == 2
        assert total == 5

    async def test_get_diaries_by_user_empty(self, diary_service: DiaryService):
        """일기가 없는 사용자는 빈 목록을 반환한다"""
        # Given: 일기가 없는 사용자
        user_id = Id()

        # When
        diaries, total = await diary_service.get_diaries_by_user(user_id)

        # Then
        assert diaries == []
        assert total == 0


class TestDiaryServiceMarkPointsEarned:
    """DiaryService.mark_points_earned() 메서드 테스트"""

    async def test_mark_points_earned_success(self, diary_service: DiaryService):
        """포인트 지급 완료 표시를 할 수 있다"""
        # Given: 일기 생성
        user_id = Id()
        diary = await diary_service.create_diary(
            user_id=user_id,
            content=DiaryContent("테스트 일기"),
            mood=DiaryMood("😊"),
            diary_date=date(2025, 12, 10),
        )
        assert diary.has_earned_points is False

        # When: 포인트 지급 완료 표시
        updated_diary = await diary_service.mark_points_earned(diary)

        # Then
        assert updated_diary.has_earned_points is True

    async def test_mark_points_earned_persists(self, diary_service: DiaryService):
        """포인트 지급 완료 표시가 DB에 저장된다"""
        # Given: 일기 생성 및 포인트 지급 완료
        user_id = Id()
        diary = await diary_service.create_diary(
            user_id=user_id,
            content=DiaryContent("테스트 일기"),
            mood=DiaryMood("😊"),
            diary_date=date(2025, 12, 10),
        )
        updated_diary = await diary_service.mark_points_earned(diary)

        # When: 다시 조회
        found_diary = await diary_service.get_diary_by_id(updated_diary.diary_id)

        # Then: 포인트 지급 완료 상태가 유지됨
        assert found_diary.has_earned_points is True
