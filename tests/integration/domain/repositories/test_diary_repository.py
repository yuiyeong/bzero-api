"""DiaryRepository Integration Tests."""

from datetime import date, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bzero.domain.entities.diary import Diary
from bzero.domain.value_objects import DiaryContent, DiaryMood, Id
from bzero.infrastructure.repositories.diary import SqlAlchemyDiaryRepository


@pytest.fixture
def diary_repository(test_session: AsyncSession) -> SqlAlchemyDiaryRepository:
    """DiaryRepository fixture를 생성합니다."""
    return SqlAlchemyDiaryRepository(test_session)


@pytest.fixture
def sample_diary() -> Diary:
    """테스트용 샘플 일기를 생성합니다."""
    return Diary.create(
        user_id=Id(),
        content=DiaryContent("오늘은 좋은 하루였다."),
        mood=DiaryMood("😊"),
        diary_date=date(2025, 12, 10),
        title="행복한 하루",
        city_id=Id(),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


class TestDiaryRepositorySave:
    """DiaryRepository.save() 메서드 테스트."""

    async def test_save_new_diary(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
        sample_diary: Diary,
    ):
        """새 일기를 저장할 수 있어야 합니다."""
        # When: 일기를 저장
        saved_diary = await diary_repository.save(sample_diary)

        # Then: 저장된 일기가 반환됨
        assert saved_diary is not None
        assert str(saved_diary.diary_id.value) == str(sample_diary.diary_id.value)
        assert saved_diary.content == sample_diary.content
        assert saved_diary.mood == sample_diary.mood
        assert saved_diary.diary_date == sample_diary.diary_date

    async def test_save_persists_to_database(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
        sample_diary: Diary,
    ):
        """저장된 일기가 데이터베이스에 저장되어야 합니다."""
        # Given: 일기를 저장
        saved_diary = await diary_repository.save(sample_diary)

        # When: 저장된 일기를 ID로 조회
        found_diary = await diary_repository.find_by_id(saved_diary.diary_id)

        # Then: 동일한 일기가 조회됨
        assert found_diary is not None
        assert found_diary.diary_id == saved_diary.diary_id
        assert found_diary.content == saved_diary.content

    async def test_update_existing_diary(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
        sample_diary: Diary,
    ):
        """기존 일기를 업데이트할 수 있어야 합니다."""
        # Given: 일기를 저장
        saved_diary = await diary_repository.save(sample_diary)

        # When: 일기 내용 수정 후 저장
        saved_diary.mark_points_earned()
        updated_diary = await diary_repository.save(saved_diary)

        # Then: 업데이트된 내용이 반영됨
        found_diary = await diary_repository.find_by_id(updated_diary.diary_id)
        assert found_diary is not None
        assert found_diary.has_earned_points is True


class TestDiaryRepositoryFindById:
    """DiaryRepository.find_by_id() 메서드 테스트."""

    async def test_find_by_id_success(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
        sample_diary: Diary,
    ):
        """존재하는 일기를 ID로 조회할 수 있어야 합니다."""
        # Given: 일기를 저장
        saved_diary = await diary_repository.save(sample_diary)

        # When: 일기 ID로 조회
        found_diary = await diary_repository.find_by_id(saved_diary.diary_id)

        # Then: 일기가 조회됨
        assert found_diary is not None
        assert found_diary.diary_id == saved_diary.diary_id
        assert found_diary.content == saved_diary.content

    async def test_find_by_id_not_found(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
    ):
        """존재하지 않는 일기 ID로 조회하면 None을 반환해야 합니다."""
        # Given: 존재하지 않는 일기 ID
        non_existent_id = Id()

        # When: 조회
        found_diary = await diary_repository.find_by_id(non_existent_id)

        # Then: None 반환
        assert found_diary is None


class TestDiaryRepositoryFindByUserAndDate:
    """DiaryRepository.find_by_user_and_date() 메서드 테스트."""

    async def test_find_by_user_and_date_success(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
        sample_diary: Diary,
    ):
        """사용자 ID와 날짜로 일기를 조회할 수 있어야 합니다."""
        # Given: 일기를 저장
        saved_diary = await diary_repository.save(sample_diary)

        # When: 사용자 ID와 날짜로 조회
        found_diary = await diary_repository.find_by_user_and_date(
            saved_diary.user_id, saved_diary.diary_date
        )

        # Then: 일기가 조회됨
        assert found_diary is not None
        assert found_diary.diary_id == saved_diary.diary_id

    async def test_find_by_user_and_date_not_found(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
    ):
        """존재하지 않는 사용자/날짜로 조회하면 None을 반환해야 합니다."""
        # Given: 존재하지 않는 사용자 ID와 날짜
        non_existent_user_id = Id()
        non_existent_date = date(2025, 1, 1)

        # When: 조회
        found_diary = await diary_repository.find_by_user_and_date(
            non_existent_user_id, non_existent_date
        )

        # Then: None 반환
        assert found_diary is None


class TestDiaryRepositoryFindByUserId:
    """DiaryRepository.find_by_user_id() 메서드 테스트."""

    async def test_find_by_user_id_success(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
    ):
        """사용자 ID로 일기 목록을 조회할 수 있어야 합니다."""
        # Given: 같은 사용자의 일기 3개 저장
        user_id = Id()
        for i in range(3):
            diary = Diary.create(
                user_id=user_id,
                content=DiaryContent(f"일기 {i+1}"),
                mood=DiaryMood("😊"),
                diary_date=date(2025, 12, 10 + i),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            await diary_repository.save(diary)

        # When: 사용자 ID로 조회
        diaries = await diary_repository.find_by_user_id(user_id)

        # Then: 3개의 일기가 조회됨 (최신순 정렬)
        assert len(diaries) == 3
        assert diaries[0].diary_date > diaries[1].diary_date
        assert diaries[1].diary_date > diaries[2].diary_date

    async def test_find_by_user_id_with_pagination(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
    ):
        """페이지네이션이 정상 작동해야 합니다."""
        # Given: 같은 사용자의 일기 5개 저장
        user_id = Id()
        for i in range(5):
            diary = Diary.create(
                user_id=user_id,
                content=DiaryContent(f"일기 {i+1}"),
                mood=DiaryMood("😊"),
                diary_date=date(2025, 12, 10 + i),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            await diary_repository.save(diary)

        # When: offset=1, limit=2로 조회
        diaries = await diary_repository.find_by_user_id(user_id, offset=1, limit=2)

        # Then: 2개의 일기가 조회됨
        assert len(diaries) == 2

    async def test_find_by_user_id_empty(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
    ):
        """일기가 없는 사용자는 빈 목록을 반환해야 합니다."""
        # Given: 일기가 없는 사용자
        user_id = Id()

        # When: 조회
        diaries = await diary_repository.find_by_user_id(user_id)

        # Then: 빈 목록 반환
        assert diaries == []


class TestDiaryRepositoryCountByUserId:
    """DiaryRepository.count_by_user_id() 메서드 테스트."""

    async def test_count_by_user_id(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
    ):
        """사용자의 일기 개수를 정확히 카운트해야 합니다."""
        # Given: 같은 사용자의 일기 3개 저장
        user_id = Id()
        for i in range(3):
            diary = Diary.create(
                user_id=user_id,
                content=DiaryContent(f"일기 {i+1}"),
                mood=DiaryMood("😊"),
                diary_date=date(2025, 12, 10 + i),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            await diary_repository.save(diary)

        # When: 사용자 ID로 카운트
        count = await diary_repository.count_by_user_id(user_id)

        # Then: 3이 반환됨
        assert count == 3

    async def test_count_by_user_id_zero(
        self,
        diary_repository: SqlAlchemyDiaryRepository,
    ):
        """일기가 없는 사용자는 0을 반환해야 합니다."""
        # Given: 일기가 없는 사용자
        user_id = Id()

        # When: 카운트
        count = await diary_repository.count_by_user_id(user_id)

        # Then: 0 반환
        assert count == 0
