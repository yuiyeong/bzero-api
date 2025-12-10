# bzero-api (B0 Backend API)

B0 프로젝트의 Backend API 서버입니다. FastAPI와 Clean Architecture를 기반으로 구축되었습니다.

---

## 프로젝트 개요

**bzero-api**는 B0 프로젝트의 백엔드 API 서버로, 사용자 인증, 포인트 시스템, 도시 관리, 실시간 채팅, 일기/문답지 저장, 비행선 티켓 시스템을 담당합니다.

**핵심 아키텍처**: Clean Architecture + Domain-Driven Design (DDD)

---

## 기술 스택

- **FastAPI** 0.121.x - 비동기 웹 프레임워크
- **Python** 3.12+, **uv** - 패키지 관리
- **PostgreSQL** 16+ - 메인 데이터베이스
- **SQLAlchemy** 2.0.44 (postgresql-asyncpg) - 비동기 ORM
- **Alembic** 1.17.x - 데이터베이스 마이그레이션
- **Celery** 5.5.x + **Redis** 5.2.x - 백그라운드 작업 및 캐싱
- **uuid-utils** 0.11.x - UUID v7 지원
- **pytest** 9.0.x + **ruff** 0.14.x - 테스트 및 린팅
- **Supabase Auth** - 사용자 인증 (JWT 기반)

---

## 프로젝트 구조

```
bzero-api/
├── src/bzero/               # 메인 소스 디렉토리
│   ├── domain/              # 도메인 계층 (순수 비즈니스 로직)
│   │   ├── entities/        # User, UserIdentity, City, PointTransaction, Airship, Ticket
│   │   ├── value_objects/   # Id, Email, Nickname, Profile, Balance, AuthProvider, TransactionType, TicketStatus 등
│   │   ├── repositories/    # 리포지토리 인터페이스 (추상 클래스, 비동기/동기 분리)
│   │   ├── ports/           # 외부 시스템 포트 인터페이스 (TaskScheduler)
│   │   ├── services/        # 도메인 서비스 (UserService, PointTransactionService, CityService, AirshipService, TicketService)
│   │   └── errors.py        # 도메인 예외
│   │
│   ├── application/         # 애플리케이션 계층 (유스케이스)
│   │   ├── use_cases/       # users/, cities/, airships/, tickets/ 하위 디렉토리로 구분
│   │   └── results/         # 유스케이스 결과 객체 (UserResult, CityResult, AirshipResult, TicketResult)
│   │
│   ├── infrastructure/      # 인프라 계층 (외부 시스템 연동)
│   │   ├── adapters/        # 포트 구현체 (CeleryTaskScheduler)
│   │   ├── auth/            # JWT 유틸리티 (Supabase JWT 검증)
│   │   ├── db/              # ORM 모델 (UserModel, CityModel, PointTransactionModel, UserIdentityModel, AirshipModel, TicketModel, TaskFailureLogModel)
│   │   └── repositories/    # 리포지토리 구현체 (비동기/동기)
│   │
│   ├── presentation/        # 프레젠테이션 계층 (API)
│   │   ├── api/             # API 엔드포인트 및 의존성 주입
│   │   ├── schemas/         # Pydantic 스키마
│   │   └── middleware/      # 미들웨어 (로깅, 에러 핸들링)
│   │
│   ├── core/                # 공통 설정
│   │   ├── settings.py      # 환경 설정
│   │   ├── database.py      # DB 연결 설정 (비동기/동기)
│   │   └── loggers.py       # 로깅 설정
│   │
│   ├── worker/              # Celery 백그라운드 작업
│   │   ├── app.py           # Celery 앱 설정
│   │   └── tasks/           # 태스크 모듈
│   │       ├── base.py      # FailoverTask 베이스 클래스
│   │       ├── names.py     # 태스크 이름 상수
│   │       └── ticket.py    # 티켓 관련 태스크
│   │
│   └── main.py              # FastAPI 앱 진입점
│
├── migrations/              # Alembic 마이그레이션
│   └── versions/            # 마이그레이션 파일들 (7개)
├── tests/                   # 테스트
│   ├── unit/                # 단위 테스트
│   │   ├── application/use_cases/  # 유스케이스 테스트
│   │   └── domain/          # 도메인 테스트
│   │       ├── entities/    # 엔티티 테스트
│   │       └── services/    # 서비스 테스트
│   ├── integration/         # 통합 테스트
│   │   ├── application/use_cases/  # 유스케이스 통합 테스트
│   │   ├── domain/          # 도메인 통합 테스트
│   │   │   ├── repositories/ # 리포지토리 테스트
│   │   │   └── services/    # 서비스 통합 테스트
│   │   └── worker/tasks/    # Celery 태스크 테스트
│   ├── e2e/                 # E2E 테스트
│   │   └── presentation/api/# API 엔드포인트 테스트
│   └── conftest.py          # pytest 설정
├── docs/                    # 프로젝트 문서
│   ├── domain-model.md      # 도메인 모델 설명
│   ├── erd.md               # ERD
│   └── checklist.md         # MVP 구현 체크리스트
├── .env                     # 환경 변수
└── pyproject.toml           # 프로젝트 설정
```

