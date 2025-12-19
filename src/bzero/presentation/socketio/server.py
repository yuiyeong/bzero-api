"""Socket.IO 서버 초기화 및 설정"""
import socketio

from bzero.core.settings import Environment, get_settings


# 환경별 CORS 설정
settings = get_settings()
cors_allowed_origins = "*" if settings.environment != Environment.PRODUCTION else settings.cors.origins

# Socket.IO 서버 (네임스페이스로 구분)
# - "/" (기본): 인증 필요
# - "/demo": 인증 불필요 (데모용)
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=cors_allowed_origins,
    logger=True,
    engineio_logger=False,
    # 하트비트 설정 (자동 관리)
    ping_interval=25,  # 25초마다 ping
    ping_timeout=60,  # 60초 응답 없으면 연결 종료
    # 성능 최적화
    max_http_buffer_size=1_000_000,  # 1MB
    compression_threshold=1024,  # 1KB 이상 압축
)

# ASGI 앱 생성
# socketio_path: Socket.IO 프로토콜 경로 (main.py의 mount 경로 + socketio_path)
# 예: main.py에서 /ws에 마운트 → 실제 경로: /ws/socket.io
sio_app = socketio.ASGIApp(sio, socketio_path='/')


def get_socketio_server() -> socketio.AsyncServer:
    """Socket.IO 서버 인스턴스를 반환합니다."""
    return sio
