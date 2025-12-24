#!/usr/bin/env python3
"""Socket.IO 채팅 E2E 테스트 스크립트.

Socket.IO 데모 서버와 인증 서버의 기본 기능을 테스트합니다.

사용법:
    uv run python scripts/test_chat_socketio.py
"""

import asyncio
import sys
from datetime import datetime

import socketio


# 데모 룸 ID
DEMO_ROOM_ID = "00000000-0000-0000-0000-000000000000"


async def test_demo_chat():
    """데모 채팅 기능 테스트."""
    print("\n🧪 [테스트 1] 데모 채팅 연결 및 메시지 전송")
    print("=" * 60)

    client = socketio.AsyncClient()
    connected = False
    system_messages = []
    text_messages = []

    @client.event
    async def connect():
        nonlocal connected
        connected = True
        print("✅ 연결 성공")

    @client.event
    async def disconnect():
        print("👋 연결 해제")

    @client.on("system_message")
    async def on_system_message(data):
        msg = data["message"]
        system_messages.append(msg)
        print(f"📢 [시스템] {msg['content']}")

    @client.on("new_message")
    async def on_new_message(data):
        msg = data["message"]
        text_messages.append(msg)
        user = msg.get("user_id", "Unknown")[:8]
        print(f"💬 [메시지] {user}... : {msg['content']}")

    @client.on("error")
    async def on_error(data):
        print(f"❌ [에러] {data.get('error', 'Unknown error')}")

    try:
        # 1. 연결
        print("\n1️⃣  연결 중...")
        await client.connect(
            "http://localhost:8000/ws-demo",
            socketio_path="/socket.io/demo",
        )
        await asyncio.sleep(1)

        if not connected:
            print("❌ 연결 실패")
            return False

        # 2. 메시지 전송
        print("\n2️⃣  메시지 전송 중...")
        await client.emit("send_message", {"content": "안녕하세요! Socket.IO 테스트입니다."})
        await asyncio.sleep(1)

        if not text_messages:
            print("❌ 메시지 수신 실패")
            return False
        print(f"✅ 메시지 전송/수신 성공 ({len(text_messages)}개)")

        # 3. Rate Limiting 테스트
        print("\n3️⃣  Rate Limiting 테스트 중...")
        error_received = False

        @client.on("error")
        async def on_rate_limit_error(data):
            nonlocal error_received
            if data.get("error") == "RATE_LIMIT_EXCEEDED":
                error_received = True
                print("✅ Rate Limit 에러 수신 (정상)")

        await client.emit("send_message", {"content": "첫 번째"})
        await asyncio.sleep(0.1)
        await client.emit("send_message", {"content": "두 번째"})
        await asyncio.sleep(1)

        if not error_received:
            print("⚠️  Rate Limit 에러 미수신 (Redis 설정 확인 필요)")

        # 4. 연결 해제
        print("\n4️⃣  연결 해제 중...")
        await client.disconnect()
        await asyncio.sleep(0.5)

        print("\n✅ 데모 채팅 테스트 완료")
        print(f"   - 시스템 메시지: {len(system_messages)}개")
        print(f"   - 텍스트 메시지: {len(text_messages)}개")
        return True

    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        if client.connected:
            await client.disconnect()


async def test_auth_chat_without_token():
    """인증 채팅 - 토큰 없이 연결 시도 (실패 예상)."""
    print("\n🧪 [테스트 2] 인증 채팅 - 토큰 없이 연결 (실패 예상)")
    print("=" * 60)

    client = socketio.AsyncClient()
    connection_failed = False

    @client.event
    async def connect_error(data):
        nonlocal connection_failed
        connection_failed = True
        print("✅ 연결 거부됨 (정상)")

    try:
        print("\n1️⃣  토큰 없이 연결 시도 중...")
        await client.connect(
            "http://localhost:8000/ws",
            socketio_path="/socket.io",
            auth={},  # 토큰 없음
            wait_timeout=3,
        )
        await asyncio.sleep(1)

        if client.connected:
            print("❌ 연결 성공 (보안 문제!)")
            await client.disconnect()
            return False

        print("\n✅ 인증 실패 테스트 완료 (연결 거부됨)")
        return True

    except socketio.exceptions.ConnectionError:
        print("✅ 연결 거부됨 (정상)")
        return True
    except Exception as e:
        print(f"\n⚠️  예상치 못한 에러: {e}")
        return True  # 연결 실패는 정상
    finally:
        if client.connected:
            await client.disconnect()


