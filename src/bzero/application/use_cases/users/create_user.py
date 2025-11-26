from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.results.user_result import UserResult
from bzero.domain.errors import DuplicatedUserError
from bzero.domain.services.point_transaction import PointTransactionService
from bzero.domain.services.user import UserService
from bzero.domain.value_objects import AuthProvider, Email, TransactionReason, TransactionReference


class CreateUserUseCase:
    """
    신규 사용자 등록 UseCase

    Supabase 인증 후 첫 로그인 시 호출됩니다.
    - UserIdentity 중복 확인
    - User 생성 (nickname=None, profile=None, current_points=0)
    - UserIdentity 생성 (provider='email')
    - 초기 포인트 지급 (1000P)
    """

    INITIAL_POINTS = 1000

    def __init__(
        self,
        session: AsyncSession,
        user_service: UserService,
        point_transaction_service: PointTransactionService,
    ):
        self._session = session
        self._user_service = user_service
        self._point_transaction_service = point_transaction_service

    async def execute(self, provider: str, provider_user_id: str, email: str) -> UserResult:
        """
        Args:
            provider: Supabase 인증 방식
            provider_user_id: Supabase user_id (JWT의 sub claim)
            email: 사용자 이메일

        Returns:
            UserResult

        Raises:
            DuplicatedUserError: 이미 존재하는 사용자일 때
        """
        try:
            # 0. 중복 생성인지 확인
            if await self._user_service.find_user_by_provider_and_provider_user_id(
                provider=AuthProvider(provider),
                provider_user_id=provider_user_id,
                raise_exception=False,
            ):
                raise DuplicatedUserError

            # 1. User + UserIdentity 생성
            user, _ = await self._user_service.create_user_with_identity(
                provider=AuthProvider(provider),
                provider_user_id=provider_user_id,
                email=Email(email),
            )

            # 2. 초기 포인트 지급
            updated_user, _ = await self._point_transaction_service.earn_by(
                user=user,
                amount=self.INITIAL_POINTS,
                reason=TransactionReason.SIGNED_UP,
                reference_type=TransactionReference.USERS,
                reference_id=user.user_id,
                description="회원가입 보너스",
            )

            await self._session.commit()

            # 3. UserResult 반환
            return UserResult.create_from(updated_user)
        except Exception:
            await self._session.rollback()
            raise
