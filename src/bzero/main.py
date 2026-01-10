from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import sentry_sdk
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from bzero.core.database import close_db_connection, setup_db_connection
from bzero.core.loggers import setup_loggers
from bzero.core.settings import Environment, get_settings
from bzero.presentation.api import router as api_router
from bzero.presentation.middleware.error_handler import setup_error_handlers
from bzero.presentation.middleware.logging import LoggingMiddleware
from bzero.presentation.socketio import sio_app


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

    # Sentry 초기화
    if settings.sentry.dsn.get_secret_value():
        sentry_sdk.init(
            dsn=settings.sentry.dsn.get_secret_value(),
            environment=settings.sentry.environment,
            traces_sample_rate=settings.sentry.traces_sample_rate,
            send_default_pii=True,  # 개인정보 포함 전송 허용 (필요시 조정)
        )

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

    setup_error_handlers(b0, debug=settings.is_debug)

    # Socket.IO 마운트 (API 라우터보다 먼저)
    # - 기본 네임스페이스 "/" : 인증 필요
    # - "/demo" 네임스페이스 : 인증 불필요 (데모용)
    b0.mount("/ws", sio_app)

    # 라우터 등록
    b0.include_router(api_router)

    # Static 파일 서빙 (채팅 데모용)
    static_dir = Path(__file__).parent.parent.parent / "static"
    if static_dir.exists():
        b0.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @b0.get("/docs/socket.io", include_in_schema=False)
    async def asyncapi_docs():
        """Socket.IO AsyncAPI 문서 (Standalone React Component)"""
        docs_path = Path(__file__).parent.parent.parent / "docs" / "asyncapi.yaml"
        if not docs_path.exists():
            return HTMLResponse("AsyncAPI definition not found.", status_code=404)

        asyncapi_content = docs_path.read_text(encoding="utf-8")

        # AsyncAPI React Component HTML Template
        # Config: showSidebar=true, sidebarOrganization='byTags'
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <title>B0 Chat API (Socket.IO)</title>
          <link rel="stylesheet" href="https://unpkg.com/@asyncapi/react-component@latest/styles/default.min.css">
          <style>
            body {{ margin: 0; padding: 0; }}
            #asyncapi {{ height: 100vh; }}
          </style>
        </head>
        <body>
          <div id="asyncapi"></div>
          <script src="https://unpkg.com/@asyncapi/react-component@latest/browser/standalone/index.js"></script>
          <script>
            const schema = {asyncapi_content!r};
            const config = {{
              showErrors: true,
              sidebarOrganization: 'byTags',
            }};
            AsyncApiStandalone.render({{ schema, config }}, document.getElementById('asyncapi'));
          </script>
        </body>
        </html>
        """
        return HTMLResponse(html_content)

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
