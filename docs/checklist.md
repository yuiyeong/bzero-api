# B0 Backend 구현 체크리스트

> bzero-api 백엔드 기능 구현을 위한 상세 체크리스트입니다.
> GitHub 이슈 생성 시 참고하세요.

---

## 0. 환경설정 ✅

- [x] FastAPI 프로젝트 구조 설정
- [x] PostgreSQL 연결 설정
- [x] Redis 연결 설정
- [x] Alembic 마이그레이션 설정
- [x] 비동기 SQLAlchemy 설정
- [x] UUID v7 지원 설정
- [x] 환경 변수 관리 (.env)

### 개발 환경 설정

- [ ] docker-compose.yml 을 활용한 개발 환경 설정
- [ ] ddl 작성

---

## 1. 온보딩 & 회원가입

### User 모델 구현 ✅
- [x] User 엔티티 생성 (domain/entities/user.py)
- [x] 값 객체 생성 (Email, Nickname, Profile, Balance)
- [x] User 테이블 마이그레이션

### UserRepository 구현 ✅
- [x] UserRepository 인터페이스 (domain/repositories/user.py)
- [x] SqlAlchemyUserRepository 구현체 (infrastructure/repositories/user.py)
- [x] UUID로 사용자 조회
- [x] 이메일로 사용자 조회
- [x] 닉네임으로 사용자 조회
- [x] 사용자 생성
- [x] 이메일 중복 검사
- [x] 닉네임 중복 검사

### PointTransaction 시스템 구현
- [ ] PointTransaction 엔티티 생성 (domain/entities/point_transaction.py)
- [ ] 값 객체 생성 (TransactionType, TransactionReason, TransactionStatus)
- [ ] PointTransactionRepository 인터페이스 (domain/repositories/point_transaction.py)
- [ ] PointTransaction ORM 모델 (infrastructure/db/point_transaction_model.py)
- [ ] SqlAlchemyPointTransactionRepository 구현체 (infrastructure/repositories/point_transaction.py)
- [ ] PointTransactionService 도메인 서비스 (domain/services/point_transaction_service.py)
  - [ ] earn_points() 메서드 (포인트 획득 + 거래 기록)
  - [ ] spend_points() 메서드 (포인트 차감 + 거래 기록)
- [ ] PointTransaction 테이블 마이그레이션

### 보안 인프라 구현 (Clean Architecture)
- [ ] PasswordHasher 인터페이스 (domain/services/password_hasher.py)
- [ ] BcryptPasswordHasher 구현체 (infrastructure/security/bcrypt_password_hasher.py)
- [ ] 도메인 에러 추가 (DuplicateEmailError, DuplicateNicknameError, InvalidPasswordError)

### 회원가입 UseCase 구현
- [ ] RegisterUserCommand DTO (application/dtos/user_dto.py)
- [ ] RegisterUserUseCase 구현 (application/use_cases/register_user.py)
  - [ ] 비밀번호 8자 이상 검증
  - [ ] Value Object 생성 및 검증
  - [ ] 이메일/닉네임 중복 확인
  - [ ] 비밀번호 해싱 (PasswordHasher 사용)
  - [ ] User 엔티티 생성 및 저장
  - [ ] PointTransactionService로 1000P 지급

### API 엔드포인트 구현
- [ ] RegisterRequest/UserResponse 스키마 (presentation/schemas/auth.py)
- [ ] POST /api/v1/auth/register 엔드포인트 (presentation/api/v1/auth.py)
- [ ] 의존성 주입 설정 (core/dependencies.py)
- [ ] 라우터 등록 (main.py)

### 테스트 작성
- [ ] PointTransactionService 단위 테스트
- [ ] PointTransactionRepository 통합 테스트
- [ ] BcryptPasswordHasher 단위 테스트
- [ ] RegisterUserUseCase 단위 테스트
- [ ] 회원가입 API 통합 테스트

