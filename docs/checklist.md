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

- [x] docker-compose.yml 을 활용한 개발 환경 설정
- [x] ddl 작성

---

## 1. 온보딩 & 회원가입 ✅

### User 모델 구현 ✅
- [x] User 엔티티 생성 (domain/entities/user.py)
- [x] UserIdentity 엔티티 생성 (domain/entities/user_identity.py)
- [x] 값 객체 생성 (Email, Nickname, Profile, Balance, AuthProvider)
- [x] User, UserIdentity 테이블 마이그레이션

### UserRepository 구현 ✅
- [x] UserRepository 인터페이스 (domain/repositories/user.py)
- [x] UserIdentityRepository 인터페이스 (domain/repositories/user_identity.py)
- [x] SqlAlchemyUserRepository 구현체 (infrastructure/repositories/user.py)
- [x] SqlAlchemyUserIdentityRepository 구현체 (infrastructure/repositories/user_identity.py)
- [x] UUID로 사용자 조회
- [x] 이메일로 사용자 조회
- [x] 닉네임으로 사용자 조회
- [x] 사용자 생성/수정
- [x] 이메일 중복 검사
- [x] 닉네임 중복 검사

### PointTransaction 시스템 구현 ✅
- [x] PointTransaction 엔티티 생성 (domain/entities/point_transaction.py)
- [x] 값 객체 생성 (TransactionType, TransactionReason, TransactionStatus, TransactionReference)
- [x] PointTransactionRepository 인터페이스 (domain/repositories/point_transaction.py)
- [x] PointTransaction ORM 모델 (infrastructure/db/point_transaction_model.py)
- [x] SqlAlchemyPointTransactionRepository 구현체 (infrastructure/repositories/point_transaction.py)
- [x] PointTransactionService 도메인 서비스 (domain/services/point_transaction.py)
  - [x] earn_points() 메서드 (포인트 획득 + 거래 기록)
  - [x] spend_points() 메서드 (포인트 차감 + 거래 기록)
- [x] PointTransaction 테이블 마이그레이션

### 인증 시스템 구현 (Supabase Auth) ✅
- [x] Supabase JWT 검증 (infrastructure/auth/jwt.py)
- [x] UserService 도메인 서비스 (domain/services/user.py)
  - [x] get_or_create_user_by_provider() 메서드
  - [x] get_user_by_id() 메서드
  - [x] update_user() 메서드
- [x] CreateUserUseCase 구현 (application/use_cases/users/create_user.py)
  - [x] Supabase 사용자 정보로 User/UserIdentity 생성
  - [x] PointTransactionService로 1000P 지급
- [x] GetMeUseCase 구현 (application/use_cases/users/get_me.py)
- [x] UpdateUserUseCase 구현 (application/use_cases/users/update_user.py)

### API 엔드포인트 구현 ✅
- [x] UserResponse 스키마 (presentation/schemas/user.py)
- [x] POST /api/v1/users 엔드포인트 (사용자 생성)
- [x] GET /api/v1/users/me 엔드포인트 (내 정보 조회)
- [x] PATCH /api/v1/users/me 엔드포인트 (내 정보 수정)
- [x] 의존성 주입 설정 (presentation/api/dependencies.py)
- [x] 라우터 등록 (main.py)

### 테스트 작성 ✅
- [x] UserService 단위 테스트
- [x] PointTransactionService 단위 테스트
- [x] UserRepository 통합 테스트
- [x] UserIdentityRepository 통합 테스트
- [x] PointTransactionRepository 통합 테스트
- [x] PointTransactionService 통합 테스트
- [x] User API E2E 테스트

### 완료 조건 ✅
- [x] Supabase Auth를 통한 사용자 인증이 작동함
- [x] 최초 로그인 시 User/UserIdentity가 생성됨
- [x] 가입 후 1000포인트가 자동 지급됨 (PointTransaction 기록 포함)
- [x] 닉네임 중복 검사가 작동함
- [x] 프로필 이모지가 저장됨
- [x] 모든 테스트가 통과함

---

## 2. B0 비행선 터미널 & 도시 선택 ✅

### City 모델 구현 ✅
- [x] City 엔티티 생성 (city_id, name, theme, description, image_url, is_active, display_order)
- [x] City 테이블 마이그레이션