### Clean Architecture 계층별 역할

```
Presentation → Application → Domain ← Infrastructure
```

- **Domain**: 순수 비즈니스 로직 (외부 의존성 없음)
- **Application**: 유스케이스 (도메인 엔티티 조합)
- **Infrastructure**: DB, 외부 API 연동 (Domain 인터페이스 구현)
- **Presentation**: HTTP 요청/응답 처리

---

## 개발 환경 설정

```bash
# 1. 의존성 설치
uv sync

# 2. 환경 변수 설정
cp .env.template .env
# .env 파일 수정 (DATABASE, REDIS, CELERY 설정 등)

# 3. Docker 인프라 실행 (PostgreSQL, Redis, Celery Worker, Celery Beat)
docker compose -f docker-compose.dev.yml up -d

# 4. 데이터베이스 마이그레이션
uv run alembic upgrade head

# 5. FastAPI 개발 서버 실행
uv run dev
```

---

## 개발 워크플로우

각 기능(`docs/01-mvp.md` 참고)마다 다음 순서로 개발:

```
1. 도메인 엔티티/값 객체 작성 (Domain)
2. 리포지토리 인터페이스 작성 (Domain)
3. 유스케이스 작성 (Application)
4. ORM 모델 작성 (Infrastructure)
5. 리포지토리 구현체 작성 (Infrastructure)
6. API 엔드포인트 작성 (Presentation)
7. Pydantic 스키마 작성 (Presentation)
8. 의존성 주입 설정
9. 마이그레이션 생성 및 적용
10. 테스트 작성
```

### 현재 구현 상태 (2025-12-10 기준)

#### ✅ 완료된 기능

**환경 설정**

- FastAPI, PostgreSQL, SQLAlchemy (비동기/동기), Alembic, UUID v7
- Supabase Auth 연동 (JWT 검증)
- Celery + Redis 백그라운드 작업 인프라

**도메인 계층**

- **엔티티**: User, UserIdentity, City, PointTransaction, Airship, Ticket
    - 모든 엔티티에 `create()` 팩토리 메서드 패턴 적용
- **값 객체**:
    - 공통: Id (UUID v7)
    - User: Email, Nickname, Profile, Balance, AuthProvider
    - PointTransaction: TransactionType, TransactionStatus, TransactionReason, TransactionReference
    - Ticket: TicketStatus, CitySnapshot, AirshipSnapshot
- **도메인 서비스**: UserService, PointTransactionService, CityService, AirshipService, TicketService
- **리포지토리 인터페이스**: UserRepository, UserIdentityRepository, CityRepository, PointTransactionRepository,
  AirshipRepository, TicketRepository, TicketSyncRepository (동기)
- **포트 인터페이스**: TaskScheduler (백그라운드 작업 스케줄링)

**인프라 계층**

- **ORM 모델**: UserModel, UserIdentityModel, CityModel, PointTransactionModel, AirshipModel, TicketModel,
  TaskFailureLogModel
- **리포지토리 구현체**: SqlAlchemyUserRepository, SqlAlchemyUserIdentityRepository, SqlAlchemyCityRepository,
  SqlAlchemyPointTransactionRepository, SqlAlchemyAirshipRepository, SqlAlchemyTicketRepository,
  SqlAlchemyTicketSyncRepository, SqlAlchemyTaskFailureLogRepository