### 완료 조건
- [ ] 회원가입이 정상적으로 완료됨
- [ ] 가입 후 1000포인트가 자동 지급됨 (PointTransaction 기록 포함)
- [ ] 이메일 중복 검사가 작동함
- [ ] 닉네임 중복 검사가 작동함
- [ ] 비밀번호가 안전하게 해싱되어 저장됨
- [ ] 프로필 이모지가 저장됨
- [ ] 모든 테스트가 통과함

---

## 2. B0 비행선 터미널 & 도시 선택

### City 모델 구현
- [ ] City 엔티티 생성 (city_id, name, theme, description, image_url, is_active, display_order)
- [ ] City 테이블 마이그레이션

### CityRepository 구현
- [ ] ID로 도시 조회
- [ ] 활성 도시 목록 조회

### 도시 시드 데이터 생성
- [ ] 세렌시아 (관계의 도시)
- [ ] 로렌시아 (회복의 도시)
- [ ] 나머지 4개 도시 (is_active=false)

### API 엔드포인트 구현
- [ ] GET /api/cities (활성 도시 목록)
- [ ] GET /api/cities/{city_id} (도시 상세 정보)

### 완료 조건
- [ ] 2개 도시 데이터가 DB에 저장됨
- [ ] 도시 목록 API가 작동함
- [ ] 도시 상세 정보 API가 작동함

---

## 3. 비행선 티켓 구매

### Ticket 모델 구현
- [ ] Ticket 엔티티 생성 (ticket_id, user_id, city_id, ticket_type, ticket_number, cost_points, departure_time, arrival_time, status)
- [ ] 값 객체 생성 (TicketType, TravelDuration, TicketStatus)
- [ ] Ticket 테이블 마이그레이션

### TicketRepository 구현
- [ ] ID로 티켓 조회
- [ ] 사용자 ID로 티켓 조회
- [ ] 상태별 티켓 조회
- [ ] 티켓 생성
- [ ] 티켓 상태 업데이트

### PointTransaction 모델 구현
- [ ] PointTransaction 엔티티 생성 (transaction_id, user_id, transaction_type, amount, reason, reference_type, reference_id, balance_before, balance_after, status, description)
- [ ] 값 객체 생성 (TransactionType, TransactionReason, TransactionStatus)
- [ ] PointTransaction 테이블 마이그레이션

### PointTransactionRepository 구현
- [ ] 거래 기록 생성
- [ ] 사용자별 거래 내역 조회

### PointTransactionService 구현
- [ ] 포인트 획득 로직
- [ ] 포인트 사용 로직 (잔액 확인, 차감)
- [ ] 트랜잭션 처리
- [ ] 동시성 제어

### 티켓 구매 로직 구현
- [ ] 포인트 잔액 확인
- [ ] 포인트 차감 (300P/500P)
- [ ] 티켓 발급 (티켓 번호 생성: "B0-{년도}-{6자리}")
- [ ] 출발/도착 시간 계산 (일반 3h, 쾌속 1h)
- [ ] 도착 시 자동 체크인 스케줄링 (Celery 태스크)

### API 엔드포인트 구현
- [ ] POST /api/tickets/purchase (티켓 구매)
- [ ] GET /api/tickets/my (내 티켓 조회)
- [ ] GET /api/tickets/{ticket_id} (티켓 상세)

### 완료 조건
- [ ] 포인트 결제가 정상 작동함
- [ ] 포인트 부족 시 에러 반환
- [ ] 티켓이 제대로 발급됨
- [ ] 도착 시간에 자동 체크인이 스케줄링됨

---

## 4. 게스트하우스 - 6명 룸

### Guesthouse 모델 구현
- [ ] Guesthouse 엔티티 생성 (guesthouse_id, city_id, name, guesthouse_type, description, image_url, is_active)
- [ ] Guesthouse 테이블 마이그레이션

### Room 모델 구현
- [ ] Room 엔티티 생성 (room_id, guesthouse_id, room_name, room_number, max_capacity, current_capacity, status, deleted_at)
- [ ] 값 객체 생성 (RoomCapacity, RoomStatus)
- [ ] Room 테이블 마이그레이션
- [ ] Soft delete 지원 (deleted_at)

