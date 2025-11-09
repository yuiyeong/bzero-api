# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

bzero-api는 FastAPI 기반의 비동기 웹 API 프로젝트입니다. PostgreSQL 데이터베이스와 Redis를 사용하며, Celery를 통한 백그라운드 작업 처리를 지원합니다.

## 기술 스택

- **웹 프레임워크**: FastAPI (비동기)
- **데이터베이스**: PostgreSQL + SQLAlchemy (비동기 postgresql-asyncpg)
- **마이그레이션**: Alembic
- **백그라운드 작업**: Celery + Redis
- **인증**: Passlib (bcrypt)
- **ID 생성**: UUID v7 (uuid-utils 또는 uuid6 라이브러리)
- **설정 관리**: Pydantic Settings + python-dotenv
- **패키지 관리**: uv

## 개발 명령어

### 개발 서버 실행
```bash
uv run dev
```
개발 서버는 `0.0.0.0:8000`에서 실행되며 코드 변경 시 자동 재시작됩니다.

### 린팅 및 포매팅
```bash
# 린팅 (자동 수정 포함)
uv run ruff check --fix .

# 포매팅
uv run ruff format .
```

### 테스트
```bash
# 전체 테스트 실행
uv run pytest

# 특정 테스트 파일 실행
uv run pytest tests/test_example.py

# 특정 테스트 함수 실행
uv run pytest tests/test_example.py::test_function_name
```

### 데이터베이스 마이그레이션
```bash
# 마이그레이션 파일 생성 (autogenerate)
uv run alembic revision --autogenerate -m "migration message"

# 마이그레이션 적용
uv run alembic upgrade head

# 마이그레이션 롤백
uv run alembic downgrade -1
```

### Pre-commit
```bash
# pre-commit 훅 설치
uv run pre-commit install

# 모든 파일에 대해 수동 실행
uv run pre-commit run --all-files
```

## 코드 구조 및 아키텍처

### 프로젝트 레이아웃
```
src/bzero/           # 메인 애플리케이션 패키지
├── main.py          # FastAPI 애플리케이션 엔트리포인트
├── config.py        # 설정 관리 (Pydantic Settings)
├── database.py      # 데이터베이스 연결 및 세션 관리
├── celery_app.py    # Celery 애플리케이션 설정
├── models/          # SQLAlchemy 모델
├── schemas/         # Pydantic 스키마 (요청/응답 DTO)
├── routers/         # FastAPI 라우터 (API 엔드포인트)
├── services/        # 비즈니스 로직
├── auth/            # 인증/인가 관련 코드
└── tasks/           # Celery 백그라운드 작업

migrations/          # Alembic 마이그레이션 파일
```

### 아키텍처 패턴

**레이어드 아키텍처**:
- **Router Layer** (`routers/`): API 엔드포인트 정의, 요청/응답 처리
- **Service Layer** (`services/`): 비즈니스 로직 구현
- **Model Layer** (`models/`): 데이터베이스 모델 정의
- **Schema Layer** (`schemas/`): 요청/응답 검증 및 직렬화

**주요 원칙**:
- 비동기 I/O 우선 사용 (SQLAlchemy async, FastAPI async endpoints)
- 의존성 주입을 통한 데이터베이스 세션 관리
- Pydantic을 활용한 타입 안정성 및 검증
- UUID v7을 기본 ID로 사용 (RFC 9562 표준)

## 코드 스타일 및 컨벤션

### Ruff 설정
- **Python 버전**: 3.12
- **라인 길이**: 120자
- **Import 정렬**: isort 규칙 적용
  - 섹션 순서: future → standard-library → third-party → first-party → local-folder
  - imports 후 2줄 공백
- **활성화된 규칙**: flake8-builtins, flake8-bugbear, flake8-comprehensions, pycodestyle, pyflakes, isort, pep8-naming, pylint 등

### 특별히 허용된 패턴
- **전역 변수 사용** (PLW0603 무시): 데이터베이스 연결 관리 등에서 필요
- **5개 이상의 함수 인자** (PLR0913 무시): 복잡한 함수 시그니처 허용

### Import 컨벤션
```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
```

## 데이터베이스 관련 주의사항

### 비동기 SQLAlchemy 사용
- `AsyncSession`을 사용하여 비동기 데이터베이스 작업 수행
- 모든 데이터베이스 쿼리는 `await` 키워드와 함께 사용
- `select()`, `insert()`, `update()`, `delete()` 등의 SQLAlchemy 2.0 스타일 사용

### Alembic 마이그레이션
- `migrations/env.py`에서 모델 메타데이터를 올바르게 설정해야 autogenerate가 작동
- 마이그레이션 파일은 항상 검토 후 커밋
- 마이그레이션 메시지는 명확하고 설명적으로 작성

## 환경 변수 및 설정

프로젝트는 `.env` 파일을 통해 환경 변수를 관리합니다. `config.py`에서 Pydantic Settings를 사용하여 타입 안전한 설정 관리를 구현합니다.

필요한 환경 변수 예시:
- `DATABASE_URL`: PostgreSQL 연결 문자열
- `REDIS_URL`: Redis 연결 문자열
- `SECRET_KEY`: JWT 등 암호화에 사용할 비밀 키

## 인증 및 보안

- Passlib의 bcrypt를 사용한 비밀번호 해싱
- JWT 또는 세션 기반 인증 구현 권장
- 민감한 정보(API 키, 토큰, 비밀번호 등)는 절대 코드에 하드코딩하지 않음
