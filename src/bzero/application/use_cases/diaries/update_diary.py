from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.results.diary_result import DiaryResult
from bzero.domain.errors import ForbiddenDiaryAccessError
from bzero.domain.services.diary import DiaryService
from bzero.domain.services.user import UserService
from bzero.domain.value_objects import DiaryMood, Id
from bzero.domain.value_objects.user import AuthProvider


class UpdateDiaryUseCase:
    """일기 수정 유스케이스.

    기존 일기의 제목, 내용, 감정을 수정합니다.
    본인이 작성한 일기만 수정할 수 있습니다.
    """

    def __init__(
        self,
        session: AsyncSession,
        user_service: UserService,
        diary_service: DiaryService,
    ):
        """유스케이스를 초기화합니다.

        Args:
            session: SQLAlchemy 비동기 세션
            user_service: 사용자 도메인 서비스
            diary_service: 일기 도메인 서비스
        """
        self._session = session
        self._user_service = user_service
        self._diary_service = diary_service

    async def execute(
        self,
        provider: str,
        provider_user_id: str,
        diary_id: str,
        title: str,
        content: str,
        mood: str,
    ) -> DiaryResult:
        """일기를 수정합니다.

        Args:
            provider: 인증 제공자 (예: "supabase")
            provider_user_id: 인증 제공자의 사용자 ID
            diary_id: 수정할 일기 ID (hex 문자열)
            title: 새 제목 (1-50자)
            content: 새 내용 (1-500자)
            mood: 새 감정 상태

        Returns:
            수정된 일기 정보

        Raises:
            NotFoundUserError: 사용자를 찾을 수 없는 경우
            NotFoundDiaryError: 일기를 찾을 수 없는 경우
            ForbiddenDiaryAccessError: 본인의 일기가 아닌 경우
            InvalidDiaryContentError: 제목 또는 내용이 유효하지 않은 경우
        """
        # 1. 사용자 조회
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )

        # 2. 일기 조회
        diary = await self._diary_service.get_diary_by_id(Id.from_hex(diary_id))

        # 3. 권한 검증 (본인 일기인지 확인)
        if diary.user_id != user.user_id:
            raise ForbiddenDiaryAccessError

        # 4. 일기 수정
        diary_mood = DiaryMood(mood)
        updated_diary = await self._diary_service.update_diary(
            diary_id=diary.diary_id,
            title=title,
            content=content,
            mood=diary_mood,
        )

        # 5. 트랜잭션 커밋
        await self._session.commit()

        return DiaryResult.create_from(updated_diary)