### RoomStay 모델 구현
- [ ] RoomStay 엔티티 생성 (stay_id, room_id, user_id, ticket_id, check_in_time, scheduled_checkout_time, actual_checkout_time, extension_count, total_extension_cost, status)
- [ ] 값 객체 생성 (RoomStayStatus)
- [ ] RoomStay 테이블 마이그레이션

### GuesthouseRepository 구현
- [ ] ID로 게스트하우스 조회
- [ ] 도시별 게스트하우스 조회

### RoomRepository 구현
- [ ] ID로 룸 조회
- [ ] 게스트하우스별 룸 목록 조회
- [ ] 가용 룸 조회 (6명 미만, deleted_at IS NULL)
- [ ] 룸 생성
- [ ] 룸 정원 업데이트
- [ ] 룸 soft delete

### RoomStayRepository 구현
- [ ] 체류 생성
- [ ] 활성 체류 조회 (user_id, room_id)
- [ ] 체크아웃 예정 체류 조회
- [ ] 체류 업데이트

### RoomAssignmentService 구현
- [ ] 가용 룸 찾기 로직 (6명 미만)
- [ ] 새 룸 생성 로직
- [ ] 자동 룸 배정 로직
- [ ] Race Condition 방지 (트랜잭션)
- [ ] 룸 정원 업데이트 (current_capacity 증가)
- [ ] 6명 도달 시 룸 상태 FULL로 변경

### 체크인 로직 구현
- [ ] 티켓 도착 처리
- [ ] 자동 룸 배정 (RoomAssignmentService)
- [ ] RoomStay 생성 (check_in_time, scheduled_checkout_time = +24h)
- [ ] UserCheckedIn 이벤트 발행

### 게스트하우스 시드 데이터 생성
- [ ] 세렌시아 게스트하우스
- [ ] 로렌시아 게스트하우스

### API 엔드포인트 구현
- [ ] GET /api/guesthouses/{city_id} (도시별 게스트하우스)
- [ ] POST /api/rooms/check-in (체크인)
- [ ] GET /api/rooms/my-stay (내 활성 체류 조회)
- [ ] GET /api/rooms/{room_id} (룸 정보)

### 완료 조건
- [ ] 6명 룸 자동 분배 로직이 작동함
- [ ] 동시 입장 시에도 정확히 작동함
- [ ] 체크인 API가 정상 작동함

---

## 5. 사랑방 - 단체 채팅

### ChatMessage 모델 구현
- [ ] ChatMessage 엔티티 생성 (message_id, room_id, user_id, content, card_id, message_type, is_system, expires_at)
- [ ] 값 객체 생성 (MessageContent, MessageType)
- [ ] ChatMessage 테이블 마이그레이션

### ConversationCard 모델 구현
- [ ] ConversationCard 엔티티 생성 (card_id, city_id, question, category, phase, is_active)
- [ ] ConversationCard 테이블 마이그레이션

### ChatMessageRepository 구현
- [ ] 메시지 생성
- [ ] 룸별 최근 메시지 조회 (페이지네이션, 50개)
- [ ] 만료된 메시지 조회 및 삭제 (3일 경과)

### ConversationCardRepository 구현
- [ ] 도시별 카드 조회
- [ ] 활성 카드 조회
- [ ] 랜덤 카드 선택

### 대화 카드 시드 데이터 생성
- [ ] 세렌시아 카드 10장
- [ ] 로렌시아 카드 10장
- [ ] 공용 카드 10장

### RateLimitingService 구현
- [ ] Redis 기반 Rate Limiting
- [ ] 메시지 전송 제한 (2초에 1회)
- [ ] 키 형식: `rate_limit:chat:{user_id}:{room_id}`
- [ ] 제한 초과 시 429 에러

### MessageExpirationService 구현
- [ ] 3일 경과 메시지 검색
- [ ] 만료 메시지 일괄 삭제
- [ ] Celery 배치 작업 (매일 실행)

### WebSocket 구현
- [ ] WebSocket 연결 관리
- [ ] 룸별 채널 관리
- [ ] 실시간 메시지 브로드캐스트
- [ ] 접속자 수 업데이트

