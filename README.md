# bzero-api

B0의 Backend 서버 - FastAPI 기반 비동기 웹 API

## 소개

bzero-api는 FastAPI를 사용하여 구축된 고성능 비동기 웹 API 서버입니다. PostgreSQL 데이터베이스와 Redis를 활용하며, Celery를 통한 백그라운드 작업 처리를 지원합니다.

## 주요 기술 스택

- **웹 프레임워크**: FastAPI (비동기)
- **데이터베이스**: PostgreSQL + SQLAlchemy (비동기)
- **마이그레이션**: Alembic
- **백그라운드 작업**: Celery + Redis
- **인증**: Supabase Auth (JWT)
- **패키지 관리**: uv
- **코드 품질**: Ruff (린터/포매터), pre-commit

## 요구사항

- Python 3.12 이상
- PostgreSQL
- Redis
- uv (패키지 관리)

## 설치

### 1. 저장소 클론

```bash
git clone <repository-url>
cd bzero-api
```

### 2. 의존성 설치

```bash
uv sync
```

### 3. 환경 변수 설정

`.env` 파일을 생성하고 필요한 환경 변수를 설정합니다:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
```

### 4. 데이터베이스 마이그레이션

```bash
uv run alembic upgrade head
```

## 실행

### 개발 서버 실행

```bash
uv run dev
```

서버가 실행되면 다음 주소에서 접근할 수 있습니다:
- API 서버: http://localhost:8000
- Swagger UI 문서: http://localhost:8000/docs
- ReDoc 문서: http://localhost:8000/redoc

### Celery 워커 실행 (백그라운드 작업)

```bash
uv run celery -A bzero.celery_app worker --loglevel=info
```

## 개발 가이드

### 코드 스타일

이 프로젝트는 Ruff를 사용하여 코드 품질을 관리합니다.

```bash
# 린팅 (자동 수정 포함)
uv run ruff check --fix .

# 포매팅
uv run ruff format .
```

### Pre-commit 훅

커밋 전 자동으로 코드 품질 검사를 실행합니다:

```bash
# 설치
uv run pre-commit install

# 수동 실행
uv run pre-commit run --all-files
```

### 테스트

```bash
# 전체 테스트 실행
uv run pytest

# 특정 테스트 파일 실행
uv run pytest tests/test_example.py

# 특정 테스트 함수 실행
uv run pytest tests/test_example.py::test_function_name

# 커버리지와 함께 실행
uv run pytest --cov=bzero --cov-report=html
```

### 데이터베이스 마이그레이션

```bash
# 마이그레이션 파일 생성
uv run alembic revision --autogenerate -m "설명"

# 마이그레이션 적용
uv run alembic upgrade head

# 마이그레이션 롤백
uv run alembic downgrade -1

# 마이그레이션 히스토리 확인
uv run alembic history
```

## 프로젝트 구조

이 프로젝트는 **Clean Architecture + Domain-Driven Design (DDD)** 원칙을 따릅니다.

```
bzero-api/
├── src/
│   └── bzero/                # 메인 애플리케이션 패키지
│       ├── domain/           # 도메인 계층 (순수 비즈니스 로직)
│       │   ├── entities/     # 도메인 엔티티 (User, City, Room 등)
│       │   ├── value_objects/# 값 객체 (Email, Nickname 등)
│       │   ├── repositories/ # 리포지토리 인터페이스 (추상 클래스)
│       │   ├── services/     # 도메인 서비스
│       │   └── errors.py     # 도메인 예외
│       │
│       ├── application/      # 애플리케이션 계층 (유스케이스)
│       │   ├── use_cases/    # 유스케이스 (users/, cities/ 하위 디렉토리)
│       │   └── results/      # 유스케이스 결과 객체
│       │
│       ├── infrastructure/   # 인프라 계층 (외부 시스템 연동)
│       │   ├── auth/         # JWT 유틸리티 (Supabase JWT 검증)
│       │   ├── db/           # SQLAlchemy ORM 모델
│       │   └── repositories/ # 리포지토리 구현체
│       │
│       ├── presentation/     # 프레젠테이션 계층 (API)
│       │   ├── api/          # API 엔드포인트 (라우터)
│       │   ├── middleware/   # 미들웨어 (로깅, 에러 핸들링)
│       │   └── schemas/      # Pydantic 스키마 (요청/응답)
│       │
│       ├── core/             # 공통 설정
│       │
│       └── main.py           # FastAPI 앱 엔트리포인트
│
├── migrations/               # Alembic 마이그레이션
│   └── versions/             # 마이그레이션 파일
├── tests/                    # 테스트 코드
│   ├── unit/                 # 단위 테스트
│   ├── integration/          # 통합 테스트
│   └── conftest.py           # 테스트 설정
├── .env                      # 환경 변수 (git 무시)
├── .env.template             # 환경 변수 템플릿
├── pyproject.toml            # 프로젝트 설정 및 의존성
├── alembic.ini               # Alembic 설정
├── ruff.toml                 # Ruff 설정
└── .pre-commit-config.yaml   # Pre-commit 설정
```

### Clean Architecture 계층별 역할

```
Presentation → Application → Domain ← Infrastructure
```

- **Domain**: 순수 비즈니스 로직 (외부 의존성 없음)
- **Application**: 유스케이스 (도메인 엔티티 조합)
- **Infrastructure**: DB, 외부 API 연동 (Domain 인터페이스 구현)
- **Presentation**: HTTP 요청/응답 처리

## 주요 기능

- RESTful API 엔드포인트
- 비동기 데이터베이스 작업
- JWT 기반 인증 (Supabase Auth)
- 백그라운드 작업 처리
- 자동 API 문서 생성 (Swagger/ReDoc)
- 데이터베이스 마이그레이션 관리
