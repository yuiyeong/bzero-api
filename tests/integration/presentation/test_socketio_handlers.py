"""Socket.IO Handlers Integration Tests."""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
import socketio
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from bzero.core.redis import get_redis_client
from bzero.core.settings import get_settings
from bzero.domain.entities import City, GuestHouse, Room, RoomStay, Ticket
from bzero.domain.value_objects import Id
from bzero.domain.value_objects.airship import AirshipSnapshot
from bzero.domain.value_objects.city import CitySnapshot
from bzero.domain.value_objects.room_stay import RoomStayStatus
from bzero.domain.value_objects.ticket import TicketStatus
from bzero.infrastructure.db.city_model import CityModel
from bzero.infrastructure.db.guest_house_model import GuestHouseModel
from bzero.infrastructure.db.room_model import RoomModel
from bzero.infrastructure.db.room_stay_model import RoomStayModel
from bzero.infrastructure.db.ticket_model import TicketModel
from bzero.infrastructure.db.user_model import UserModel
from bzero.presentation.socketio import sio, sio_demo

# Socket.IO 클라이언트 설정
DEMO_ROOM_ID = "00000000-0000-0000-0000-000000000000"


@pytest.fixture
def settings():
    """Settings fixture."""
    return get_settings()


@pytest.fixture
async def demo_client():
    """Socket.IO demo client fixture."""
    client = socketio.AsyncClient()
    yield client
    if client.connected:
        await client.disconnect()


@pytest.fixture
async def auth_client():
    """Socket.IO auth client fixture."""
    client = socketio.AsyncClient()
    yield client
    if client.connected:
        await client.disconnect()


@pytest.fixture
async def sample_user(test_session: AsyncSession) -> UserModel:
    """테스트용 샘플 유저."""
    now = datetime.now()
    user = UserModel(
        user_id=uuid7(),
        email="test@example.com",
        nickname="테스트유저",
        profile_emoji="👤",
        current_points=1000,
        created_at=now,
        updated_at=now,
    )
    test_session.add(user)
    await test_session.flush()
    return user


@pytest.fixture
async def sample_city(test_session: AsyncSession) -> CityModel:
    """테스트용 도시 fixture."""
    now = datetime.now()
    city = CityModel(
        city_id=uuid7(),
        name="테스트 도시",
        theme="도시 테마",
        description="테스트 설명",
        image_url="https://example.com/city.jpg",
        base_cost_points=100,
        base_duration_hours=24,
        is_active=True,
        display_order=1,
        created_at=now,
        updated_at=now,
    )
    test_session.add(city)
    await test_session.flush()
    return city