- **베이스 클래스**: TicketRepositoryBase (티켓 리포지토리 공통 로직)
- **어댑터**: CeleryTaskScheduler (TaskScheduler 구현체)
- **인증**: Supabase JWT 검증 (verify_supabase_jwt, extract_user_id_from_jwt)

**애플리케이션 계층**

- **유스케이스**:
    - User: CreateUserUseCase, GetMeUseCase, UpdateUserUseCase
    - City: GetActiveCitiesUseCase, GetCityByIdUseCase
    - Airship: GetAvailableAirshipsUseCase
    - Ticket: PurchaseTicketUseCase, GetTicketsByUserUseCase, GetTicketDetailUseCase, GetCurrentBoardingTicketUseCase,
      CancelTicketUseCase
- **결과 객체**: UserResult, CityResult, AirshipResult, TicketResult, PaginatedResult

**프레젠테이션 계층**

- **API 엔드포인트**:
    - `POST /api/v1/users` - 사용자 생성
    - `GET /api/v1/users/me` - 내 정보 조회
    - `PATCH /api/v1/users/me` - 내 정보 수정
    - `GET /api/v1/cities` - 활성화된 도시 목록 조회
    - `GET /api/v1/cities/{city_id}` - 도시 상세 조회
    - `GET /api/v1/airships` - 이용 가능한 비행선 목록 조회
    - `POST /api/v1/tickets` - 티켓 구매
    - `GET /api/v1/tickets` - 내 티켓 목록 조회
    - `GET /api/v1/tickets/current` - 현재 탑승 중인 티켓 조회
    - `GET /api/v1/tickets/{ticket_id}` - 티켓 상세 조회
    - `POST /api/v1/tickets/{ticket_id}/cancel` - 티켓 취소
- **Pydantic 스키마**: UserResponse, CityResponse, AirshipResponse, TicketResponse
- **의존성 주입**: DBSession, CurrentJWTPayload, CurrentUserService, CurrentPointTransactionService, CurrentCityService,
  CurrentAirshipService, CurrentTicketService, CurrentTaskScheduler
- **미들웨어**: 로깅, 에러 핸들링

**Celery Worker**

- **태스크**: complete_ticket_task (도착 시 자동 티켓 완료 처리)
- **Failover 처리**: FailoverTask 베이스 클래스 (acks_late, reject_on_worker_lost, 실패 로그 DB 저장)

**마이그레이션** (7개)

- 0001_create_user.py
- 0002_create_city.py (base_cost_points, base_duration_hours 포함)
- 0003_create_pointtransaction.py
- 0004_create_useridentity.py
- 0005_create_airship.py
- 0006_create_ticket.py
- 0008_create_taskfailurelog.py

**테스트**

- 단위 테스트:
    - 엔티티: City, Airship, Ticket
    - 서비스: UserService, PointTransactionService, AirshipService, TicketService
    - 유스케이스: City, Airship
- 통합 테스트:
    - 리포지토리: UserRepository, UserIdentityRepository, CityRepository, PointTransactionRepository, AirshipRepository,
      TicketRepository
    - 서비스: PointTransactionService, AirshipService, TicketService
    - 유스케이스: Ticket
    - Celery 태스크: complete_ticket_task
- E2E 테스트: User API, City API, Airship API, Ticket API

#### 🚧 진행 예정

- 게스트하우스 및 룸 시스템
- 채팅 시스템

자세한 진행 상황은 `docs/checklist.md` 참조

### 코드 예시: 주요 도메인 모델

#### 1. Domain Layer - 엔티티 (팩토리 메서드 패턴)

```python
# src/bzero/domain/entities/user.py
@dataclass
class User:
    user_id: Id
    email: Email | None  # nullable (소셜 로그인 시)
    nickname: Nickname | None  # nullable (온보딩 전)
    profile: Profile | None  # nullable (온보딩 전)
    current_points: Balance

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    @classmethod
    def create(
            cls,
            email: Email | None,
            created_at: datetime,
            updated_at: datetime,
            nickname: Nickname | None = None,
            profile: Profile | None = None,
    ) -> "User":
        """새 User 엔티티를 생성합니다 (ID 자동 생성)."""
        return cls(
            user_id=Id(),
            email=email,
            nickname=nickname,
            profile=profile,
            current_points=Balance(0),
            created_at=created_at,
            updated_at=updated_at,
        )
```

