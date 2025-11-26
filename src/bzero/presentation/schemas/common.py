from dataclasses import dataclass

from pydantic import BaseModel

from bzero.domain.errors import ErrorCode


class DataResponse[T](BaseModel):
    """단일 객체 정보를 나타내는 Response.

    Attributes:
        data: 응답 데이터
    """

    data: T


class Pagination(BaseModel):
    """목록에 대한 페이지네이션 정보.

    Attributes:
        total: 전체 항목 수
        offset: 시작 위치
        limit: 한 페이지당 항목 수
    """

    total: int
    offset: int
    limit: int


class ListResponse[T](BaseModel):
    """목록 정보를 나타내는 Response.

    Attributes:
        list: 목록 데이터
        pagination: 페이지네이션 정보
    """

    list: list[T]
    pagination: Pagination


class Error(BaseModel):
    """에러를 나타내는 객체.

    Attributes:
        code: 에러 코드
        message: 에러 메시지
    """

    code: str
    message: str


class ErrorResponse(BaseModel):
    """에러를 가지고 있는 Response.

    Attributes:
        error: 에러 객체
    """

    error: Error

    @classmethod
    def from_error_code(cls, error_code: ErrorCode, message: str | None = None) -> "ErrorResponse":
        """ErrorCode로부터 ErrorResponse를 생성합니다.

        Args:
            error_code: 에러 코드
            message: 커스텀 메시지 (옵션)

        Returns:
            ErrorResponse: 생성된 에러 응답
        """
        return cls(
            error=Error(code=error_code.name, message=message if message else error_code.value),
        )


@dataclass
class JWTPayload:
    """JWT payload data."""

    provider: str
    provider_user_id: str
    email: str
    phone: str
    email_verified: bool
    phone_verified: bool
