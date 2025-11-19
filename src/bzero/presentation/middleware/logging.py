"""요청/응답 로깅 미들웨어."""

import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from bzero.core.loggers import access_logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """각 HTTP 요청/응답을 로깅하는 미들웨어."""

    async def dispatch(self, request: Request, call_next):
        """요청을 처리하고 로깅합니다.

        Args:
            request: FastAPI 요청 객체
            call_next: 다음 미들웨어 또는 라우트 핸들러

        Returns:
            Response: FastAPI 응답 객체
        """
        # 요청 ID 생성
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # 시작 시간 기록
        start_time = time.time()

        logger = access_logger()

        # 요청 정보 로깅
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_host": request.client.host if request.client else None,
            },
        )

        try:
            # 요청 처리
            response: Response = await call_next(request)

            # 처리 시간 계산
            process_time = time.time() - start_time

            # 응답 정보 로깅
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time": f"{process_time:.3f}s",
                    "client_host": request.client.host if request.client else None,
                },
            )

            # 응답 헤더에 request_id 추가
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # 에러 발생 시 로깅
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} - {e!s}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "process_time": f"{process_time:.3f}s",
                    "client_host": request.client.host if request.client else None,
                },
                exc_info=True,
            )
            raise