### API 엔드포인트 구현
- [ ] POST /api/chat/messages (메시지 전송)
- [ ] GET /api/chat/messages/{room_id} (채팅 히스토리)
- [ ] GET /api/chat/cards/random/{city_id} (랜덤 카드 뽑기)
- [ ] POST /api/chat/cards/share (카드 공유)
- [ ] WebSocket /ws/chat/{room_id}

### 완료 조건
- [ ] 채팅 메시지가 DB에 저장됨
- [ ] 채팅 히스토리 조회가 작동함
- [ ] 3일 이전 메시지가 자동 삭제됨
- [ ] 대화 카드를 랜덤으로 뽑을 수 있음
- [ ] WebSocket으로 실시간 메시지 전송이 작동함

---

## 6. 라운지 - 1:1 대화

### DirectMessageRoom 모델 구현
- [ ] DirectMessageRoom 엔티티 생성 (dm_room_id, guesthouse_id, room_id, user1_id, user2_id, status, started_at, ended_at)
- [ ] 값 객체 생성 (DMStatus)
- [ ] DirectMessageRoom 테이블 마이그레이션

### DirectMessage 모델 구현
- [ ] DirectMessage 엔티티 생성 (dm_id, dm_room_id, from_user_id, to_user_id, content, is_read)
- [ ] DirectMessage 테이블 마이그레이션

### DirectMessageRoomRepository 구현
- [ ] 대화방 생성
- [ ] 룸별, 사용자별 대화방 조회
- [ ] 대화방 상태 업데이트
- [ ] 체크아웃 시 대화방 삭제

### DirectMessageRepository 구현
- [ ] 메시지 생성
- [ ] 대화방별 메시지 조회
- [ ] 읽음 처리

### 1:1 대화 로직 구현
- [ ] 대화 신청 (PENDING)
- [ ] 대화 수락 (ACCEPTED → ACTIVE)
- [ ] 대화 거절 (REJECTED)
- [ ] 메시지 전송
- [ ] 같은 룸 내에서만 대화 가능 검증

### WebSocket 구현
- [ ] 1:1 대화방 WebSocket 연결
- [ ] 실시간 메시지 전송
- [ ] 대화 신청/수락/거절 알림

### API 엔드포인트 구현
- [ ] GET /api/dm/room-members (같은 룸 여행자 목록)
- [ ] POST /api/dm/request (대화 신청)
- [ ] POST /api/dm/accept/{dm_room_id} (대화 수락)
- [ ] POST /api/dm/reject/{dm_room_id} (대화 거절)
- [ ] POST /api/dm/messages (메시지 전송)
- [ ] GET /api/dm/messages/{dm_room_id} (메시지 조회)
- [ ] WebSocket /ws/dm/{dm_room_id}

### 완료 조건
- [ ] 같은 룸 여행자 목록 API가 작동함
- [ ] 대화 신청/수락/거절이 작동함
- [ ] 1:1 메시지가 DB에 저장됨
- [ ] 체크아웃 시 대화 기록이 삭제됨
- [ ] WebSocket으로 실시간 메시지 전송이 작동함

---

## 7. 개인 숙소

### Diary 모델 구현
- [ ] Diary 엔티티 생성 (diary_id, user_id, title, content, mood, diary_date, city_id, has_earned_points)
- [ ] 값 객체 생성 (DiaryContent, DiaryMood)
- [ ] Diary 테이블 마이그레이션
- [ ] UNIQUE(user_id, diary_date) 제약 조건

### Questionnaire 모델 구현
- [ ] Questionnaire 엔티티 생성 (questionnaire_id, user_id, city_id, question_1_answer, question_2_answer, question_3_answer, has_earned_points)
- [ ] 값 객체 생성 (QuestionAnswer)
- [ ] Questionnaire 테이블 마이그레이션
- [ ] UNIQUE(user_id, city_id) 제약 조건

### DiaryRepository 구현
- [ ] 일기 생성
- [ ] 사용자별 일기 조회
- [ ] 특정 날짜 일기 조회 (중복 방지)

