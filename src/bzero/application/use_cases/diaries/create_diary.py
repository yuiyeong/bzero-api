from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.results.diary_result import DiaryResult
from bzero.domain.errors import NotFoundRoomStayError
from bzero.domain.services.diary import DiaryService
from bzero.domain.services.point_transaction import PointTransactionService
from bzero.domain.services.room_stay import RoomStayService
from bzero.domain.services.user import UserService
from bzero.domain.value_objects import DiaryMood
from bzero.domain.value_objects.point_transaction import (
    TransactionReason,
    TransactionReference,
)
from bzero.domain.value_objects.user import AuthProvider


class CreateDiaryUseCase:
    """일기 생성 유스케이스.

    체류 중 일기를 작성하고 포인트를 지급합니다.

    비즈니스 규칙:
        - 현재 활성 체류(CHECKED_IN 또는 EXTENDED) 중일 때만 작성 가능
        - 체류당 1개의 일기만 작성 가능
        - 최초 작성 시 50P 지급 (TransactionReference.DIARIES로 중복 방지)
    """

    DIARY_REWARD_POINTS = 50

    def __init__(
        self,
        session: AsyncSession,
        user_service: UserService,
        room_stay_service: RoomStayService,
        diary_service: DiaryService,
        point_transaction_service: PointTransactionService,
    ):
        """유스케이스를 초기화합니다.

        Args:
            session: SQLAlchemy 비동기 세션
            user_service: 사용자 도메인 서비스
            room_stay_service: 체류 도메인 서비스
            diary_service: 일기 도메인 서비스
            point_transaction_service: 포인트 거래 도메인 서비스
        """
        self._session = session
        self._user_service = user_service
        self._room_stay_service = room_stay_service
        self._diary_service = diary_service
        self._point_transaction_service = point_transaction_service

    async def execute(
        self,
        provider: str,
        provider_user_id: str,
        title: str,
        content: str,
        mood: str,
    ) -> DiaryResult:
        """일기를 생성합니다.

        Args:
            provider: 인증 제공자 (예: "supabase")
            provider_user_id: 인증 제공자의 사용자 ID
            title: 일기 제목 (1-50자)
            content: 일기 내용 (1-500자)
            mood: 감정 상태

        Returns:
            생성된 일기 정보

        Raises:
            NotFoundUserError: 사용자를 찾을 수 없는 경우
            NotFoundRoomStayError: 활성 체류가 없는 경우
            DuplicatedDiaryError: 이미 일기가 작성된 체류인 경우
            InvalidDiaryContentError: 제목 또는 내용이 유효하지 않은 경우
        """
        # 1. 사용자 조회
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )

        # 2. 현재 활성 체류 조회 (없으면 에러)
        room_stay = await self._room_stay_service.get_checked_in_by_user_id(user.user_id)
        if room_stay is None:
            raise NotFoundRoomStayError

        # 3. 일기 생성 (중복 체크 포함)
        diary_mood = DiaryMood(mood)
        diary = await self._diary_service.create_diary(
            user_id=user.user_id,
            room_stay_id=room_stay.room_stay_id,
            city_id=room_stay.city_id,
            guest_house_id=room_stay.guest_house_id,
            title=title,
            content=content,
            mood=diary_mood,
        )

        # 4. 포인트 지급 (TransactionReference.DIARIES로 중복 방지)
        await self._point_transaction_service.earn_by(
            user=user,
            amount=self.DIARY_REWARD_POINTS,
            reason=TransactionReason.DIARY,
            reference_type=TransactionReference.DIARIES,
            reference_id=diary.diary_id,
        )

        # 5. 트랜잭션 커밋
        await self._session.commit()

        return DiaryResult.create_from(diary)