```python
# src/bzero/domain/entities/user_identity.py
@dataclass
class UserIdentity:
    identity_id: Id
    user_id: Id
    provider: AuthProvider  # SUPABASE
    provider_user_id: str  # Supabase UUID

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
```

```python
# src/bzero/domain/entities/point_transaction.py
@dataclass
class PointTransaction:
    point_transaction_id: Id
    user_id: Id
    transaction_type: TransactionType  # EARN, SPEND
    amount: int
    reason: TransactionReason  # SIGN_UP, DIARY, QUESTIONNAIRE, TICKET, EXTEND
    balance_before: Balance
    balance_after: Balance
    status: TransactionStatus  # PENDING, COMPLETED, FAILED

    created_at: datetime
    updated_at: datetime

    reference_type: TransactionReference | None = None
    reference_id: Id | None = None
    description: str | None = None
```

#### 2. Domain Layer - 값 객체

```python
# src/bzero/domain/value_objects/common.py
@dataclass(frozen=True)
class Id:
    value: str

    def __init__(self, value: str | None = None):
        object.__setattr__(self, "value", value or str(uuid7()))
```

```python
# src/bzero/domain/value_objects/user.py
class AuthProvider(Enum):
    SUPABASE = "supabase"


@dataclass(frozen=True)
class Email:
    value: str
    # 이메일 형식 검증


@dataclass(frozen=True)
class Nickname:
    value: str
    # 2-10자 검증


@dataclass(frozen=True)
class Profile:
    value: str
    # 이모지 프로필


@dataclass(frozen=True)
class Balance:
    value: int
    # 음수 방지
```

#### 3. Domain Layer - 서비스

```python
# src/bzero/domain/services/user.py
class UserService:
    def __init__(self, user_repo, user_identity_repo):
        self._user_repo = user_repo
        self._user_identity_repo = user_identity_repo

    async def get_or_create_user_by_provider(...) -> User: ...

    async def get_user_by_id(user_id: Id) -> User | None: ...

    async def update_user(user_id: Id, nickname, profile) -> User: ...
```

```python
# src/bzero/domain/services/point_transaction.py
class PointTransactionService:
    async def earn_points(user_id, amount, reason, ...) -> PointTransaction: ...

    async def spend_points(user_id, amount, reason, ...) -> PointTransaction: ...

    async def get_transactions(user_id, filter) -> list[PointTransaction]: ...
```

```python
# src/bzero/domain/services/city.py
class CityService:
    def __init__(self, city_repo):
        self._city_repository = city_repo

    async def get_active_cities() -> list[City]: ...

    async def get_city_by_id(city_id: Id) -> City | None: ...
```

---

## 코딩 가이드라인

### Clean Architecture 원칙

- **의존성 방향**: Presentation → Application → Domain ← Infrastructure
- **Domain**: 외부 프레임워크 의존성 없음 (순수 Python)
- **Application**: Domain 인터페이스만 사용 (구현체 사용 금지)
- **Infrastructure**: Domain 인터페이스 구현
- **Presentation**: 비즈니스 로직은 유스케이스에 위임

### 주요 규칙

- **비동기 처리**: 모든 DB 작업은 `async/await` 사용
- **ID 생성**: UUID v7 사용 (`uuid_utils.uuid7()`)
- **값 객체**: 불변 객체로 작성 (`@dataclass(frozen=True)`)
- **엔티티 팩토리 메서드**: 새 엔티티 생성 시 `Entity.create()` 클래스 메서드 사용 (ID 자동 생성)
- **예외 처리**: 도메인 예외 → HTTP 예외 변환 (Presentation Layer에서)
- **인증**: Supabase Auth (JWT), 환경 변수로 민감 정보 관리
- **타입 힌트**: 모든 함수와 메서드에 타입 힌트 필수

