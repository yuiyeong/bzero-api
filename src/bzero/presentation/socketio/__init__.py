"""Socket.IO 패키지"""
# 핸들러 등록 (import만으로 @sio.on 데코레이터 실행)
from bzero.presentation.socketio.handlers import *  # noqa: F403
from bzero.presentation.socketio.server import (
    get_socketio_server,
    sio,
    sio_app,
)


__all__ = [
    "get_socketio_server",
    "sio",
    "sio_app",
]
