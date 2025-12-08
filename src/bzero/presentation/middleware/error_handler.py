"""전역 예외 처리 핸들러."""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from bzero.domain.errors import (
    AuthError,
    BadRequestError,
    BeZeroError,
    DuplicatedError,
    ErrorCode,
    NotFoundError,
)
from bzero.presentation.schemas.common import ErrorResponse


def setup_error_handlers(app: FastAPI, debug: bool) -> None:
    """애플리케이션에서 발생하는 에러에 대한 핸들러를 등록하는 함수.

    Args:
        app: FastAPI 애플리케이션 인스턴스
        debug: 디버그 모드 여부
    """

    @app.exception_handler(AuthError)
    async def handle_auth_error(_: Request, e: AuthError) -> JSONResponse:
        """인증/인가 에러를 처리합니다."""
        return _convert_error_to_json(status_code=status.HTTP_401_UNAUTHORIZED, error_code=e.code)

    @app.exception_handler(DuplicatedError)
    async def handle_duplicated_error(_: Request, e: DuplicatedError) -> JSONResponse:
        return _convert_error_to_json(status_code=status.HTTP_409_CONFLICT, error_code=e.code)

    @app.exception_handler(BadRequestError)
    async def handle_bad_request_error(_: Request, e: BadRequestError) -> JSONResponse:
        """잘못된 요청 에러를 처리합니다."""
        return _convert_error_to_json(status_code=status.HTTP_400_BAD_REQUEST, error_code=e.code)

    @app.exception_handler(NotFoundError)
    async def handle_not_found_error(_: Request, e: NotFoundError) -> JSONResponse:
        """리소스를 찾을 수 없는 에러를 처리합니다."""
        return _convert_error_to_json(status_code=status.HTTP_404_NOT_FOUND, error_code=e.code)

    @app.exception_handler(BeZeroError)
    async def handle_smartrss_error(_: Request, e: BeZeroError) -> JSONResponse:
        """B0 애플리케이션 에러를 처리합니다."""
        return _convert_error_to_json(status_code=status.HTTP_400_BAD_REQUEST, error_code=e.code)

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(_: Request, e: RequestValidationError) -> JSONResponse:
        """RequestValidationError가 발생했을 때, ErrorResponse를 만들어 반환하는 함수."""
        error_messages = []
        for error in e.errors():
            field = " -> ".join([str(x) for x in error["loc"]])
            message = f"{field}: {error['msg']}"
            error_messages.append(message)
        return _convert_error_to_json(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            error_code=ErrorCode.INVALID_PARAMETER,
            message="; ".join(error_messages),
        )

    @app.exception_handler(Exception)
    async def handle_exception(_: Request, e: Exception) -> JSONResponse:
        """핸들링하지 못한 exception들도 ErrorResponse를 반환할 수 있도록 설정."""
        return _convert_error_to_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=ErrorCode.INTERNAL_ERROR,
            message=str(e) if debug else None,
        )


def _convert_error_to_json(status_code: int, error_code: ErrorCode, message: str | None = None) -> JSONResponse:
    """ErrorCode를 바탕으로 JSONResponse를 만드는 함수.

    Args:
        status_code: HTTP 상태 코드
        error_code: 에러 코드
        message: 커스텀 메시지 (옵션)

    Returns:
        JSONResponse: 에러 응답
    """
    error_response = ErrorResponse.from_error_code(error_code, message)
    return JSONResponse(status_code=status_code, content=error_response.model_dump())