### CityRepository 구현 ✅
- [x] CityRepository 인터페이스 (domain/repositories/city.py)
- [x] SqlAlchemyCityRepository 구현체 (infrastructure/repositories/city.py)
- [x] ID로 도시 조회
- [x] 활성 도시 목록 조회

### CityService 구현 ✅
- [x] CityService 도메인 서비스 (domain/services/city.py)
  - [x] get_active_cities() 메서드
  - [x] get_city_by_id() 메서드

### City UseCase 구현 ✅
- [x] GetActiveCitiesUseCase 구현 (application/use_cases/cities/get_active_cities.py)
- [x] GetCityByIdUseCase 구현 (application/use_cases/cities/get_city_by_id.py)

### 도시 시드 데이터 생성 ✅
- [x] 시드 스크립트 작성 (scripts/seed_cities.py)
- [x] 세렌시아 (관계의 도시)
- [x] 로렌시아 (회복의 도시)
- [x] 나머지 4개 도시 (is_active=false)

### API 엔드포인트 구현 ✅
- [x] CityResponse 스키마 (presentation/schemas/city.py)
- [x] GET /api/v1/cities (활성 도시 목록)
- [x] GET /api/v1/cities/{city_id} (도시 상세 정보)
- [x] 의존성 주입 설정 (presentation/api/dependencies.py)

### 테스트 작성 ✅
- [x] City 엔티티 단위 테스트
- [x] City UseCase 단위 테스트
- [x] CityRepository 통합 테스트
- [x] City API E2E 테스트

### 완료 조건 ✅
- [x] 6개 도시 데이터가 시드 스크립트로 생성됨 (2개 활성, 4개 비활성)
- [x] 도시 목록 API가 작동함
- [x] 도시 상세 정보 API가 작동함

---

## 3. 비행선 티켓 구매 ✅

### Airship 모델 구현 ✅
- [x] Airship 엔티티 생성 (airship_id, name, description, image_url, cost_factor, duration_factor, display_order, is_active)
- [x] Airship 테이블 마이그레이션
- [x] AirshipRepository 인터페이스 (domain/repositories/airship.py)
- [x] SqlAlchemyAirshipRepository 구현체 (infrastructure/repositories/airship.py)
- [x] AirshipService 도메인 서비스 (domain/services/airship.py)
  - [x] get_active_airships() 메서드
  - [x] get_airship_by_id() 메서드

### City 모델 수정 ✅
- [x] City 엔티티에 base_cost_points, base_duration_hours 속성 추가
- [x] City 테이블 마이그레이션 (ALTER TABLE)
- [x] 도시 시드 데이터 업데이트 (base_cost_points, base_duration_hours 설정)

### Airship 시드 데이터 생성 ✅
- [x] 일반 비행선 (cost_factor: 1.0, duration_factor: 3.0)
- [x] 고속 비행선 (cost_factor: 2.0, duration_factor: 1.0)

### Ticket 모델 구현 ✅
- [x] Ticket 엔티티 생성 (user_id, city_snapshot, airship_snapshot, cost_points, status, departure_datetime, arrival_datetime)
- [x] 값 객체 생성 (TicketStatus: BOARDING, COMPLETED, CANCELLED, CitySnapshot, AirshipSnapshot)
- [x] Ticket 테이블 마이그레이션

### TicketRepository 구현 ✅
- [x] TicketRepository 인터페이스 (domain/repositories/ticket.py)
- [x] TicketSyncRepository 인터페이스 (domain/repositories/ticket_sync.py) - Celery용 동기 버전
- [x] SqlAlchemyTicketRepository 구현체 (infrastructure/repositories/ticket.py)
- [x] SqlAlchemyTicketSyncRepository 구현체 (infrastructure/repositories/ticket_sync.py)
- [x] ID로 티켓 조회
- [x] 사용자 ID로 티켓 조회
- [x] 상태별 티켓 조회 (현재 탑승 중인 티켓 조회)
- [x] 티켓 생성 및 상태 업데이트

### TicketService 구현 ✅
- [x] TicketService 도메인 서비스 (domain/services/ticket.py)
  - [x] calculate_cost() 메서드: City.base_cost_points × Airship.cost_factor
  - [x] calculate_duration() 메서드: City.base_duration_hours × Airship.duration_factor
  - [x] purchase_ticket() 메서드
  - [x] cancel_ticket() 메서드

