import re
from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, Field, field_validator

from bzero.application.results.user_result import UserResult


class UpdateUserRequest(BaseModel):
    PATTERN_ALLOWED_NICKNAME: ClassVar[str] = r"^[가-힣a-zA-Z0-9]+$"

    nickname: str = Field(
        ...,
        min_length=2,
        max_length=10,
        description="사용자 닉네임 (2-10자, 한글/영문/숫자만 허용)",
        examples=["홍길동", "김철수123", "JohnDoe"],
    )
    profile_emoji: str = Field(
        ...,
        min_length=1,
        max_length=4,
        description="프로필 이모지 (단일 이모지만 허용)",
        examples=["😎", "👍", "😍"],
    )

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, v: str) -> str:
        """닉네임 형식을 검증합니다.

        Args:
            v: 닉네임 값

        Returns:
            검증된 닉네임

        Raises:
            ValueError: 닉네임 형식이 잘못된 경우
        """
        # 한글, 영문, 숫자만 허용
        pattern = re.compile(cls.PATTERN_ALLOWED_NICKNAME)
        if not pattern.match(v):
            raise ValueError("닉네임은 한글, 영문, 숫자만 허용됩니다 (특수문자 불가)")

        return v

    @field_validator("profile_emoji")
    @classmethod
    def validate_emoji(cls, v: str) -> str:
        """이모지 형식을 검증합니다.

        Args:
            v: 이모지 값

        Returns:
            검증된 이모지

        Raises:
            ValueError: 이모지 형식이 잘못된 경우
        """
        # 허용된 이모지 인지 검증
        if v not in ["🙂", "😊", "😎", "😍", "🤔", "👉", "🌟", "👍", "🤩", "🚀"]:
            raise ValueError("유효한 단일 이모지를 입력해주세요")

        return v


class UserResponse(BaseModel):
    """사용자 정보 응답 스키마"""

    user_id: str = Field(..., description="사용자 ID (UUID v7 hex)")
    email: str = Field(..., description="이메일")
    nickname: str | None = Field(None, description="닉네임 (2-10자)")
    profile_emoji: str | None = Field(None, description="프로필 이모지")
    current_points: int = Field(..., description="현재 포인트")
    is_profile_complete: bool = Field(..., description="프로필 완료 여부")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")

    model_config = {"from_attributes": True}

    @classmethod
    def create_from(cls, result: UserResult) -> "UserResponse":
        return cls(
            user_id=result.user_id,
            email=result.email,
            nickname=result.nickname,
            profile_emoji=result.profile_emoji,
            current_points=result.current_points,
            is_profile_complete=result.is_profile_complete,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )
