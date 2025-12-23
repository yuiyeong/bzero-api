from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from uuid_utils import uuid7

from bzero.core.settings import get_settings
from bzero.domain.entities.diary import Diary
from bzero.domain.errors import InvalidDiaryContentError
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.diary import DiaryMood


class TestDiaryMood:
    """DiaryMood 값 객체 단위 테스트"""

    def test_diary_mood_values(self):
        """DiaryMood는 8개의 감정 상태를 가진다"""
        # Given/When/Then
        assert DiaryMood.HAPPY.value == "happy"
        assert DiaryMood.PEACEFUL.value == "peaceful"
        assert DiaryMood.GRATEFUL.value == "grateful"
        assert DiaryMood.REFLECTIVE.value == "reflective"
        assert DiaryMood.SAD.value == "sad"
        assert DiaryMood.ANXIOUS.value == "anxious"
        assert DiaryMood.HOPEFUL.value == "hopeful"
        assert DiaryMood.TIRED.value == "tired"

    def test_diary_mood_is_string_enum(self):
        """DiaryMood는 문자열 Enum이다"""
        # Given/When/Then
        assert isinstance(DiaryMood.HAPPY, str)
        assert DiaryMood.HAPPY == "happy"


class TestDiary:
    """Diary 엔티티 단위 테스트"""

    @pytest.fixture
    def tz(self) -> ZoneInfo:
        """Seoul timezone"""
        return get_settings().timezone

    def test_create_diary(self, tz: ZoneInfo):
        """일기를 생성할 수 있다"""
        # Given
        user_id = Id(uuid7())
        room_stay_id = Id(uuid7())
        city_id = Id(uuid7())
        guest_house_id = Id(uuid7())
        title = "오늘의 일기"
        content = "오늘 하루도 평화로웠다."
        mood = DiaryMood.PEACEFUL
        now = datetime.now(tz)

        # When
        diary = Diary.create(
            user_id=user_id,
            room_stay_id=room_stay_id,
            city_id=city_id,
            guest_house_id=guest_house_id,
            title=title,
            content=content,
            mood=mood,
            created_at=now,
            updated_at=now,
        )

        # Then
        assert diary.diary_id is not None
        assert diary.user_id == user_id
        assert diary.room_stay_id == room_stay_id
        assert diary.city_id == city_id
        assert diary.guest_house_id == guest_house_id
        assert diary.title == title
        assert diary.content == content
        assert diary.mood == mood
        assert diary.created_at == now
        assert diary.updated_at == now
        assert diary.deleted_at is None

    def test_create_diary_generates_id(self, tz: ZoneInfo):
        """일기 생성 시 diary_id가 자동 생성된다"""
        # Given
        now = datetime.now(tz)

        # When
        diary = Diary.create(
            user_id=Id(uuid7()),
            room_stay_id=Id(uuid7()),
            city_id=Id(uuid7()),
            guest_house_id=Id(uuid7()),
            title="오늘의 일기",
            content="오늘 하루도 평화로웠다.",
            mood=DiaryMood.HAPPY,
            created_at=now,
            updated_at=now,
        )

        # Then
        assert diary.diary_id is not None
        assert isinstance(diary.diary_id, Id)

    def test_create_diary_with_max_length(self, tz: ZoneInfo):
        """최대 길이의 제목과 긴 내용으로 일기를 생성할 수 있다"""
        # Given
        now = datetime.now(tz)
        title = "a" * 255  # MAX_TITLE_LENGTH = 255
        content = "b" * 1000  # 내용은 길이 제한 없음

        # When
        diary = Diary.create(
            user_id=Id(uuid7()),
            room_stay_id=Id(uuid7()),
            city_id=Id(uuid7()),
            guest_house_id=Id(uuid7()),
            title=title,
            content=content,
            mood=DiaryMood.HAPPY,
            created_at=now,
            updated_at=now,
        )

        # Then
        assert len(diary.title) == 255
        assert len(diary.content) == 1000

    def test_create_diary_with_empty_title_raises_error(self, tz: ZoneInfo):
        """빈 제목으로 일기를 생성하면 에러가 발생한다"""
        # Given
        now = datetime.now(tz)

        # When/Then
        with pytest.raises(InvalidDiaryContentError):
            Diary.create(
                user_id=Id(uuid7()),
                room_stay_id=Id(uuid7()),
                city_id=Id(uuid7()),
                guest_house_id=Id(uuid7()),
                title="",
                content="내용이 있어요",
                mood=DiaryMood.HAPPY,
                created_at=now,
                updated_at=now,
            )

    def test_create_diary_with_empty_content_raises_error(self, tz: ZoneInfo):
        """빈 내용으로 일기를 생성하면 에러가 발생한다"""
        # Given
        now = datetime.now(tz)

        # When/Then
        with pytest.raises(InvalidDiaryContentError):
            Diary.create(
                user_id=Id(uuid7()),
                room_stay_id=Id(uuid7()),
                city_id=Id(uuid7()),
                guest_house_id=Id(uuid7()),
                title="제목이 있어요",
                content="",
                mood=DiaryMood.HAPPY,
                created_at=now,
                updated_at=now,
            )

    def test_create_diary_with_too_long_title_raises_error(self, tz: ZoneInfo):
        """제목이 255자를 초과하면 에러가 발생한다"""
        # Given
        now = datetime.now(tz)

        # When/Then
        with pytest.raises(InvalidDiaryContentError):
            Diary.create(
                user_id=Id(uuid7()),
                room_stay_id=Id(uuid7()),
                city_id=Id(uuid7()),
                guest_house_id=Id(uuid7()),
                title="a" * 256,
                content="내용이 있어요",
                mood=DiaryMood.HAPPY,
                created_at=now,
                updated_at=now,
            )

    def test_update_content(self, tz: ZoneInfo):
        """일기 내용을 수정할 수 있다"""
        # Given
        now = datetime.now(tz)
        diary = Diary.create(
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
        new_title = "수정된 제목"
        new_content = "수정된 내용입니다."
        new_mood = DiaryMood.HAPPY
        update_time = datetime.now(tz)

        # When
        diary.update_content(
            title=new_title,
            content=new_content,
            mood=new_mood,
            updated_at=update_time,
        )

        # Then
        assert diary.title == new_title
        assert diary.content == new_content
        assert diary.mood == new_mood
        assert diary.updated_at == update_time

    def test_update_content_with_invalid_title_raises_error(self, tz: ZoneInfo):
        """수정 시 빈 제목은 에러가 발생한다"""
        # Given
        now = datetime.now(tz)
        diary = Diary.create(
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

        # When/Then
        with pytest.raises(InvalidDiaryContentError):
            diary.update_content(
                title="",
                content="수정된 내용입니다.",
                mood=DiaryMood.HAPPY,
                updated_at=datetime.now(tz),
            )

    def test_update_content_with_invalid_content_raises_error(self, tz: ZoneInfo):
        """수정 시 빈 내용은 에러가 발생한다"""
        # Given
        now = datetime.now(tz)
        diary = Diary.create(
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

        # When/Then
        with pytest.raises(InvalidDiaryContentError):
            diary.update_content(
                title="수정된 제목",
                content="",
                mood=DiaryMood.HAPPY,
                updated_at=datetime.now(tz),
            )

    def test_soft_delete(self, tz: ZoneInfo):
        """일기를 soft delete 처리할 수 있다"""
        # Given
        now = datetime.now(tz)
        diary = Diary.create(
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
        delete_time = datetime.now(tz)

        # When
        diary.soft_delete(deleted_at=delete_time)

        # Then
        assert diary.deleted_at == delete_time
        assert diary.updated_at == delete_time

    def test_diary_with_different_moods(self, tz: ZoneInfo):
        """다양한 감정 상태로 일기를 생성할 수 있다"""
        # Given
        now = datetime.now(tz)
        moods = [
            DiaryMood.HAPPY,
            DiaryMood.PEACEFUL,
            DiaryMood.GRATEFUL,
            DiaryMood.REFLECTIVE,
            DiaryMood.SAD,
            DiaryMood.ANXIOUS,
            DiaryMood.HOPEFUL,
            DiaryMood.TIRED,
        ]

        # When/Then
        for mood in moods:
            diary = Diary.create(
                user_id=Id(uuid7()),
                room_stay_id=Id(uuid7()),
                city_id=Id(uuid7()),
                guest_house_id=Id(uuid7()),
                title="오늘의 일기",
                content="오늘 하루도 평화로웠다.",
                mood=mood,
                created_at=now,
                updated_at=now,
            )
            assert diary.mood == mood