### QuestionnaireRepository 구현
- [ ] 문답지 생성
- [ ] 사용자별 문답지 조회
- [ ] 도시별 문답지 조회 (중복 방지)

### CityQuestionService 구현
- [ ] 도시별 질문 관리 (코드 기반)
- [ ] 세렌시아 질문 3개
- [ ] 로렌시아 질문 3개

### 일기/문답지 작성 로직 구현
- [ ] 일기 작성 (하루 1회 포인트 획득)
- [ ] 문답지 작성 (도시별 1회 포인트 획득)
- [ ] 포인트 지급 (PointTransactionService)
- [ ] 중복 포인트 지급 방지

### API 엔드포인트 구현
- [ ] POST /api/diary (일기 작성)
- [ ] GET /api/diary/today (오늘 일기 조회)
- [ ] GET /api/questionnaire/questions/{city_id} (도시별 질문 조회)
- [ ] POST /api/questionnaire (문답지 작성)
- [ ] GET /api/questionnaire/{city_id} (도시별 문답지 조회)

### 완료 조건
- [ ] 일기 작성 시 포인트가 지급됨
- [ ] 문답지 작성 시 포인트가 지급됨
- [ ] 중복 포인트 지급이 방지됨
- [ ] 일기와 문답지가 DB에 저장됨

---

## 8. 포인트 시스템

### 포인트 규칙 검증
- [ ] 회원가입 시 1000P 지급 확인
- [ ] 일기 작성 시 50P 지급 (하루 1회)
- [ ] 문답지 작성 시 50P 지급 (도시별 1회)
- [ ] 티켓 구매 시 포인트 차감 (300P/500P)
- [ ] 체류 연장 시 포인트 차감 (300P)

### 포인트 잔액 동기화
- [ ] User 테이블의 current_points 실시간 업데이트
- [ ] 트랜잭션 처리로 동시성 제어
- [ ] 음수 잔액 방지

### API 엔드포인트 구현
- [ ] GET /api/points/balance (현재 잔액)
- [ ] GET /api/points/transactions (거래 내역)

### 완료 조건
- [ ] 포인트가 정확히 지급됨
- [ ] 포인트가 정확히 차감됨
- [ ] 중복 지급이 방지됨
- [ ] 음수 잔액이 방지됨
- [ ] 동시성 문제가 발생하지 않음

---

## 9. 체크아웃 시스템

### StayExtensionService 구현
- [ ] 포인트 검증 (300P 이상)
- [ ] 포인트 차감 (PointTransactionService)
- [ ] scheduled_checkout_time에 24시간 추가
- [ ] extension_count 증가
- [ ] total_extension_cost에 300P 누적
- [ ] StayExtended 이벤트 발행

### CheckoutService 구현
- [ ] 체크인 시 24시간 후 체크아웃 예약 (Celery 태스크)
- [ ] 23시간 후 알림 발송 (NotificationService)
- [ ] 자동 체크아웃 처리
  - [ ] RoomStay 상태를 CHECKED_OUT으로 변경
  - [ ] actual_checkout_time 기록
  - [ ] Room의 current_capacity 감소
  - [ ] 1:1 대화방 삭제
  - [ ] 마지막 여행자 체크아웃 시 룸 soft delete (deleted_at 설정)
- [ ] UserCheckedOut 이벤트 발행

### NotificationService 구현
- [ ] 체크아웃 1시간 전 알림 생성
- [ ] Celery 태스크 스케줄링
- [ ] 연장 시 기존 알림 취소 및 재예약

### 룸 삭제 배치 작업
- [ ] deleted_at 설정된 룸 검색
- [ ] 일정 기간 경과 후 실제 삭제
- [ ] Celery 배치 작업 (매일 실행)

### API 엔드포인트 구현
- [ ] POST /api/rooms/extend (체류 연장)
- [ ] POST /api/rooms/checkout (수동 체크아웃)
- [ ] GET /api/rooms/checkout-time (체크아웃 시간 조회)