### 티켓 구매 로직 구현 ✅
- [x] 포인트 잔액 확인
- [x] 비용 계산: City.base_cost_points × Airship.cost_factor
- [x] 포인트 차감 (PointTransactionService)
- [x] 시간 계산: City.base_duration_hours × Airship.duration_factor
- [x] 티켓 발급 (구매 즉시 BOARDING 상태)
- [x] 도착 시 자동 완료 스케줄링 (Celery 태스크)

### Celery Worker 구현 ✅
- [x] TaskScheduler 포트 인터페이스 (domain/ports/task_scheduler.py)
- [x] CeleryTaskScheduler 어댑터 (infrastructure/adapters/celery_task_scheduler.py)
- [x] FailoverTask 베이스 클래스 (worker/tasks/base.py)
- [x] complete_ticket_task 태스크 (worker/tasks/ticket.py)
- [x] TaskFailureLog 모델 및 마이그레이션

### API 엔드포인트 구현 ✅
- [x] GET /api/v1/airships (비행선 목록 조회)
- [x] POST /api/v1/tickets (티켓 구매 - city_id, airship_id 파라미터)
- [x] GET /api/v1/tickets (내 티켓 목록 조회)
- [x] GET /api/v1/tickets/current (현재 탑승 중인 티켓 조회)
- [x] GET /api/v1/tickets/{ticket_id} (티켓 상세)
- [x] POST /api/v1/tickets/{ticket_id}/cancel (티켓 취소)

### 테스트 작성 ✅
- [x] Airship 엔티티 단위 테스트
- [x] Ticket 엔티티 단위 테스트
- [x] TicketService 단위 테스트 (비용/시간 계산)
- [x] AirshipRepository 통합 테스트
- [x] TicketRepository 통합 테스트
- [x] TicketService 통합 테스트
- [x] Ticket UseCase 통합 테스트
- [x] Celery 태스크 통합 테스트
- [x] Ticket API E2E 테스트

### 완료 조건 ✅
- [x] 비행선 목록 API가 작동함
- [x] 비용이 City.base_cost_points × Airship.cost_factor로 계산됨
- [x] 이동 시간이 City.base_duration_hours × Airship.duration_factor로 계산됨
- [x] 포인트 결제가 정상 작동함
- [x] 포인트 부족 시 에러 반환
- [x] 티켓이 제대로 발급됨
- [x] 도착 시간에 자동 완료가 스케줄링됨 (Celery)

---

## 4. 게스트하우스 & 자동 체크인

### Guesthouse 모델 구현
- [x] Guesthouse 엔티티 생성 (guesthouse_id, city_id, name, guesthouse_type, description, image_url, is_active)
- [x] 값 객체 생성 (GuesthouseType: NORMAL - 추후 확장 가능)
- [x] GuesthouseRepository 인터페이스 (domain/repositories/guesthouse.py)
- [x] SqlAlchemyGuesthouseRepository 구현체 (infrastructure/repositories/guesthouse.py)
- [x] Guesthouse ORM 모델 (infrastructure/db/guesthouse_model.py)
- [x] Guesthouse 테이블 마이그레이션

### Room 모델 구현
- [x] Room 엔티티 생성 (room_id, guesthouse_id, max_capacity, current_capacity, status, created_at, updated_at, deleted_at)
- [x] RoomRepository 인터페이스 (domain/repositories/room.py)
- [x] RoomSyncRepository 인터페이스 (domain/repositories/room_sync.py) - Celery용 동기 버전
- [x] SqlAlchemyRoomRepository 구현체 (infrastructure/repositories/room.py)
- [x] SqlAlchemyRoomSyncRepository 구현체 (infrastructure/repositories/room_sync.py)
- [x] Room ORM 모델 (infrastructure/db/room_model.py)
- [x] Room 테이블 마이그레이션
- [x] Soft delete 지원 (deleted_at)

