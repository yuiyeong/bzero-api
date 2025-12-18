"""Socket.IO 패키지"""
from bzero.presentation.socketio.server import (
    get_socketio_server,
    sio,
    sio_app,
)

# 핸들러 등록 (import만으로 @sio.on 데코레이터 실행)
from bzero.presentation.socketio.handlers import *  # noqa: F401, F403

__all__ = [
    "sio",
    "sio_app",
    "get_socketio_server",
]
