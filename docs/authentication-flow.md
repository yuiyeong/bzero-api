## 인증 시스템 설계

### 1. 아키텍처

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Frontend   │ ←──→ │   Supabase   │      │   FastAPI    │
│   (React)    │      │     Auth     │      │   Backend    │
└──────────────┘      └──────────────┘      └──────────────┘
       │                                           │
       │          JWT 토큰 첨부하여 API 호출           │
       └──────────────────────────────────────────→│
                                                   ↓
                                            ┌──────────────┐
                                            │  PostgreSQL  │
                                            └──────────────┘
```

### 2. 역할 분담

| 역할               | 담당                          |
|------------------|-----------------------------|
| 이메일/소셜 인증        | Frontend + Supabase SDK     |
| Access Token 발급  | Supabase                    |
| Refresh Token 발급 | Supabase                    |
| Access Token 갱신  | Supabase SDK (자동)           |
| 토큰 저장            | Supabase SDK (localStorage) |
| JWT 검증           | Backend                     |
| 사용자 데이터 저장       | Backend → PostgreSQL        |

### 3. 테이블 설계

```
┌──────────────────┐       ┌─────────────────────┐
│      users       │       │   user_identities   │
├──────────────────┤       ├─────────────────────┤
│ id (PK)          │←──────│ user_id (FK)        │
│ email            │       │ provider            │  ← 'email', 'google', 'kakao'
│ nickname         │       │ provider_user_id    │  ← Supabase auth user id
│ profile_emoji    │       │ provider_email      │
│ created_at       │       │ created_at          │
│ updated_at       │       └─────────────────────┘
└──────────────────┘
```

**분리 이유:**

- 한 사용자가 여러 인증 방식 연동 가능 (이메일 + Google + Kakao)
- Supabase 종속성 제거 (나중에 다른 Auth로 마이그레이션 용이)
- 업계 표준 패턴 (Federated Identity)

### 4. API 설계

| Method | Endpoint    | 설명        | 호출 시점               |
|--------|-------------|-----------|---------------------|
| POST   | `/users/me` | 신규 사용자 등록 | 첫 로그인 후 (404 받았을 때) |
| GET    | `/users/me` | 현재 사용자 조회 | 인증 후 사용자 확인         |
| PATCH  | `/users/me` | 프로필 업데이트  | 온보딩 완료 시            |

### 5. 회원가입 플로우 (2단계)

```
1단계: Supabase 인증              2단계: 온보딩
┌─────────────────────┐         ┌─────────────────────┐
│ - 이메일/비밀번호       │    →    │ - 닉네임 (필수)        │
│ - 또는 소셜 로그인      │         │ - 프로필 이미지        │
│                     │         │                     │
│ (Supabase 처리)      │         │ (Backend API 처리)   │
└─────────────────────┘         └─────────────────────┘
```

### 6. 프로필 완료 여부 판단

별도 컬럼 없이 **필수 필드(nickname) null 여부**로 판단:

```python
@property
def is_profile_complete(self) -> bool:
    return self.nickname is not None
```

### 7. 토큰 관리 흐름

```
[로그인]
Supabase → Access Token (1시간) + Refresh Token (60일) 발급
                    ↓
           Frontend localStorage에 저장 (SDK가 자동 처리)

[API 호출]
Frontend: getSession() → 만료 확인 → 필요시 자동 갱신 → Backend 호출
Backend: JWT 검증만

[토큰 만료 시]
Supabase SDK가 Refresh Token으로 새 Access Token 자동 발급
```

### 8. Frontend 흐름

```
[첫 로그인 (회원가입)]
Supabase 인증 완료
     │
     ├─ GET /users/me → 404 Not Found
     │
     ├─ POST /users/me → 201 Created
     │
     └─ is_profile_complete: false → /onboarding
                                          │
                                    PATCH /users/me/profile
                                          │
                                     /dashboard

[기존 사용자 로그인]
Supabase 인증 완료
     │
     ├─ GET /users/me → 200 OK
     │
     ├─ is_profile_complete: true → /dashboard
     │
     └─ is_profile_complete: false → /onboarding
```