### 네이밍 컨벤션

- 클래스: `PascalCase` (예: `User`, `UserRepository`)
- 함수/변수: `snake_case` (예: `get_user`, `user_id`)
- 상수: `UPPER_SNAKE_CASE` (예: `MAX_RETRY_COUNT`)

---

## Celery Task 작성 가이드라인

### 아키텍처 개요

```
Application (UseCase) → Domain Port (TaskScheduler) ← Infrastructure Adapter (CeleryTaskScheduler)
                                                                    ↓
                                                            Worker (Celery Task)
                                                                    ↓
                                                      Sync Repository (DB 작업)
```

- **유스케이스**: `TaskScheduler` 포트를 통해 백그라운드 작업 예약
- **어댑터**: `CeleryTaskScheduler`가 실제 Celery `send_task` 호출
- **Worker**: 독립 프로세스로 실행, 동기 리포지토리 사용

### 새 Celery Task 작성 순서

```
1. 태스크 이름 상수 정의 (worker/tasks/names.py)
2. 동기 리포지토리 인터페이스 작성 (domain/repositories/*_sync.py) - 필요시
3. 동기 리포지토리 구현체 작성 (infrastructure/repositories/*_sync.py) - 필요시
4. 태스크 함수 작성 (worker/tasks/*.py)
5. 태스크 export (worker/tasks/__init__.py)
6. 포트 인터페이스에 메서드 추가 (domain/ports/task_scheduler.py)
7. 어댑터에 메서드 구현 (infrastructure/adapters/celery_task_scheduler.py)
8. 유스케이스에서 포트 호출
9. 테스트 작성 (tests/integration/worker/tasks/)
```

### 필수 규칙

#### 1. 태스크 이름 상수 사용

```python
# src/bzero/worker/tasks/names.py
# 태스크 이름은 반드시 상수로 정의 (태스크 정의와 send_task 양쪽에서 사용)
COMPLETE_TICKET_TASK_NAME = "bzero.worker.tasks.ticket.complete_ticket_task"
```

#### 2. FailoverTask 베이스 클래스 상속

```python
# src/bzero/worker/tasks/ticket.py
from bzero.worker.tasks.base import FailoverTask


@shared_task(
    name=COMPLETE_TICKET_TASK_NAME,
    base=FailoverTask,  # 반드시 FailoverTask 상속
    autoretry_for=(OperationalError,),  # 일시적 오류 재시도
    retry_backoff=True,  # 점진적 재시도 간격
    retry_kwargs={"max_retries": 3},  # 최대 재시도 횟수
)
def complete_ticket_task(ticket_id: str) -> dict:
    ...
```

**FailoverTask 기능**:

- `acks_late = True`: 태스크 완료 후 ACK (실행 전 ACK 방지)
- `reject_on_worker_lost = True`: 워커 손실 시 재큐잉
- `on_failure`: 최종 실패 시 `TaskFailureLogModel`에 로그 저장

#### 3. 동기 세션 사용 (Celery는 비동기 미지원)

```python
# 태스크 내에서 동기 세션 사용
from bzero.core.database import get_sync_db_session

with get_sync_db_session() as session:
    repository = SqlAlchemyTicketSyncRepository(session)
    # DB 작업...
    session.commit()  # 명시적 커밋 필수
```

#### 4. 멱등성 보장

```python
# 이미 처리된 상태면 성공으로 반환 (중복 실행 안전)
if ticket.status in (TicketStatus.COMPLETED, TicketStatus.CANCELLED):
    return {"ticket_id": ticket_id, "result": "success"}
```

#### 5. 예외 처리 패턴

```python
def some_task(param: str) -> dict:
    error_message: str | None = None

    with get_sync_db_session() as session:
        try:
            # 비즈니스 로직...
            session.commit()
        except BeZeroError as e:
            # 비즈니스 예외: 로깅 후 결과 반환 (재시도 안함)
            error_message = e.code.value
            logger.error(f"Business logic error: {error_message}")
        except Exception as e:
            # 예상치 못한 예외: 재시도 위해 다시 던짐
            logger.error(f"Unexpected error: {e}")
            raise e

    return {
        "param": param,
        "result": f"failed; {error_message}" if error_message else "success",
    }
```

