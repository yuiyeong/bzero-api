from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from zoneinfo import ZoneInfo

import pytest
from uuid_utils import uuid7

from bzero.domain.entities.diary import Diary
from bzero.domain.errors import DuplicatedDiaryError, NotFoundDiaryError
from bzero.domain.repositories.diary import DiaryRepository
from bzero.domain.services.diary import DiaryService
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.diary import DiaryMood


@pytest.fixture
def mock_diary_repository() -> MagicMock:
    """Mock DiaryRepository"""
    return MagicMock(spec=DiaryRepository)


@pytest.fixture
def timezone() -> ZoneInfo:
    """Seoul timezone"""
    return ZoneInfo("Asia/Seoul")


@pytest.fixture
def diary_service(mock_diary_repository: MagicMock, timezone: ZoneInfo) -> DiaryService:
    """DiaryService with mocked repository"""
    return DiaryService(mock_diary_repository, timezone)


@pytest.fixture
def sample_diary(timezone: ZoneInfo) -> Diary:
    """샘플 일기"""
    now = datetime.now(timezone)
    return Diary.create(
        user_id=Id(uuid7()),
        room_stay_id=Id(uuid7()),
        city_id=Id(uuid7()),
        guest_house_id=Id(uuid7()),
        title="오늘의 일기",
        content="오늘 하루도 평화로웠다.",
        mood=DiaryMood.PEACEFUL,
        created_at=now,
        updated_at=now,
    )


class TestDiaryServiceCreateDiary:
    """create_diary 메서드 테스트"""

    async def test_create_diary_success(
        self,
        diary_service: DiaryService,
        mock_diary_repository: MagicMock,
    ):
        """일기를 성공적으로 생성할 수 있다"""
        # Given
        user_id = Id(uuid7())
        room_stay_id = Id(uuid7())
        city_id = Id(uuid7())
        guest_house_id = Id(uuid7())
        title = "오늘의 일기"
        content = "오늘 하루도 평화로웠다."
        mood = DiaryMood.PEACEFUL

        mock_diary_repository.exists_by_room_stay_id = AsyncMock(return_value=False)

        async def mock_create(diary: Diary) -> Diary:
            return diary

        mock_diary_repository.create = AsyncMock(side_effect=mock_create)

        # When
        diary = await diary_service.create_diary(
            user_id=user_id,
            room_stay_id=room_stay_id,
            city_id=city_id,
            guest_house_id=guest_house_id,
            title=title,
            content=content,
            mood=mood,
        )

        # Then
        assert diary.user_id == user_id
        assert diary.room_stay_id == room_stay_id
        assert diary.city_id == city_id
        assert diary.guest_house_id == guest_house_id
        assert diary.title == title
        assert diary.content == content
        assert diary.mood == mood
        mock_diary_repository.exists_by_room_stay_id.assert_called_once_with(room_stay_id)
        mock_diary_repository.create.assert_called_once()

    async def test_create_diary_raises_error_when_diary_already_exists(
        self,
        diary_service: DiaryService,
        mock_diary_repository: MagicMock,
    ):
        """이미 해당 체류에 일기가 존재하면 에러가 발생한다"""
        # Given
        user_id = Id(uuid7())
        room_stay_id = Id(uuid7())
        city_id = Id(uuid7())
        guest_house_id = Id(uuid7())
        title = "오늘의 일기"
        content = "오늘 하루도 평화로웠다."
        mood = DiaryMood.PEACEFUL

        mock_diary_repository.exists_by_room_stay_id = AsyncMock(return_value=True)

        # When/Then
        with pytest.raises(DuplicatedDiaryError):
            await diary_service.create_diary(
                user_id=user_id,
                room_stay_id=room_stay_id,
                city_id=city_id,
                guest_house_id=guest_house_id,
                title=title,
                content=content,
                mood=mood,
            )


