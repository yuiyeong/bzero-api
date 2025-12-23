# 채팅 데모 테스트 가이드

Socket.IO와 Redis를 사용한 실시간 채팅 기능을 테스트할 수 있는 데모입니다.

---

## 🚀 빠른 시작

### 1. 서버 실행 확인

FastAPI 서버가 실행 중인지 확인하세요:

```bash
uv run dev
```

서버가 `http://0.0.0.0:8000`에서 실행되어야 합니다.

### 2. 브라우저에서 채팅 데모 열기

다음 URL을 브라우저에서 열어주세요:

```
http://localhost:8000/static/chat_demo.html
```

### 3. 실시간 채팅 테스트

**여러 브라우저 탭을 열어서 테스트하세요!**

1. 같은 URL을 여러 탭에서 엽니다
2. 한 탭에서 메시지를 입력하고 전송하세요
3. 다른 탭에서 실시간으로 메시지가 표시되는지 확인하세요

---

## 🎯 테스트할 수 있는 기능

### ✅ 실시간 메시지 전송/수신
- 메시지를 입력하고 전송 버튼 클릭 또는 Enter 키 입력
- 모든 연결된 클라이언트에 즉시 브로드캐스트

### ✅ 시스템 메시지
- 사용자 입장/퇴장 시 자동 시스템 메시지 표시
- 탭을 닫으면 "퇴장했습니다" 메시지 자동 전송

### ✅ Socket.IO 연결 상태
- 헤더의 상태 표시:
  - 🟢 연결됨 (초록색)
  - 🟡 재연결 중... (노란색)
  - 🔴 연결 끊김 (빨간색)

### ✅ 자동 재연결
- Socket.IO가 자동으로 heartbeat 관리
- 연결 끊김 시 자동 재연결 (최대 5회, 2초 간격)
- 수동 ping/pong 불필요

### ✅ Rate Limiting
- 2초에 1회 제한
- 빠르게 연속으로 전송하면 에러 메시지 표시

---

## 🧪 테스트 시나리오

### 시나리오 1: 기본 채팅
1. 브라우저 탭 2개 열기
2. 각 탭에서 메시지 전송
3. 양쪽 탭에서 메시지가 실시간으로 표시되는지 확인

### 시나리오 2: 입장/퇴장
1. 새 탭 열기 → "입장했습니다" 메시지 확인
2. 탭 닫기 → "퇴장했습니다" 메시지 확인

### 시나리오 3: Rate Limiting
1. 메시지를 빠르게 여러 번 전송
2. 2초 내 중복 전송 시 에러 메시지 확인

### 시나리오 4: 연결 끊김/재연결
1. 서버 재시작 (Ctrl+C 후 `uv run dev`)
2. 브라우저에서 "🟡 재연결 중..." 상태 확인
3. 2초 후 자동 재연결 확인 (최대 5회 시도)

---

## 🔍 백엔드 확인

### 데이터베이스에서 메시지 확인

채팅 메시지가 실제로 DB에 저장되는지 확인:

```bash
uv run python -c "
import asyncio
from sqlalchemy import select
from bzero.core.database import get_async_db_session, setup_db_connection
from bzero.core.settings import get_settings
from bzero.infrastructure.db.chat_message_model import ChatMessageModel

async def check():
    settings = get_settings()
    setup_db_connection(settings)
    async for session in get_async_db_session():
        result = await session.execute(
            select(ChatMessageModel).order_by(ChatMessageModel.created_at.desc()).limit(10)
        )
        messages = result.scalars().all()
        print(f'\n📩 최근 메시지 {len(messages)}개:')
        for msg in messages:
            msg_type = '💬' if msg.message_type == 'text' else '🔔'
            print(f'{msg_type} [{msg.created_at}] {msg.content}')
        break
asyncio.run(check())
"
```

### Redis Rate Limiting 확인

Redis에서 rate limit 키 확인:

```bash
docker exec -it bzero-redis redis-cli
> KEYS rate_limit:chat:*
> TTL rate_limit:chat:<user_id>:<room_id>
```

---

## 📝 기술 스택

- **Socket.IO**: 실시간 양방향 통신 (자동 재연결, heartbeat)
- **Redis**: Rate Limiting (2초에 1회 제한)
- **PostgreSQL**: 메시지 영구 저장 (3일 후 자동 삭제)
- **FastAPI**: Socket.IO ASGI 앱 통합

---

## ⚠️ 주의사항

### 이 데모는 테스트 전용입니다!

- JWT 인증이 **없습니다** (실제 프로덕션에서는 인증 필수)
- 고정된 데모 룸 ID 사용 (`demo-room-00000000-0000-0000-0000-000000000000`)
- 임시 사용자 ID 자동 생성 (UUID)

### 프로덕션 엔드포인트

실제 프로덕션에서는 인증이 필요한 엔드포인트를 사용하세요:

```javascript
// Socket.IO 인증 연결
const socket = io('http://localhost:8000/ws', {
    path: '/socket.io',
    auth: {
        token: 'your_jwt_token',
        room_id: 'room_uuid'
    }
});
```

인증 및 룸 접근 권한 검증이 포함되어 있습니다.

---

## 🐛 문제 해결

### "연결 끊김" 상태가 계속 표시되는 경우
- FastAPI 서버가 실행 중인지 확인
- Redis 컨테이너가 실행 중인지 확인: `docker ps`
- 브라우저 콘솔에서 에러 확인 (F12)

### 메시지가 전송되지 않는 경우
- Rate Limiting 확인 (2초 간격)
- 브라우저 콘솔에서 에러 메시지 확인

### 데이터베이스 연결 오류
- PostgreSQL 컨테이너 확인: `docker ps`
- `.env` 파일의 DATABASE_URL 확인

---

## 📚 관련 문서

- [Socket.IO 마이그레이션 가이드](../docs/websocket-to-socketio-migration.md)
- [Socket.IO 공식 문서](https://socket.io/docs/v4/)
- [Redis Rate Limiting 패턴](https://redis.io/docs/manual/patterns/rate-limiter/)

## 🧪 E2E 테스트 실행

Socket.IO 기능을 자동으로 테스트하려면:

```bash
uv run python scripts/test_chat_socketio.py
```

---

**즐거운 테스트 되세요! 🎉**
