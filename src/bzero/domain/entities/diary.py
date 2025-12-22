from dataclasses import dataclass
from datetime import datetime

from bzero.domain.errors import InvalidDiaryContentError
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.diary import DiaryMood


@dataclass
class Diary:
    """일기 엔티티.

    체류 중 작성하는 개인 일기입니다.
    체류당 1개의 일기만 작성 가능하며, 작성 시 50P를 획득합니다.

    Attributes:
        diary_id: 일기 고유 식별자 (UUID v7)
        user_id: 작성자 ID (FK)
        room_stay_id: 체류 ID (FK, UNIQUE - 체류당 1개만 허용)
        city_id: 도시 ID (FK, 비정규화)
        guest_house_id: 게스트하우스 ID (FK, 비정규화)
        title: 일기 제목 (1-255자)
        content: 일기 내용 (필수, 길이 제한 없음)
        mood: 감정 상태 (DiaryMood)
        created_at: 생성 시각
        updated_at: 수정 시각
        deleted_at: 삭제 시각 (soft delete)

    도메인 규칙:
        - 체류당 1개의 일기만 작성 가능 (room_stay_id UNIQUE)
        - 최초 작성 시에만 포인트 지급 (50P)
        - 수정/삭제는 언제든지 가능
        - 제목은 1-255자 제한, 내용은 길이 제한 없음
    """

    MAX_TITLE_LENGTH = 255

    diary_id: Id
    user_id: Id
    room_stay_id: Id
    city_id: Id
    guest_house_id: Id
    title: str
    content: str
    mood: DiaryMood
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    def __post_init__(self) -> None:
        """유효성 검사를 수행합니다."""

        # 제목 유효성 검사
        if not self.title or len(self.title) > self.MAX_TITLE_LENGTH:
            raise InvalidDiaryContentError

        # 내용 유효성 검사
        if not self.content:
            raise InvalidDiaryContentError

    def update_content(
        self,
        title: str,
        content: str,
        mood: DiaryMood,
        updated_at: datetime,
    ) -> None:
        """일기 내용을 수정합니다.

        Args:
            title: 새 일기 제목
            content: 새 일기 내용
            mood: 새 감정 상태
            updated_at: 수정 시각

        Raises:
            InvalidDiaryContentError: 제목 또는 내용이 유효하지 않은 경우
        """
        self._validate_title(title)
        self._validate_content(content)
        self.title = title
        self.content = content
        self.mood = mood
        self.updated_at = updated_at

    def soft_delete(self, deleted_at: datetime) -> None:
        """일기를 soft delete 처리합니다.

        Args:
            deleted_at: 삭제 시각
        """
        self.deleted_at = deleted_at
        self.updated_at = deleted_at

    @classmethod
    def create(
        cls,
        user_id: Id,
        room_stay_id: Id,
        city_id: Id,
        guest_house_id: Id,
        title: str,
        content: str,
        mood: DiaryMood,
        created_at: datetime,
        updated_at: datetime,
    ) -> "Diary":
        """새 일기 엔티티를 생성합니다.

        Args:
            user_id: 작성자 ID
            room_stay_id: 체류 ID
            city_id: 도시 ID
            guest_house_id: 게스트하우스 ID
            title: 일기 제목
            content: 일기 내용
            mood: 감정 상태
            created_at: 생성 시각
            updated_at: 수정 시각

        Returns:
            새로 생성된 Diary 엔티티 (ID 자동 생성)

        Raises:
            InvalidDiaryContentError: 제목 또는 내용이 유효하지 않은 경우
        """
        return cls(
            diary_id=Id(),
            user_id=user_id,
            room_stay_id=room_stay_id,
            city_id=city_id,
            guest_house_id=guest_house_id,
            title=title,
            content=content,
            mood=mood,
            created_at=created_at,
            updated_at=updated_at,
        )
