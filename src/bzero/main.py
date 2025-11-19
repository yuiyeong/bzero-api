from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bzero.core.database import close_db_connection, setup_db_connection
from bzero.core.loggers import setup_loggers
from bzero.core.settings import Environment, get_settings
from bzero.presentation.middleware.logging import LoggingMiddleware


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """애플리케이션 시작/종료 시 실행되는 이벤트"""
    # Startup: 데이터베이스 연결 초기화
    settings = get_settings()
    setup_db_connection(settings)

    yield

    # Shutdown: 데이터베이스 연결 종료
    await close_db_connection()


def create_app() -> FastAPI:
    settings = get_settings()

    b0 = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.is_debug,
        lifespan=lifespan,  # lifespan 이벤트 등록
    )

    # CORS 설정
    b0.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors.origins,
        allow_credentials=settings.cors.allow_credentials,
        allow_methods=settings.cors.allow_methods,
        allow_headers=settings.cors.allow_headers,
    )

    if settings.environment != Environment.TEST:
        # 테스트 때는 로깅 X
        setup_loggers(settings)
        b0.add_middleware(LoggingMiddleware)

    @b0.get("/")
    def check_health():
        return {"status": "ok"}

    return b0


app = create_app()


def dev():
    """개발 서버 실행"""
    uvicorn.run(
        "bzero.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
