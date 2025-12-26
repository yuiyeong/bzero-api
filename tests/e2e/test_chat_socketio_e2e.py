import asyncio
import logging
import os
import socket
import subprocess
import sys
import time
from datetime import datetime

import pytest
import socketio

from bzero.core.database import _async_engine, get_async_db_session, setup_db_connection
from bzero.core.settings import get_settings
from bzero.domain.value_objects.guesthouse import GuestHouseType
from bzero.infrastructure.db.base import Base
from bzero.infrastructure.db.city_model import CityModel
from bzero.infrastructure.db.guest_house_model import GuestHouseModel
from bzero.infrastructure.db.room_model import RoomModel


logger = logging.getLogger(__name__)

# 데모용 고정 룸 ID
DEMO_ROOM_ID = "00000000-0000-0000-0000-000000000000"


def find_free_port():
    """사용 가능한 자유 포트를 찾습니다."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


async def init_test_db():
    """테스트용 기초 데이터(도시, 게스트하우스, 데모 룸)를 생성합니다."""


    async with get_async_db_session() as session:
        # 1. 도시 생성
        city = await session.get(CityModel, "00000000-0000-0000-0000-000000000000")
        if not city:
            city = CityModel(
                city_id="00000000-0000-0000-0000-000000000000",
                name="데모 시티",
                theme="데모 테마",
                description="테스트용 도시",
                base_cost_points=0,
                base_duration_hours=0,
                is_active=True,
                display_order=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(city)

        # 2. 게스트하우스 생성
        gh = await session.get(GuestHouseModel, "00000000-0000-0000-0000-000000000000")
        if not gh:
            gh = GuestHouseModel(
                guest_house_id="00000000-0000-0000-0000-000000000000",
                city_id=city.city_id,
                name="데모 게스트하우스",
                description="테스트용",
                guest_house_type=GuestHouseType.MIXED.value,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(gh)

        # 3. 룸 생성
        room = await session.get(RoomModel, DEMO_ROOM_ID)
        if not room:
            room = RoomModel(
                room_id=DEMO_ROOM_ID,
                guest_house_id=gh.guest_house_id,
                max_capacity=100,
                current_capacity=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(room)

        await session.commit()


# run_server 는 더 이상 사용되지 않음 (Popen에서 bzero.main:create_app 사용)


@pytest.fixture(scope="module")
def live_server_url():
    """테스트용 라이브 서버를 실행하고 URL을 반환합니다."""
    port = find_free_port()
    env = os.environ.copy()
    env["ENVIRONMENT"] = "test"

    # 서버 실행 (uvicorn 직접 실행)
    cmd = [
        sys.executable, "-m", "uvicorn",
        "bzero.main:create_app",
        "--factory",
        "--host", "127.0.0.1",
        "--port", str(port),
        "--log-level", "error"
    ]

    # DB 초기화 (테이블 생성 및 데모 데이터)

    # 현재 프로세스에서 DB 초기화 실행 (서버 시작 전)
    os.environ["ENVIRONMENT"] = "test"
    settings = get_settings()
    setup_db_connection(settings)

    async def setup_db():
        # 현재 프로세스에서 DB 초기화 실행 (서버 시작 전)
        if _async_engine:
            async with _async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        await init_test_db()

    asyncio.run(setup_db())

    # 서버 기동
    proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # 서버 기동 대기 (포트가 열릴 때까지 최대 5초)
    start_time = time.time()
    while time.time() - start_time < 5:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                break
        time.sleep(0.5)
    else:
        stdout, stderr = proc.communicate()
        print(f"STDOUT: {stdout.decode()}")
        print(f"STDERR: {stderr.decode()}")
        proc.kill()
        raise RuntimeError("Server failed to start in time")

    yield f"http://127.0.0.1:{port}"

    proc.terminate()
    proc.wait()


@pytest.mark.asyncio
async def test_chat_demo_e2e_flow(live_server_url):
    """데모 채팅의 전체 E2E 흐름을 테스트합니다.

    1. 연결
    2. 룸 입장 및 시스템 메시지 확인
    3. 메시지 전송 및 브로드캐스트 확인
    4. Rate Limiting 확인
    """
    client = socketio.AsyncClient()
    messages_received = []
    system_messages = []
    errors = []

    @client.on("connected", namespace="/demo")
    async def on_connected(data):
        logger.info(f"Connected: {data}")

    @client.on("new_message", namespace="/demo")
    async def on_new_message(data):
        messages_received.append(data["message"])

    @client.on("system_message", namespace="/demo")
    async def on_system_message(data):
        system_messages.append(data["message"])

    @client.on("error", namespace="/demo")
    async def on_error(data):
        errors.append(data)

    # 1. 연결
    await client.connect(
        live_server_url,
        socketio_path="/ws/socket.io/",
        namespaces=["/demo"]
    )
    assert client.connected

    # 2. 룸 입장
    await client.emit("join_room", {"room_id": DEMO_ROOM_ID}, namespace="/demo")

    # 시스템 메시지 수신 대기 (최대 2초)
    for _ in range(20):
        if any("입장했습니다" in msg["content"] for msg in system_messages):
            break
        await asyncio.sleep(0.1)

    # 입장 시스템 메시지 확인
    if not any("입장했습니다" in msg["content"] for msg in system_messages):
        print(f"DEBUG: system_messages={system_messages}")
        print(f"DEBUG: errors={errors}")
        pytest.fail(f"System message '입장했습니다' not received. Errors: {errors}")

    # 3. 메시지 전송
    test_content = f"E2E Test Message {datetime.now().isoformat()}"
    await client.emit("send_message", {"content": test_content}, namespace="/demo")

    # 메시지 수신 대기 (최대 2초)
    for _ in range(20):
        if any(msg["content"] == test_content for msg in messages_received):
            break
        await asyncio.sleep(0.1)

    # 메시지 수신 확인
    if not any(msg["content"] == test_content for msg in messages_received):
        print(f"DEBUG: messages_received={messages_received}")
        pytest.fail(f"Message '{test_content}' not received")

    # 4. Rate Limiting 테스트 (연속 전송)
    await client.emit("send_message", {"content": "Fast message 1"}, namespace="/demo")
    await client.emit("send_message", {"content": "Fast message 2"}, namespace="/demo")
    await asyncio.sleep(0.5)

    # 에러 발생 확인
    assert any(err.get("error") == "RATE_LIMIT_EXCEEDED" for err in errors)

    await client.disconnect()


@pytest.mark.asyncio
async def test_concurrent_chat_e2e(live_server_url):
    """다중 클라이언트 동시 접속 및 메시지 교환 테스트."""
    num_clients = 3
    clients = [socketio.AsyncClient() for _ in range(num_clients)]
    received_counts = [0] * num_clients

    async def setup_client(client_id, c):
        @c.on("new_message", namespace="/demo")
        async def on_msg(data):
            received_counts[client_id] += 1

        await c.connect(live_server_url, socketio_path="/ws/socket.io/", namespaces=["/demo"])
        await c.emit("join_room", {"room_id": DEMO_ROOM_ID}, namespace="/demo")

    # 모든 클라이언트 접속
    await asyncio.gather(*(setup_client(i, c) for i, c in enumerate(clients)))
    await asyncio.sleep(0.5)

    # 각 클라이언트가 메시지 한 번씩 전송
    for i, c in enumerate(clients):
        await c.emit("send_message", {"content": f"Hello from client {i}"}, namespace="/demo")
        await asyncio.sleep(0.1)

    await asyncio.sleep(1)

    # 각 클라이언트는 본인 포함 3개의 메시지를 받아야 함
    for count in received_counts:
        assert count == num_clients

    # 정리
    await asyncio.gather(*(c.disconnect() for c in clients))