class TestDiaryServiceGetDiaryById:
    """get_diary_by_id 메서드 테스트"""

    async def test_get_diary_by_id_success(
        self,
        diary_service: DiaryService,
        mock_diary_repository: MagicMock,
        sample_diary: Diary,
    ):
        """일기 ID로 일기를 조회할 수 있다"""
        # Given
        mock_diary_repository.find_by_diary_id = AsyncMock(return_value=sample_diary)

        # When
        diary = await diary_service.get_diary_by_id(sample_diary.diary_id)

        # Then
        assert diary.diary_id == sample_diary.diary_id
        mock_diary_repository.find_by_diary_id.assert_called_once_with(sample_diary.diary_id)

    async def test_get_diary_by_id_raises_error_when_not_found(
        self,
        diary_service: DiaryService,
        mock_diary_repository: MagicMock,
    ):
        """일기를 찾을 수 없으면 에러가 발생한다"""
        # Given
        diary_id = Id(uuid7())
        mock_diary_repository.find_by_diary_id = AsyncMock(return_value=None)

        # When/Then
        with pytest.raises(NotFoundDiaryError):
            await diary_service.get_diary_by_id(diary_id)


class TestDiaryServiceGetDiaryByRoomStayId:
    """get_diary_by_room_stay_id 메서드 테스트"""

    async def test_get_diary_by_room_stay_id_success(
        self,
        diary_service: DiaryService,
        mock_diary_repository: MagicMock,
        sample_diary: Diary,
    ):
        """체류 ID로 일기를 조회할 수 있다"""
        # Given
        mock_diary_repository.find_by_room_stay_id = AsyncMock(return_value=sample_diary)

        # When
        diary = await diary_service.get_diary_by_room_stay_id(sample_diary.room_stay_id)

        # Then
        assert diary is not None
        assert diary.room_stay_id == sample_diary.room_stay_id
        mock_diary_repository.find_by_room_stay_id.assert_called_once_with(sample_diary.room_stay_id)

    async def test_get_diary_by_room_stay_id_returns_none_when_not_found(
        self,
        diary_service: DiaryService,
        mock_diary_repository: MagicMock,
    ):
        """일기가 없으면 None을 반환한다"""
        # Given
        room_stay_id = Id(uuid7())
        mock_diary_repository.find_by_room_stay_id = AsyncMock(return_value=None)

        # When
        diary = await diary_service.get_diary_by_room_stay_id(room_stay_id)

        # Then
        assert diary is None


class TestDiaryServiceGetDiariesByUserId:
    """get_diaries_by_user_id 메서드 테스트"""

    async def test_get_diaries_by_user_id_success(
        self,
        diary_service: DiaryService,
        mock_diary_repository: MagicMock,
        sample_diary: Diary,
    ):
        """사용자의 모든 일기를 조회할 수 있다"""
        # Given
        mock_diary_repository.find_all_by_user_id = AsyncMock(return_value=[sample_diary])
        mock_diary_repository.count_by_user_id = AsyncMock(return_value=1)

        # When
        diaries, total = await diary_service.get_diaries_by_user_id(sample_diary.user_id)

        # Then
        assert len(diaries) == 1
        assert total == 1
        assert diaries[0].user_id == sample_diary.user_id
        mock_diary_repository.find_all_by_user_id.assert_called_once_with(
            user_id=sample_diary.user_id, limit=20, offset=0
        )
        mock_diary_repository.count_by_user_id.assert_called_once_with(sample_diary.user_id)

    async def test_get_diaries_by_user_id_with_pagination(
        self,
        diary_service: DiaryService,
        mock_diary_repository: MagicMock,
    ):
        """pagination 파라미터로 일기 목록을 조회할 수 있다"""
        # Given
        user_id = Id(uuid7())
        mock_diary_repository.find_all_by_user_id = AsyncMock(return_value=[])
        mock_diary_repository.count_by_user_id = AsyncMock(return_value=50)

        # When
        diaries, total = await diary_service.get_diaries_by_user_id(user_id=user_id, limit=10, offset=20)

        # Then
        assert len(diaries) == 0
        assert total == 50
        mock_diary_repository.find_all_by_user_id.assert_called_once_with(user_id=user_id, limit=10, offset=20)

    async def test_get_diaries_by_user_id_returns_empty_list(
        self,
        diary_service: DiaryService,
        mock_diary_repository: MagicMock,
    ):
        """일기가 없으면 빈 리스트를 반환한다"""
        # Given
        user_id = Id(uuid7())
        mock_diary_repository.find_all_by_user_id = AsyncMock(return_value=[])
        mock_diary_repository.count_by_user_id = AsyncMock(return_value=0)

        # When
        diaries, total = await diary_service.get_diaries_by_user_id(user_id)

        # Then
        assert diaries == []
        assert total == 0


