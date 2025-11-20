# bzero-api (B0 Backend API)

B0 프로젝트의 백엔드 API 서버입니다. FastAPI와 Clean Architecture를 기반으로 구축되었습니다.

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
- **pytest** 8.4.x + **ruff** 0.14.x - 테스트 및 린팅
- **passlib[bcrypt]** - 비밀번호 해싱

---

## 프로젝트 구조

```
bzero-api/
├── src/bzero/               # 메인 소스 디렉토리
│   ├── domain/              # 도메인 계층 (순수 비즈니스 로직)
│   │   ├── entities/        # User, City, Room 등
│   │   ├── value_objects.py # Email, Nickname, Profile, Balance 등
│   │   ├── repositories/    # 리포지토리 인터페이스 (추상 클래스)
│   │   └── errors.py        # 도메인 예외
│   │
│   ├── application/         # 애플리케이션 계층 (유스케이스)
│   │   ├── use_cases/       # RegisterUser, PurchaseTicket 등
│   │   └── results/         # 유스케이스 결과 객체
│   │
│   ├── infrastructure/      # 인프라 계층 (외부 시스템 연동)
│   │   ├── db/
│   │   │   ├── base.py      # SQLAlchemy Base 설정
│   │   │   └── user_model.py # User ORM 모델
│   │   └── repositories/    # 리포지토리 구현체
│   │       └── user.py      # UserRepository 구현
│   │
│   ├── presentation/        # 프레젠테이션 계층 (API)
│   │   ├── api/             # API 엔드포인트
│   │   ├── schemas/         # Pydantic 스키마
│   │   └── middleware/      # 미들웨어 (로깅 등)
│   │
│   ├── core/                # 공통 설정
│   │   ├── settings.py      # 환경 설정
│   │   ├── database.py      # DB 연결 설정
│   │   └── loggers.py       # 로깅 설정
│   │
│   └── main.py              # FastAPI 앱 진입점
│
├── migrations/              # Alembic 마이그레이션
│   └── versions/            # 마이그레이션 파일들
├── tests/                   # 테스트
│   ├── integration/         # 통합 테스트
│   │   └── repositories/    # 리포지토리 테스트
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
# 의존성 설치
uv sync

# 환경 변수 설정
cp .env.example .env
# .env 파일 수정 (DATABASE_URL, SECRET_KEY 등)

# 데이터베이스 초기화
createdb bzero_dev
uv run alembic upgrade head
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

### 현재 구현 상태 (2025-01-20 기준)

#### ✅ 완료된 기능
- **환경 설정**: FastAPI, PostgreSQL, SQLAlchemy (비동기), Alembic, UUID v7
- **User 도메인**: User 엔티티, 값 객체 (Id, Email, Nickname, Profile, Balance)
- **User 리포지토리**: 인터페이스 및 구현체 (SqlAlchemyUserRepository)
- **테스트**: User 리포지토리 통합 테스트
- **마이그레이션**: User 테이블 생성 (0001_create_user.py)

#### 🚧 진행 중
- 회원가입 UseCase 및 API 엔드포인트 구현 예정
- PointTransaction 시스템 구현 예정

자세한 진행 상황은 `docs/checklist.md` 참조

### 코드 예시: User 엔티티 및 리포지토리

#### 1. Domain Layer

```python
# src/bzero/domain/entities/user.py
@dataclass
class User:
    id: Id                    # 값 객체
    email: Email              # 값 객체
    nickname: Nickname        # 값 객체
    profile: Profile          # 값 객체 (이모지)
    password_hash: str
    balance: Balance          # 값 객체 (포인트)
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

```python
# src/bzero/domain/value_objects.py
@dataclass(frozen=True)
class Id:
    value: str

@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self):
        # 이메일 형식 검증
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", self.value):
            raise ValueError("Invalid email format")

@dataclass(frozen=True)
class Nickname:
    value: str

    def __post_init__(self):
        # 2-10자 검증
        if not (2 <= len(self.value) <= 10):
            raise ValueError("Nickname must be 2-10 characters")

@dataclass(frozen=True)
class Balance:
    value: int

    def __post_init__(self):
        # 음수 방지
        if self.value < 0:
            raise ValueError("Balance cannot be negative")
```

```python
# src/bzero/domain/repositories/user.py (인터페이스)
class UserRepository(ABC):
    @abstractmethod
    async def create(self, user: User) -> User: ...

    @abstractmethod
    async def get_by_id(self, user_id: Id) -> User | None: ...

    @abstractmethod
    async def get_by_email(self, email: Email) -> User | None: ...

    @abstractmethod
    async def get_by_nickname(self, nickname: Nickname) -> User | None: ...

    @abstractmethod
    async def exists_by_email(self, email: Email) -> bool: ...

    @abstractmethod
    async def exists_by_nickname(self, nickname: Nickname) -> bool: ...
```

#### 2. Infrastructure Layer

```python
# src/bzero/infrastructure/db/user_model.py (ORM)
class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    nickname: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    profile_emoji: Mapped[str] = mapped_column(String(10), nullable=False)
    current_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
```

```python
# src/bzero/infrastructure/repositories/user.py
class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user: User) -> User:
        user_model = self._to_model(user)  # 엔티티 → ORM 변환
        self.session.add(user_model)
        await self.session.flush()
        await self.session.refresh(user_model)
        return self._to_entity(user_model)  # ORM → 엔티티 변환

    async def get_by_id(self, user_id: Id) -> User | None:
        stmt = select(UserModel).where(UserModel.id == user_id.value)
        result = await self.session.execute(stmt)
        user_model = result.scalar_one_or_none()
        return self._to_entity(user_model) if user_model else None

    def _to_entity(self, model: UserModel) -> User:
        """ORM 모델을 도메인 엔티티로 변환"""
        return User(
            id=Id(model.id),
            email=Email(model.email),
            nickname=Nickname(model.nickname),
            profile=Profile(model.profile_emoji),
            password_hash=model.password_hash,
            balance=Balance(model.current_points),
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: User) -> UserModel:
        """도메인 엔티티를 ORM 모델로 변환"""
        return UserModel(
            id=entity.id.value,
            email=entity.email.value,
            nickname=entity.nickname.value,
            profile_emoji=entity.profile.value,
            password_hash=entity.password_hash,
            current_points=entity.balance.value,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
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
- **예외 처리**: 도메인 예외 → HTTP 예외 변환 (Presentation Layer에서)
- **보안**: 비밀번호는 bcrypt 해싱, JWT 토큰 사용, 환경 변수로 민감 정보 관리
- **타입 힌트**: 모든 함수와 메서드에 타입 힌트 필수

### 네이밍 컨벤션

- 클래스: `PascalCase` (예: `User`, `UserRepository`)
- 함수/변수: `snake_case` (예: `get_user`, `user_id`)
- 상수: `UPPER_SNAKE_CASE` (예: `MAX_RETRY_COUNT`)

---

## 자주 사용하는 명령어

### 개발 서버

```bash
# 개발 서버 실행 (http://0.0.0.0:8000)
uv run dev

# Swagger UI: http://0.0.0.0:8000/docs
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

- PostgreSQL 실행 확인: `pg_ctl status`
- `.env`의 `DATABASE_URL` 확인
- DB 생성: `createdb bzero_dev`

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
- **Clean Architecture**: https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
- **UUID v7 (RFC 9562)**: https://www.rfc-editor.org/rfc/rfc9562.html