### 완료 조건
- [ ] 연장 시 포인트가 차감되고 체크아웃 시간이 24시간 추가됨
- [ ] 포인트 부족 시 연장 불가
- [ ] 여러 번 연장이 가능함
- [ ] 연장 시 같은 룸이 유지됨
- [ ] 체크아웃 시간 도달 시 자동 체크아웃됨

---

## 10. 데이터 수집

### Analytics 모델 구현
- [ ] UserActivity 엔티티 (activity_id, user_id, activity_type, metadata, timestamp)
- [ ] 테이블 마이그레이션

### 데이터 수집 로직 구현
- [ ] DAU (일일 활성 사용자) 추적
- [ ] 도시별 방문 수 추적
- [ ] 평균 체류 시간 계산
- [ ] 채팅 활성도 추적 (메시지 수)
- [ ] 일기 작성률 추적

### 개인정보 보호
- [ ] 채팅/일기/문답지 내용은 수집하지 않음
- [ ] 개인 식별 정보 암호화
- [ ] 익명화된 통계만 저장

### 기능 ON/OFF 관리
- [ ] FeatureFlag 모델 (feature_id, feature_name, is_enabled)
- [ ] 대화 카드 활성화/비활성화
- [ ] Admin API로 기능 제어

### API 엔드포인트 구현
- [ ] GET /api/admin/analytics/dau (DAU)
- [ ] GET /api/admin/analytics/cities (도시별 방문)
- [ ] GET /api/admin/analytics/avg-stay (평균 체류 시간)
- [ ] GET /api/admin/analytics/chat-activity (채팅 활성도)
- [ ] GET /api/admin/feature-flags (기능 플래그 조회)
- [ ] PUT /api/admin/feature-flags/{feature_id} (기능 플래그 수정)

### 완료 조건
- [ ] 주요 행동이 추적됨
- [ ] 기본 통계 API가 작동함
- [ ] 기능 ON/OFF가 즉시 반영됨
- [ ] 개인정보가 보호됨
- [ ] 채팅/일기 내용은 수집되지 않음

---

## 11. 통합 테스트 및 배포

### 단위 테스트 작성
- [ ] 모델 테스트
- [ ] 리포지토리 테스트
- [ ] 서비스 테스트
- [ ] API 엔드포인트 테스트

### 통합 테스트 작성
- [ ] 회원가입 → 로그인 플로우
- [ ] 티켓 구매 → 체크인 플로우
- [ ] 채팅 → 메시지 전송 플로우
- [ ] 일기/문답지 → 포인트 획득 플로우
- [ ] 체류 연장 → 체크아웃 플로우

### 부하 테스트
- [ ] 동시 접속자 100명 테스트
- [ ] 채팅 메시지 전송 부하 테스트
- [ ] 룸 배정 동시성 테스트

### Docker 설정
- [ ] Dockerfile 작성
- [ ] docker-compose.yml 작성 (PostgreSQL, Redis, Celery)

### 배포 준비
- [ ] 환경 변수 설정 (Production)
- [ ] 로깅 설정
- [ ] 에러 핸들링
- [ ] CORS 설정

### 완료 조건
- [ ] 모든 단위 테스트 통과
- [ ] 모든 통합 테스트 통과
- [ ] 부하 테스트 통과 (100명 동시 접속)
- [ ] Docker 컨테이너로 실행 가능
- [ ] Production 환경 배포 완료

---

## 참고 문서

- **MVP 기능 명세**: `/docs/01-mvp.md`
- **도메인 모델**: `/bzero-api/docs/domain-model.md`
- **ERD**: `/bzero-api/docs/erd.md`

---

## GitHub 이슈 생성 가이드

각 기능별로 다음과 같이 GitHub 이슈를 생성하세요:

**제목 형식**: `[h2 제목] h3 제목인 기능`

**예시**:
- `[환경설정] 개발 환경 설정`
- `[온보딩 & 회원가입] User 모델 구현`

**라벨**:
- `feature`: 새로운 기능
- `priority-high` / `priority-medium` / `priority-low`: 우선순위

**마일스톤**: `MVP Phase 1`

**체크리스트**: 이 문서의 해당 섹션 복사