class TestDiaryServiceUpdateDiary:
    """update_diary 메서드 테스트"""

    async def test_update_diary_success(
        self,
        diary_service: DiaryService,
        mock_diary_repository: MagicMock,
        sample_diary: Diary,
    ):
        """일기를 성공적으로 수정할 수 있다"""
        # Given
        new_title = "수정된 제목"
        new_content = "수정된 내용입니다."
        new_mood = DiaryMood.HAPPY
        mock_diary_repository.find_by_diary_id = AsyncMock(return_value=sample_diary)
        mock_diary_repository.update = AsyncMock(return_value=sample_diary)

        # When
        updated_diary = await diary_service.update_diary(
            diary_id=sample_diary.diary_id,
            title=new_title,
            content=new_content,
            mood=new_mood,
        )

        # Then
        assert updated_diary.title == new_title
        assert updated_diary.content == new_content
        assert updated_diary.mood == new_mood
        mock_diary_repository.find_by_diary_id.assert_called_once_with(sample_diary.diary_id)
        mock_diary_repository.update.assert_called_once()

    async def test_update_diary_raises_error_when_not_found(
        self,
        diary_service: DiaryService,
        mock_diary_repository: MagicMock,
    ):
        """일기를 찾을 수 없으면 에러가 발생한다"""
        # Given
        diary_id = Id(uuid7())
        new_title = "수정된 제목"
        new_content = "수정된 내용입니다."
        new_mood = DiaryMood.HAPPY
        mock_diary_repository.find_by_diary_id = AsyncMock(return_value=None)

        # When/Then
        with pytest.raises(NotFoundDiaryError):
            await diary_service.update_diary(
                diary_id=diary_id,
                title=new_title,
                content=new_content,
                mood=new_mood,
            )


class TestDiaryServiceDeleteDiary:
    """delete_diary 메서드 테스트"""

    async def test_delete_diary_success(
        self,
        diary_service: DiaryService,
        mock_diary_repository: MagicMock,
        sample_diary: Diary,
    ):
        """일기를 성공적으로 삭제할 수 있다 (soft delete)"""
        # Given
        mock_diary_repository.find_by_diary_id = AsyncMock(return_value=sample_diary)
        mock_diary_repository.update = AsyncMock(return_value=sample_diary)

        # When
        deleted_diary = await diary_service.delete_diary(sample_diary.diary_id)

        # Then
        assert deleted_diary.deleted_at is not None
        mock_diary_repository.find_by_diary_id.assert_called_once_with(sample_diary.diary_id)
        mock_diary_repository.update.assert_called_once()

    async def test_delete_diary_raises_error_when_not_found(
        self,
        diary_service: DiaryService,
        mock_diary_repository: MagicMock,
    ):
        """일기를 찾을 수 없으면 에러가 발생한다"""
        # Given
        diary_id = Id(uuid7())
        mock_diary_repository.find_by_diary_id = AsyncMock(return_value=None)

        # When/Then
        with pytest.raises(NotFoundDiaryError):
            await diary_service.delete_diary(diary_id)
