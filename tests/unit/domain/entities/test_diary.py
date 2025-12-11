"""Diary 엔티티 단위 테스트"""

from datetime import date, datetime

from bzero.domain.entities.diary import Diary
from bzero.domain.value_objects import DiaryContent, DiaryMood, Id


class TestDiary:
    """Diary 엔티티 테스트"""

    def test_create_diary(self):
        """일기를 생성할 수 있다"""
        # Given
        user_id = Id()
        content = DiaryContent("오늘은 좋은 하루였다.")
        mood = DiaryMood("😊")
        diary_date = date(2025, 12, 10)
        now = datetime.now()

        # When
        diary = Diary.create(
            user_id=user_id,
            content=content,
            mood=mood,
            diary_date=diary_date,
            created_at=now,
            updated_at=now,
        )

        # Then
        assert diary.diary_id is not None
        assert diary.user_id == user_id
        assert diary.content == content
        assert diary.mood == mood
        assert diary.diary_date == diary_date
        assert diary.title is None
        assert diary.city_id is None
        assert diary.has_earned_points is False
        assert diary.deleted_at is None

    def test_create_diary_with_optional_fields(self):
        """제목과 도시 ID를 포함한 일기를 생성할 수 있다"""
        # Given
        user_id = Id()
        content = DiaryContent("좋은 하루였다.")
        mood = DiaryMood("😊")
        diary_date = date(2025, 12, 10)
        title = "행복한 하루"
        city_id = Id()
        now = datetime.now()

        # When
        diary = Diary.create(
            user_id=user_id,
            content=content,
            mood=mood,
            diary_date=diary_date,
            title=title,
            city_id=city_id,
            created_at=now,
            updated_at=now,
        )

        # Then
        assert diary.title == title
        assert diary.city_id == city_id

    def test_mark_points_earned(self):
        """포인트 지급 완료 표시를 할 수 있다"""
        # Given
        diary = Diary.create(
            user_id=Id(),
            content=DiaryContent("테스트"),
            mood=DiaryMood("😊"),
            diary_date=date.today(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert diary.has_earned_points is False

        # When
        diary.mark_points_earned()

        # Then
        assert diary.has_earned_points is True
