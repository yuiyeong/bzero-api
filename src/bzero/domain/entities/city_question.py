from dataclasses import dataclass
from datetime import datetime

from bzero.domain.errors import InvalidCityQuestionError
from bzero.domain.value_objects import Id


@dataclass
class CityQuestion:
    """도시별 질문 엔티티.

    각 도시에 속한 사전 정의된 질문입니다.
    사용자는 체류 중 해당 도시의 질문에 답변할 수 있습니다.

    Attributes:
        city_question_id: 질문 고유 식별자 (UUID v7)
        city_id: 도시 ID (FK)
        question: 질문 내용
        display_order: 표시 순서 (1부터 시작)
        is_active: 활성화 여부
        created_at: 생성 시각
        updated_at: 수정 시각
        deleted_at: 삭제 시각 (soft delete)

    도메인 규칙:
        - 도시별 display_order는 유니크 (deleted_at IS NULL 조건)
    """

    city_question_id: Id
    city_id: Id
    question: str
    display_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    def __post_init__(self) -> None:
        """유효성 검사를 수행합니다."""
        if not self.question:
            raise InvalidCityQuestionError

        if self.display_order < 1:
            raise InvalidCityQuestionError

    def activate(self) -> None:
        """질문을 활성화합니다."""
        self.is_active = True

    def deactivate(self) -> None:
        """질문을 비활성화합니다."""
        self.is_active = False

    def soft_delete(self, deleted_at: datetime) -> None:
        """질문을 soft delete 처리합니다.

        Args:
            deleted_at: 삭제 시각
        """
        self.deleted_at = deleted_at
        self.updated_at = deleted_at

    @classmethod
    def create(
        cls,
        city_id: Id,
        question: str,
        display_order: int,
        created_at: datetime,
        updated_at: datetime,
        is_active: bool = True,
    ) -> "CityQuestion":
        """새 도시 질문 엔티티를 생성합니다.

        Args:
            city_id: 도시 ID
            question: 질문 내용
            display_order: 표시 순서
            created_at: 생성 시각
            updated_at: 수정 시각
            is_active: 활성화 여부 (기본값: True)

        Returns:
            새로 생성된 CityQuestion 엔티티 (ID 자동 생성)

        Raises:
            InvalidCityQuestionError: 질문 내용이 유효하지 않은 경우
        """
        return cls(
            city_question_id=Id(),
            city_id=city_id,
            question=question,
            display_order=display_order,
            is_active=is_active,
            created_at=created_at,
            updated_at=updated_at,
        )