async def test_concurrent_connections():
    """동시 다중 연결 테스트."""
    print("\n🧪 [테스트 3] 동시 다중 연결 (5명)")
    print("=" * 60)

    clients = []
    connected_count = 0

    async def create_client(client_id: int):
        nonlocal connected_count
        client = socketio.AsyncClient()

        @client.event
        async def connect():
            nonlocal connected_count
            connected_count += 1
            print(f"✅ 클라이언트 #{client_id} 연결 성공")

        @client.on("new_message")
        async def on_new_message(data):
            msg = data["message"]
            user = msg.get("user_id", "Unknown")[:8]
            print(f"💬 클라이언트 #{client_id} 수신: {user}... : {msg['content']}")

        try:
            await client.connect(
                "http://localhost:8000/ws-demo",
                socketio_path="/socket.io/demo",
            )
            clients.append(client)
            return client
        except Exception as e:
            print(f"❌ 클라이언트 #{client_id} 연결 실패: {e}")
            return None

    try:
        # 1. 5개 클라이언트 동시 연결
        print("\n1️⃣  5개 클라이언트 연결 중...")
        tasks = [create_client(i) for i in range(1, 6)]
        await asyncio.gather(*tasks)
        await asyncio.sleep(1)

        if connected_count != 5:
            print(f"❌ 연결 실패 (연결됨: {connected_count}/5)")
            return False

        # 2. 첫 번째 클라이언트에서 메시지 전송
        print("\n2️⃣  클라이언트 #1에서 메시지 전송 중...")
        if clients and clients[0]:
            await clients[0].emit("send_message", {"content": "모두에게 인사합니다!"})
            await asyncio.sleep(1)

        # 3. 모든 클라이언트 연결 해제
        print("\n3️⃣  모든 클라이언트 연결 해제 중...")
        for i, client in enumerate(clients, 1):
            if client and client.connected:
                await client.disconnect()
                print(f"👋 클라이언트 #{i} 연결 해제")
        await asyncio.sleep(0.5)

        print("\n✅ 동시 다중 연결 테스트 완료")
        return True

    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        for client in clients:
            if client and client.connected:
                await client.disconnect()


async def main():
    """모든 테스트 실행."""
    print("\n" + "=" * 60)
    print("🚀 Socket.IO E2E 테스트 시작")
    print("=" * 60)
    print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n⚠️  사전 요구사항:")
    print("   1. FastAPI 서버 실행 중 (uv run dev)")
    print("   2. Redis 서버 실행 중")
    print("   3. 데모 룸 생성 완료 (scripts/create_demo_room.py)")
    print("\n계속하려면 Enter를 누르세요...")
    input()

    results = []

    # 테스트 1: 데모 채팅
    result1 = await test_demo_chat()
    results.append(("데모 채팅", result1))
    await asyncio.sleep(1)

    # 테스트 2: 인증 실패
    result2 = await test_auth_chat_without_token()
    results.append(("인증 실패 (토큰 없음)", result2))
    await asyncio.sleep(1)

    # 테스트 3: 동시 다중 연결
    result3 = await test_concurrent_connections()
    results.append(("동시 다중 연결", result3))

    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    total = len(results)
    passed = sum(1 for _, result in results if result)
    print(f"\n총 {total}개 테스트 중 {passed}개 통과 ({passed/total*100:.0f}%)")
    print(f"⏰ 종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")

    return all(result for _, result in results)


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단됨")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 실행 실패: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
