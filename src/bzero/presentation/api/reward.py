from fastapi import APIRouter

from bzero.application.use_cases.rewards import ClaimDailyLoginRewardUseCase
from bzero.core.settings import get_settings
from bzero.presentation.api.dependencies import CurrentJWTPayload, DBSession
from bzero.presentation.schemas.common import DataResponse
from bzero.presentation.schemas.reward import RewardResponse


router = APIRouter(prefix="/rewards", tags=["rewards"])


@router.post(
    "/daily-login/claim",
    response_model=DataResponse[RewardResponse],
    summary="일일 출석 보상 수령",
    description="""
일일 출석 보상을 수령합니다.

- 첫 요청: 100P 지급, claimed=True
- 이후 요청 (같은 날): 기존 기록 반환, claimed=False

날짜 기준은 한국 시간(KST) 자정입니다.
""",
)
async def claim_daily_login_reward(
    session: DBSession,
    jwt_payload: CurrentJWTPayload,
) -> DataResponse[RewardResponse]:
    """일일 출석 보상을 수령합니다.

    Args:
        session: 데이터베이스 세션
        jwt_payload: JWT 페이로드 (인증된 사용자 정보)

    Returns:
        RewardResponse: 보상 결과 (claimed 필드로 신규/중복 구분)
    """
    use_case = ClaimDailyLoginRewardUseCase(session, get_settings().timezone)
    result = await use_case.execute(
        provider=jwt_payload.provider,
        provider_user_id=jwt_payload.provider_user_id,
    )
    return DataResponse(data=RewardResponse.create_from(result))
