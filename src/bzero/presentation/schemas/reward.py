from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from bzero.application.results.reward_result import RewardResult


class RewardResponse(BaseModel):
    """보상 응답 스키마."""

    reward_id: str = Field(..., description="보상 ID (UUID v7 hex)")
    user_id: str = Field(..., description="사용자 ID (UUID v7 hex)")
    reward_type: str = Field(..., description="보상 유형 (daily_login 등)")
    amount: int = Field(..., description="지급 포인트")
    reference_date: str = Field(..., description="기준 날짜 (YYYY-MM-DD)")
    claimed: bool = Field(..., description="True: 새로 지급, False: 이미 받음")
    created_at: datetime = Field(..., description="생성 일시")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def create_from(cls, result: RewardResult) -> "RewardResponse":
        """RewardResult로부터 RewardResponse를 생성합니다.

        Args:
            result: 보상 유스케이스 결과 객체

        Returns:
            RewardResponse: 보상 응답 스키마
        """
        return cls(
            reward_id=result.reward_id,
            user_id=result.user_id,
            reward_type=result.reward_type,
            amount=result.amount,
            reference_date=result.reference_date,
            claimed=result.claimed,
            created_at=result.created_at,
        )
