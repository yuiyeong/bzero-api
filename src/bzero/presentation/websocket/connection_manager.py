"""WebSocket 연결 관리자.

룸별로 WebSocket 연결을 관리하고 메시지를 브로드캐스트합니다.
"""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket 연결 관리자.

    룸별로 연결을 그룹화하여 관리하며, 하트비트를 통해 연결 상태를 모니터링합니다.

    구조:
        - active_connections: {room_id: {user_id: WebSocket}}
        - last_heartbeat: {user_id: datetime}

    하트비트:
        - 클라이언트는 30초마다 ping 메시지 전송
        - 서버는 pong 응답
        - 60초 동안 heartbeat 없으면 연결 종료
    """

    HEARTBEAT_INTERVAL = 30  # 초
    HEARTBEAT_TIMEOUT = 60  # 초

    def __init__(self, timezone: ZoneInfo):
        """ConnectionManager를 초기화합니다.

        Args:
            timezone: 시간대 정보 (하트비트 타임스탬프용)
        """
        self._active_connections: dict[str, dict[str, WebSocket]] = defaultdict(dict)
        self._last_heartbeat: dict[str, datetime] = {}
        self._timezone = timezone
        self._heartbeat_task: asyncio.Task | None = None

    async def connect(self, room_id: str, user_id: str, websocket: WebSocket) -> None:
        """WebSocket 연결을 수락하고 룸에 추가합니다.

        Args:
            room_id: 룸 ID (hex 문자열)
            user_id: 사용자 ID (hex 문자열)
            websocket: WebSocket 연결
        """
        await websocket.accept()
        self._active_connections[room_id][user_id] = websocket
        self._last_heartbeat[user_id] = datetime.now(self._timezone)
        logger.info(f"User {user_id} connected to room {room_id}")

        # 하트비트 모니터링 시작 (아직 시작 안했으면)
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._monitor_heartbeats())

    def disconnect(self, room_id: str, user_id: str) -> None:
        """WebSocket 연결을 종료하고 룸에서 제거합니다.

        Args:
            room_id: 룸 ID (hex 문자열)
            user_id: 사용자 ID (hex 문자열)
        """
        if room_id in self._active_connections:
            self._active_connections[room_id].pop(user_id, None)

            # 룸이 비어있으면 삭제
            if not self._active_connections[room_id]:
                del self._active_connections[room_id]

        self._last_heartbeat.pop(user_id, None)
        logger.info(f"User {user_id} disconnected from room {room_id}")

    def update_heartbeat(self, user_id: str) -> None:
        """사용자의 마지막 하트비트 시간을 업데이트합니다.

        Args:
            user_id: 사용자 ID (hex 문자열)
        """
        self._last_heartbeat[user_id] = datetime.now(self._timezone)

    async def send_personal_message(self, message: dict, room_id: str, user_id: str) -> None:
        """특정 사용자에게 메시지를 전송합니다.

        Args:
            message: 전송할 메시지 (JSON)
            room_id: 룸 ID (hex 문자열)
            user_id: 사용자 ID (hex 문자열)
        """
        if room_id in self._active_connections and user_id in self._active_connections[room_id]:
            websocket = self._active_connections[room_id][user_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {e}")
                # 전송 실패 시 연결 종료
                self.disconnect(room_id, user_id)

    async def broadcast_to_room(self, message: dict, room_id: str) -> None:
        """룸의 모든 사용자에게 메시지를 브로드캐스트합니다.

        Args:
            message: 전송할 메시지 (JSON)
            room_id: 룸 ID (hex 문자열)
        """
        if room_id not in self._active_connections:
            return

        # 전송 실패한 사용자 목록
        failed_users = []

        for user_id, websocket in self._active_connections[room_id].items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to user {user_id}: {e}")
                failed_users.append(user_id)

        # 전송 실패한 사용자 연결 종료
        for user_id in failed_users:
            self.disconnect(room_id, user_id)

    def get_active_users(self, room_id: str) -> list[str]:
        """룸의 활성 사용자 목록을 반환합니다.

        Args:
            room_id: 룸 ID (hex 문자열)

        Returns:
            사용자 ID 목록 (hex 문자열)
        """
        return list(self._active_connections.get(room_id, {}).keys())

    async def _monitor_heartbeats(self) -> None:
        """하트비트를 모니터링하고 타임아웃된 연결을 종료합니다.

        60초 동안 heartbeat가 없으면 연결을 종료합니다.
        """
        while True:
            try:
                await asyncio.sleep(30)  # 30초마다 체크

                now = datetime.now(self._timezone)
                timeout_users = []

                for user_id, last_heartbeat in self._last_heartbeat.items():
                    if now - last_heartbeat > timedelta(seconds=self.HEARTBEAT_TIMEOUT):
                        timeout_users.append(user_id)

                # 타임아웃된 사용자 연결 종료
                for user_id in timeout_users:
                    logger.warning(f"User {user_id} heartbeat timeout, disconnecting...")
                    # room_id를 찾아서 연결 종료
                    for room_id in self._active_connections:
                        if user_id in self._active_connections[room_id]:
                            self.disconnect(room_id, user_id)
                            break

            except Exception as e:
                logger.error(f"Heartbeat monitor error: {e}")