### RoomStay 모델 구현
- [x] RoomStay 엔티티 생성 (room_stay_id, room_id, user_id, ticket_id, check_in_at, scheduled_checkout_at, actual_checkout_at, extension_count, total_extension_cost, status)
- [x] 값 객체 생성 (RoomStayStatus: CHECKED_IN, CHECKED_OUT, EXTENDED)
- [x] RoomStayRepository 인터페이스 (domain/repositories/room_stay.py)
- [x] RoomStaySyncRepository 인터페이스 (domain/repositories/room_stay_sync.py) - Celery용 동기 버전
- [x] SqlAlchemyRoomStayRepository 구현체 (infrastructure/repositories/room_stay.py)
- [x] SqlAlchemyRoomStaySyncRepository 구현체 (infrastructure/repositories/room_stay_sync.py)
- [x] RoomStay ORM 모델 (infrastructure/db/room_stay_model.py)
- [x] RoomStay 테이블 마이그레이션

### GuesthouseRepository 구현
- [x] ID로 게스트하우스 조회
- [x] 도시 ID로 게스트하우스 조회 (도시당 1개)
- [x] 활성 게스트하우스 조회

### RoomRepository 구현
- [x] ID로 룸 조회
- [x] 게스트하우스별 가용 룸 조회 (current_capacity < max_capacity, deleted_at IS NULL, status = AVAILABLE)
- [x] 룸 생성
- [x] 룸 정원 업데이트 (current_capacity 증가/감소)
- [x] 룸 상태 업데이트 (AVAILABLE ↔ FULL)
- [x] 룸 soft delete (deleted_at 설정)

### RoomStayRepository 구현
- [x] 체류 생성
- [x] 사용자 ID로 활성 체류 조회 (status = ACTIVE)
- [x] 룸 ID로 활성 체류 목록 조회
- [x] 티켓 ID로 체류 조회
- [x] 체크아웃 예정 체류 조회 (scheduled_checkout_at 기준)
- [x] 체류 상태 업데이트

### 도메인 서비스 구현
- [x] GuestHouseSyncService
- [x] RoomSyncService
- [x] RoomStaySyncService

### 자동 체크인 로직 구현 (Celery Task)
- [x] check_in_task 태스크 (worker/tasks/check_in.py)
  - [x] 티켓 COMPLETED 상태 확인
  - [x] 해당 도시의 게스트하우스 조회
  - [x] RoomAssignmentService로 룸 배정
  - [x] RoomStay 생성 (check_in_at = now, scheduled_checkout_at = now + 24h)
  - [x] Room.current_capacity 증가
- [x] complete_ticket_task에서 check_in_task 호출 연동

### 게스트하우스 시드 데이터 생성
- [x] 시드 스크립트 작성 (scripts/seed_guesthouses.py)
- [x] 세렌시아 게스트하우스
- [x] 로렌시아 게스트하우스

### UseCase 구현
- [x] GetCurrentStayUseCase (application/use_cases/room_stays/get_current_stay.py)
- [x] GetRoomMembersUseCase (application/use_cases/rooms/get_room_members.py) - 같은 방 멤버 조회

### API 엔드포인트 구현
- [x] GET /api/v1/room-stays/current (내 활성 체류 조회)
- [x] GET /api/v1/rooms/{room_id}/members (같은 방 멤버 조회)

### 테스트 작성
- [x] Guesthouse 엔티티 단위 테스트
- [x] Room 엔티티 단위 테스트
- [x] RoomStay 엔티티 단위 테스트
- [x] RoomAssignmentService 단위 테스트
- [x] CheckInService 단위 테스트
- [x] GuesthouseRepository 통합 테스트
- [x] RoomRepository 통합 테스트
- [x] RoomStayRepository 통합 테스트
- [x] RoomAssignmentService 통합 테스트
- [x] check_in_task Celery 태스크 통합 테스트
- [x] Guesthouse API E2E 테스트
- [x] RoomStay API E2E 테스트

### 완료 조건
- [x] 티켓 완료(COMPLETED) 시 자동으로 해당 도시 게스트하우스에 체크인됨
- [x] 자동 룸 배정이 작동함 (6명 미만 룸에 배정, 없으면 새 룸 생성)
- [x] 동시 입장 시에도 Race Condition 없이 정확히 작동함
- [x] 체크인 시점에서 24시간 후 체크아웃이 스케줄링됨
- [x] 내 활성 체류 조회 API가 정상 작동함
- [x] 같은 방 멤버 조회 API가 정상 작동함

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
