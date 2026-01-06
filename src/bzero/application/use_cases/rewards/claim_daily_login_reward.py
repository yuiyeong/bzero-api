from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.results.reward_result import RewardResult
from bzero.domain.errors import AlreadyClaimedRewardError, NotFoundUserError
from bzero.domain.repositories.point_transaction import PointTransactionRepository
from bzero.domain.repositories.reward import RewardRepository
from bzero.domain.repositories.user import UserRepository
from bzero.domain.repositories.user_identity import UserIdentityRepository
from bzero.domain.services.point_transaction import PointTransactionService
from bzero.domain.services.reward import RewardService
from bzero.domain.services.user import UserService
from bzero.domain.value_objects.reward import RewardType
from bzero.domain.value_objects.user import AuthProvider
from bzero.infrastructure.repositories.point_transaction import SqlAlchemyPointTransactionRepository
from bzero.infrastructure.repositories.reward import SqlAlchemyRewardRepository
from bzero.infrastructure.repositories.user import SqlAlchemyUserRepository
from bzero.infrastructure.repositories.user_identity import SqlAlchemyUserIdentityRepository


class ClaimDailyLoginRewardUseCase:
    """일일 출석 보상 수령 유스케이스.

    매일 로그인하는 사용자에게 100P를 지급합니다.

    비즈니스 규칙:
        - 하루 1회만 지급 (KST 자정 기준)
        - 중복 요청 시 기존 보상 정보 반환 (claimed=False)
        - 멱등성 보장 (여러 번 호출해도 안전)
    """

    def __init__(self, session: AsyncSession, timezone: ZoneInfo):
        """유스케이스를 초기화합니다.

        Args:
            session: SQLAlchemy 비동기 세션
            timezone: 날짜 계산에 사용할 타임존 (KST)
        """
        self._session = session
        self._timezone = timezone

    async def execute(
        self,
        provider: str,
        provider_user_id: str,
    ) -> RewardResult:
        """일일 출석 보상을 수령합니다.

        Args:
            provider: 인증 제공자 (예: "supabase")
            provider_user_id: 인증 제공자의 사용자 ID

        Returns:
            보상 결과 (claimed=True: 새로 지급, claimed=False: 이미 받음)

        Raises:
            NotFoundUserError: 사용자를 찾을 수 없는 경우
        """
        # 리포지토리 생성
        user_repo: UserRepository = SqlAlchemyUserRepository(self._session)
        user_identity_repo: UserIdentityRepository = SqlAlchemyUserIdentityRepository(self._session)
        reward_repo: RewardRepository = SqlAlchemyRewardRepository(self._session)
        point_tx_repo: PointTransactionRepository = SqlAlchemyPointTransactionRepository(self._session)

        # 서비스 생성
        user_service = UserService(user_repo, user_identity_repo, self._timezone)
        point_tx_service = PointTransactionService(user_repo, point_tx_repo)
        reward_service = RewardService(reward_repo, user_repo, point_tx_service, self._timezone)

        # 사용자 조회
        user = await user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )
        if user is None:
            raise NotFoundUserError

        # 보상 수령 시도
        try:
            reward = await reward_service.claim_daily_login(user.user_id)
            await self._session.commit()
            return RewardResult.create_from(reward, claimed=True)
        except AlreadyClaimedRewardError:
            # 이미 받은 경우 기존 기록 반환
            existing = await reward_service.get_today_reward(user.user_id, RewardType.DAILY_LOGIN)
            if existing is None:
                raise  # 이론상 발생하지 않음
            return RewardResult.create_from(existing, claimed=False)