@pytest.fixture
async def sample_guest_house(test_session: AsyncSession, sample_city: CityModel) -> GuestHouseModel:
    """테스트용 게스트하우스 fixture."""
    now = datetime.now()
    guest_house = GuestHouseModel(
        guest_house_id=uuid7(),
        city_id=sample_city.city_id,
        guest_house_type="standard",
        name="테스트 게스트하우스",
        description="테스트 설명",
        image_url="https://example.com/guesthouse.jpg",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    test_session.add(guest_house)
    await test_session.flush()
    return guest_house


@pytest.fixture
async def sample_room(test_session: AsyncSession, sample_guest_house: GuestHouseModel) -> RoomModel:
    """테스트용 룸 fixture."""
    now = datetime.now()
    room = RoomModel(
        room_id=uuid7(),
        guest_house_id=sample_guest_house.guest_house_id,
        max_capacity=10,
        current_capacity=0,
        created_at=now,
        updated_at=now,
    )
    test_session.add(room)
    await test_session.flush()
    return room


@pytest.fixture
async def sample_ticket(
    test_session: AsyncSession,
    sample_user: UserModel,
    sample_city: CityModel,
) -> TicketModel:
    """테스트용 티켓 fixture."""
    settings = get_settings()
    now = datetime.now(settings.timezone)

    ticket = TicketModel(
        ticket_id=uuid7(),
        user_id=sample_user.user_id,
        city_id=sample_city.city_id,
        status="boarding",
        cost_points=100,
        duration_hours=24,
        boarding_time=now,
        scheduled_arrival_time=now + timedelta(hours=24),
        airship_snapshot={
            "airship_id": str(uuid7()),
            "name": "테스트 비행선",
            "theme": "standard",
            "image_url": "https://example.com/airship.jpg",
        },
        city_snapshot={
            "city_id": str(sample_city.city_id),
            "name": sample_city.name,
            "theme": sample_city.theme,
            "image_url": sample_city.image_url,
        },
        created_at=now,
        updated_at=now,
    )
    test_session.add(ticket)
    await test_session.flush()
    return ticket


@pytest.fixture
async def sample_room_stay(
    test_session: AsyncSession,
    sample_user: UserModel,
    sample_room: RoomModel,
    sample_ticket: TicketModel,
) -> RoomStayModel:
    """테스트용 룸 스테이 fixture (체류 중 상태)."""
    settings = get_settings()
    now = datetime.now(settings.timezone)

    room_stay = RoomStayModel(
        room_stay_id=uuid7(),
        user_id=sample_user.user_id,
        room_id=sample_room.room_id,
        ticket_id=sample_ticket.ticket_id,
        status="staying",
        check_in_time=now,
        scheduled_check_out_time=now + timedelta(hours=24),
        created_at=now,
        updated_at=now,
    )
    test_session.add(room_stay)
    await test_session.flush()
    return room_stay


@pytest.fixture
def mock_jwt_token(sample_user: UserModel, settings) -> str:
    """테스트용 JWT 토큰 생성."""
    import jwt

    payload = {
        "sub": str(sample_user.user_id),
        "email": sample_user.email,
        "aud": settings.auth.supabase_jwt_audience,
        "exp": datetime.now().timestamp() + 3600,
    }

    return jwt.encode(
        payload,
        settings.auth.supabase_jwt_secret.get_secret_value(),
        algorithm="HS256",
    )


# =============================================================================
# Demo Handler Tests (No Authentication)
# =============================================================================


@pytest.mark.asyncio
async def test_demo_connect_success(demo_client: socketio.AsyncClient):
    """데모 연결 성공 테스트."""
    # Given: Socket.IO 서버가 실행 중
    connected = False
    system_message_received = False

    @demo_client.on("system_message")
    async def on_system_message(data):
        nonlocal system_message_received
        assert "message" in data
        assert "입장했습니다" in data["message"]["content"]
        system_message_received = True

    @demo_client.event
    async def connect():
        nonlocal connected
        connected = True

    # When: 데모 서버에 연결
    await demo_client.connect(
        "http://localhost:8000/ws-demo",
        socketio_path="/socket.io/demo",
    )

    # Then: 연결 성공 및 입장 시스템 메시지 수신
    await asyncio.sleep(1)  # 시스템 메시지 수신 대기
    assert connected
    assert demo_client.connected
    assert system_message_received

    await demo_client.disconnect()


@pytest.mark.asyncio
async def test_demo_send_message_success(demo_client: socketio.AsyncClient):
    """데모 메시지 전송 성공 테스트."""
    # Given: 데모 서버에 연결
    message_received = False
    received_data = None

    @demo_client.on("new_message")
    async def on_new_message(data):
        nonlocal message_received, received_data
        message_received = True
        received_data = data

    await demo_client.connect(
        "http://localhost:8000/ws-demo",
        socketio_path="/socket.io/demo",
    )
    await asyncio.sleep(0.5)

    # When: 메시지 전송
    await demo_client.emit("send_message", {"content": "안녕하세요"})

    # Then: 메시지 브로드캐스트 수신
    await asyncio.sleep(1)
    assert message_received
    assert received_data is not None
    assert received_data["message"]["content"] == "안녕하세요"
    assert received_data["message"]["message_type"] == "text"

    await demo_client.disconnect()


@pytest.mark.asyncio
async def test_demo_rate_limiting(demo_client: socketio.AsyncClient):
    """데모 Rate Limiting 테스트."""
    # Given: 데모 서버에 연결
    error_received = False
    error_data = None

    @demo_client.on("error")
    async def on_error(data):
        nonlocal error_received, error_data
        error_received = True
        error_data = data

    await demo_client.connect(
        "http://localhost:8000/ws-demo",
        socketio_path="/socket.io/demo",
    )
    await asyncio.sleep(0.5)

    # When: 연속으로 2번 메시지 전송 (2초 제한)
    await demo_client.emit("send_message", {"content": "첫 번째"})
    await asyncio.sleep(0.1)
    await demo_client.emit("send_message", {"content": "두 번째"})

    # Then: Rate limit 에러 수신
    await asyncio.sleep(1)
    assert error_received
    assert error_data["error"] == "RATE_LIMIT_EXCEEDED"

    await demo_client.disconnect()


@pytest.mark.asyncio
async def test_demo_disconnect(demo_client: socketio.AsyncClient):
    """데모 연결 해제 테스트."""
    # Given: 데모 서버에 연결
    system_message_received = False
    disconnect_message = None

    @demo_client.on("system_message")
    async def on_system_message(data):
        nonlocal system_message_received, disconnect_message
        if "퇴장했습니다" in data["message"]["content"]:
            system_message_received = True
            disconnect_message = data

    await demo_client.connect(
        "http://localhost:8000/ws-demo",
        socketio_path="/socket.io/demo",
    )
    await asyncio.sleep(0.5)

    # When: 연결 해제
    await demo_client.disconnect()

    # Then: 퇴장 시스템 메시지 전송됨
    await asyncio.sleep(1)
    # Note: 퇴장 메시지는 다른 클라이언트만 받기 때문에 여기서는 검증 불가
    assert not demo_client.connected


# =============================================================================
# Auth Handler Tests (Authentication Required)
# =============================================================================


@pytest.mark.asyncio
async def test_auth_connect_success(
    auth_client: socketio.AsyncClient,
    sample_user: UserModel,
    sample_room: RoomModel,
    sample_room_stay: RoomStayModel,
    mock_jwt_token: str,
):
    """인증 연결 성공 테스트."""
    # Given: 유효한 JWT 토큰과 룸 접근 권한
    connected = False
    system_message_received = False

    @auth_client.on("system_message")
    async def on_system_message(data):
        nonlocal system_message_received
        assert "message" in data
        assert "입장했습니다" in data["message"]["content"]
        system_message_received = True

    @auth_client.event
    async def connect():
        nonlocal connected
        connected = True

    # When: 인증 정보와 함께 연결
    await auth_client.connect(
        "http://localhost:8000/ws",
        socketio_path="/socket.io",
        auth={
            "token": mock_jwt_token,
            "room_id": str(sample_room.room_id),
        },
    )

    # Then: 연결 성공
    await asyncio.sleep(1)
    assert connected
    assert auth_client.connected
    assert system_message_received

    await auth_client.disconnect()


@pytest.mark.asyncio
async def test_auth_connect_failure_no_token(auth_client: socketio.AsyncClient):
    """인증 실패 테스트 - 토큰 없음."""
    # Given: 토큰 없이 연결 시도
    connection_failed = False

    @auth_client.event
    async def connect_error(data):
        nonlocal connection_failed
        connection_failed = True

    # When: 토큰 없이 연결
    try:
        await auth_client.connect(
            "http://localhost:8000/ws",
            socketio_path="/socket.io",
            auth={},
        )
    except socketio.exceptions.ConnectionError:
        connection_failed = True

    # Then: 연결 거부
    await asyncio.sleep(0.5)
    assert connection_failed or not auth_client.connected


@pytest.mark.asyncio
async def test_auth_connect_failure_invalid_token(
    auth_client: socketio.AsyncClient,
    sample_room: RoomModel,
):
    """인증 실패 테스트 - 잘못된 토큰."""
    # Given: 잘못된 JWT 토큰
    connection_failed = False

    @auth_client.event
    async def connect_error(data):
        nonlocal connection_failed
        connection_failed = True

    # When: 잘못된 토큰으로 연결
    try:
        await auth_client.connect(
            "http://localhost:8000/ws",
            socketio_path="/socket.io",
            auth={
                "token": "invalid_token",
                "room_id": str(sample_room.room_id),
            },
        )
    except socketio.exceptions.ConnectionError:
        connection_failed = True

    # Then: 연결 거부
    await asyncio.sleep(0.5)
    assert connection_failed or not auth_client.connected


@pytest.mark.asyncio
async def test_auth_send_message_success(
    auth_client: socketio.AsyncClient,
    sample_user: UserModel,
    sample_room: RoomModel,
    sample_room_stay: RoomStayModel,
    mock_jwt_token: str,
):
    """인증 메시지 전송 성공 테스트."""
    # Given: 인증 서버에 연결
    message_received = False
    received_data = None

    @auth_client.on("new_message")
    async def on_new_message(data):
        nonlocal message_received, received_data
        message_received = True
        received_data = data

    await auth_client.connect(
        "http://localhost:8000/ws",
        socketio_path="/socket.io",
        auth={
            "token": mock_jwt_token,
            "room_id": str(sample_room.room_id),
        },
    )
    await asyncio.sleep(0.5)

    # When: 메시지 전송
    await auth_client.emit("send_message", {"content": "테스트 메시지"})

    # Then: 메시지 브로드캐스트 수신
    await asyncio.sleep(1)
    assert message_received
    assert received_data is not None
    assert received_data["message"]["content"] == "테스트 메시지"
    assert received_data["message"]["user_id"] == str(sample_user.user_id)

    await auth_client.disconnect()


@pytest.mark.asyncio
async def test_auth_get_history_success(
    auth_client: socketio.AsyncClient,
    sample_user: UserModel,
    sample_room: RoomModel,
    sample_room_stay: RoomStayModel,
    mock_jwt_token: str,
    test_session: AsyncSession,
):
    """메시지 히스토리 조회 성공 테스트."""
    # Given: 인증 서버에 연결 및 메시지 기록 생성
    from bzero.infrastructure.db.chat_message_model import ChatMessageModel

    settings = get_settings()
    now = datetime.now(settings.timezone)

    # 테스트 메시지 생성
    message = ChatMessageModel(
        message_id=uuid7(),
        room_id=sample_room.room_id,
        user_id=sample_user.user_id,
        content="히스토리 테스트",
        message_type="text",
        is_system=False,
        expires_at=now + timedelta(days=3),
        created_at=now,
        updated_at=now,
    )
    test_session.add(message)
    await test_session.flush()

    history_received = False
    received_history = None

    @auth_client.on("history")
    async def on_history(data):
        nonlocal history_received, received_history
        history_received = True
        received_history = data

    await auth_client.connect(
        "http://localhost:8000/ws",
        socketio_path="/socket.io",
        auth={
            "token": mock_jwt_token,
            "room_id": str(sample_room.room_id),
        },
    )
    await asyncio.sleep(0.5)

    # When: 히스토리 조회
    await auth_client.emit("get_history", {"limit": 10})

    # Then: 히스토리 수신
    await asyncio.sleep(1)
    assert history_received
    assert received_history is not None
    assert "messages" in received_history
    assert len(received_history["messages"]) > 0

    await auth_client.disconnect()


# =============================================================================
# Cleanup
# =============================================================================


@pytest.fixture(autouse=True)
async def cleanup_redis():
    """테스트 후 Redis 정리."""
    yield
    # Rate limit 키 정리
    redis_client = get_redis_client()
    keys = await redis_client.keys("rate_limit:chat:*")
    if keys:
        await redis_client.delete(*keys)