#### 6. 포트/어댑터 패턴 준수

```python
# src/bzero/domain/ports/task_scheduler.py
class TaskScheduler(ABC):
    @abstractmethod
    def schedule_ticket_completion(self, ticket_id: str, eta: datetime) -> None:
        """티켓 완료 작업을 예약합니다."""


# src/bzero/infrastructure/adapters/celery_task_scheduler.py
class CeleryTaskScheduler(TaskScheduler):
    def schedule_ticket_completion(self, ticket_id: str, eta: datetime) -> None:
        bzero_celery_app.send_task(
            COMPLETE_TICKET_TASK_NAME,
            args=[ticket_id],
            eta=eta,
        )
```

### 테스트 작성

```python
# tests/integration/worker/tasks/test_ticket_tasks.py
def test_complete_ticket_task_success(db_session, ...):
    # Given: BOARDING 상태 티켓
    # When: complete_ticket_task 실행
    result = complete_ticket_task(ticket.ticket_id.to_hex())
    # Then: COMPLETED 상태로 변경
    assert result["result"] == "success"
```

### Worker 실행

```bash
# 개발 환경 (Docker)
docker compose -f docker-compose.dev.yml up -d

# 로그 확인
docker compose -f docker-compose.dev.yml logs -f celery-worker

# 개별 서비스 재시작 (코드 변경 후)
docker compose -f docker-compose.dev.yml restart celery-worker
```

---

## 자주 사용하는 명령어

### 개발 서버

```bash
# 1. Docker 인프라 실행 (PostgreSQL, Redis, Celery Worker, Celery Beat)
docker compose -f docker-compose.dev.yml up -d

# 2. FastAPI 개발 서버 실행 (http://0.0.0.0:8000)
uv run dev

# Swagger UI: http://0.0.0.0:8000/docs

# Docker 로그 확인
docker compose -f docker-compose.dev.yml logs -f celery-worker
docker compose -f docker-compose.dev.yml logs -f celery-beat

# Docker 컨테이너 중지
docker compose -f docker-compose.dev.yml down
```

### 린팅 및 테스트

```bash
# 포매팅 + 린팅
uv run ruff format .
uv run ruff check --fix .

# 테스트
uv run pytest
uv run pytest --cov=src/bzero --cov-report=html
```

### 마이그레이션

```bash
# 마이그레이션 파일 생성 (자동 생성)
uv run alembic revision --autogenerate -m "설명"

# 마이그레이션 적용
uv run alembic upgrade head

# 마이그레이션 1단계 롤백
uv run alembic downgrade -1

# 마이그레이션 히스토리 확인
uv run alembic history

# 현재 버전 확인
uv run alembic current

# 마이그레이션 파일 위치
# migrations/versions/
```

---

## 문제 해결

### 마이그레이션 충돌

```bash
uv run alembic heads  # 헤드 확인
uv run alembic merge -m "Merge heads" <rev1> <rev2>
```

### 비동기 세션 에러

- 모든 DB 쿼리 앞에 `await` 사용
- `AsyncSession`을 컨텍스트 매니저로 사용

### CORS 에러

```python
# app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 데이터베이스 연결 실패

- Docker 컨테이너 상태 확인: `docker compose -f docker-compose.dev.yml ps`
- PostgreSQL 로그 확인: `docker compose -f docker-compose.dev.yml logs postgres`
- `.env`의 DATABASE 설정 확인
- 컨테이너 재시작: `docker compose -f docker-compose.dev.yml restart postgres`

---

## 참고 자료

### 프로젝트 문서

- **MVP 기능 명세**: `../docs/01-mvp.md`
- **도메인 모델**: `docs/domain-model.md`
- **ERD**: `docs/erd.md`
- **MVP 체크리스트**: `docs/checklist.md`

### 기술 문서

- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy 2.0**: https://docs.sqlalchemy.org/en/20/
- **Alembic**: https://alembic.sqlalchemy.org/
- **Celery**: https://docs.celeryq.dev/en/stable/
- **Clean Architecture**: https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
- **UUID v7 (RFC 9562)**: https://www.rfc-editor.org/rfc/rfc9562.html
