# bzero-api (B0 Backend API)

B0 프로젝트의 백엔드 API 서버입니다. FastAPI와 Clean Architecture를 기반으로 구축되었습니다.

---

## 프로젝트 개요

**bzero-api**는 B0 프로젝트의 백엔드 API 서버로, 사용자 인증, 포인트 시스템, 도시 관리, 실시간 채팅, 일기/문답지 저장, 비행선 티켓 시스템을 담당합니다.

**핵심 아키텍처**: Clean Architecture + Domain-Driven Design (DDD)

---

## 기술 스택

- **FastAPI** 0.115.x - 비동기 웹 프레임워크
- **Python** 3.12+, **uv** - 패키지 관리
- **PostgreSQL** 16+ - 메인 데이터베이스
- **SQLAlchemy** 2.0+ - 비동기 ORM
- **Alembic** - 데이터베이스 마이그레이션
- **pytest** + **ruff** - 테스트 및 린팅

---

## 프로젝트 구조

```
bzero-api/
├── app/
│   ├── domain/              # 도메인 계층 (순수 비즈니스 로직)
│   │   ├── entities/        # User, City, Room 등
│   │   ├── value_objects/   # Email, Nickname 등
│   │   ├── repositories/    # 리포지토리 인터페이스 (추상 클래스)
│   │   ├── services/        # 도메인 서비스
│   │   └── exceptions/      # 도메인 예외
│   │
│   ├── application/         # 애플리케이션 계층 (유스케이스)
│   │   ├── use_cases/       # RegisterUser, PurchaseTicket 등
│   │   └── dtos/
│   │
│   ├── infrastructure/      # 인프라 계층 (외부 시스템 연동)
│   │   ├── db/
│   │   │   ├── models/      # SQLAlchemy ORM 모델
│   │   │   └── session.py
│   │   └── repositories/    # 리포지토리 구현체
│   │
│   ├── presentation/        # 프레젠테이션 계층 (API)
│   │   ├── api/v1/          # API 엔드포인트
│   │   └── schemas/         # Pydantic 스키마
│   │
│   ├── core/                # 공통 설정
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   └── security.py
│   │
│   └── main.py
│
├── alembic/                 # DB 마이그레이션
├── tests/                   # 테스트
├── .env                     # 환경 변수
└── pyproject.toml
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

### 개발 예시: 회원가입 기능

#### 1. Domain Layer

```python
# app/domain/entities/user.py
@dataclass
class User:
    id: str  # ULID
    email: Email  # 값 객체
    nickname: Nickname  # 값 객체
    points: int

    def add_points(self, amount: int) -> None:
        """비즈니스 로직"""
        if self.points + amount < 0:
            raise InsufficientPointsException()
        self.points += amount
```

```python
# app/domain/repositories/user_repository.py (인터페이스)
class UserRepository(ABC):
    @abstractmethod
    async def create(self, user: User) -> User: pass

    @abstractmethod
    async def get_by_email(self, email: Email) -> User | None: pass
```

#### 2. Application Layer

```python
# app/application/use_cases/register_user.py
class RegisterUserUseCase:
    def __init__(self, user_repository: UserRepository, password_service: PasswordService):
        self.user_repository = user_repository
        self.password_service = password_service

    async def execute(self, email: str, password: str, nickname: str, emoji: str) -> User:
        # 1. 값 객체 생성 (검증)
        email_vo = Email(email)
        nickname_vo = Nickname(nickname)

        # 2. 중복 확인
        if await self.user_repository.get_by_email(email_vo):
            raise DuplicateEmailException()

        # 3. User 엔티티 생성 및 저장
        user = User(id=str(ulid.ULID()), email=email_vo, ...)
        return await self.user_repository.create(user)
```

#### 3. Infrastructure Layer

```python
# app/infrastructure/db/models/user_model.py (ORM)
class UserModel(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    points: Mapped[int] = mapped_column(Integer, default=1000)
```

```python
# app/infrastructure/repositories/user_repository_impl.py
class UserRepositoryImpl(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user: User) -> User:
        user_model = self._to_model(user)  # 엔티티 → ORM 변환
        self.session.add(user_model)
        await self.session.commit()
        return self._to_entity(user_model)  # ORM → 엔티티 변환
```

#### 4. Presentation Layer

```python
# app/presentation/api/v1/auth.py
@router.post("/register", status_code=201)
async def register(
        request: RegisterRequest,
        use_case: RegisterUserUseCase = Depends(get_register_user_use_case)
):
    try:
        user = await use_case.execute(...)
        return UserResponse.from_entity(user)
    except DuplicateEmailException:
        raise HTTPException(status_code=409, detail="Email already exists")
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
- **ID 생성**: ULID 사용 (`str(ulid.ULID())`)
- **값 객체**: 불변 객체로 작성 (`@dataclass(frozen=True)`)
- **예외 처리**: 도메인 예외 → HTTP 예외 변환 (Presentation Layer에서)
- **보안**: 비밀번호는 bcrypt 해싱, JWT 토큰 사용, 환경 변수로 민감 정보 관리

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
uv run pytest --cov=app --cov-report=html
```

### 마이그레이션

```bash
# 생성
uv run alembic revision --autogenerate -m "Add User model"

# 적용
uv run alembic upgrade head

# 롤백
uv run alembic downgrade -1

# 히스토리 확인
uv run alembic history
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

- **프로젝트 문서**: `../docs/01-mvp.md`, `../docs/workflow.md`
- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy 2.0**: https://docs.sqlalchemy.org/en/20/
- **Clean Architecture**: https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
