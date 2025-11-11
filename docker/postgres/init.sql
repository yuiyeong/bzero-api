-- B0 Database Initialization Script
-- PostgreSQL 17
--
-- UUID v7 Note:
-- PostgreSQL 17에는 gen_random_uuid() 네이티브 함수가 없습니다.
-- 애플리케이션(Python)에서 uuid7 라이브러리로 UUID v7을 생성하는 것을 권장합니다.
-- 이 스크립트에서는 gen_random_uuid()를 사용하지만, 실제 운영에서는
-- 애플리케이션 레벨에서 UUID v7을 생성하여 INSERT 시 명시적으로 전달합니다.
--
-- Encoding:
-- docker-compose.yml의 POSTGRES_INITDB_ARGS로 UTF-8 인코딩이 설정됩니다.
-- 컨테이너 재생성 시 자동으로 UTF-8로 초기화됩니다.

-- ============================================================================
-- ENUM Types
-- ============================================================================

-- TICKET ENUMs
CREATE TYPE ticket_type_enum AS ENUM ('NORMAL', 'EXPRESS');
CREATE TYPE ticket_status_enum AS ENUM ('PURCHASED', 'TRAVELING', 'ARRIVED', 'EXPIRED');

-- GUESTHOUSE ENUMs
CREATE TYPE guesthouse_type_enum AS ENUM ('MIXED', 'QUIET');

-- ROOM ENUMs
CREATE TYPE room_status_enum AS ENUM ('ACTIVE', 'FULL');

-- ROOM_STAY ENUMs
CREATE TYPE room_stay_status_enum AS ENUM ('CHECKED_IN', 'CHECKED_OUT');

-- CHAT_MESSAGE ENUMs
CREATE TYPE message_type_enum AS ENUM ('TEXT', 'CARD_SHARED', 'SYSTEM');

-- DIRECT_MESSAGE_ROOM ENUMs
CREATE TYPE dm_room_status_enum AS ENUM ('PENDING', 'ACCEPTED', 'REJECTED', 'ACTIVE', 'ENDED');

-- POINT_TRANSACTION ENUMs
CREATE TYPE transaction_type_enum AS ENUM ('EARN', 'SPEND');
CREATE TYPE transaction_reason_enum AS ENUM ('SIGNUP', 'DIARY', 'QUESTIONNAIRE', 'TICKET', 'EXTENSION');
CREATE TYPE transaction_status_enum AS ENUM ('PENDING', 'COMPLETED', 'FAILED');

-- ============================================================================
-- Tables
-- ============================================================================

-- USER Table
CREATE TABLE users
(
    user_id        UUID PRIMARY KEY      DEFAULT gen_random_uuid(),
    email          VARCHAR(255) NOT NULL UNIQUE,
    password_hash  VARCHAR(255) NOT NULL,
    nickname       VARCHAR(50)  NOT NULL UNIQUE,
    profile_emoji  VARCHAR(10)  NOT NULL,
    current_points INTEGER      NOT NULL DEFAULT 1000,
    is_active      BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMP    NOT NULL DEFAULT NOW(),
    deleted_at     TIMESTAMP NULL,

    CONSTRAINT nickname_length CHECK (char_length(nickname) BETWEEN 2 AND 10),
    CONSTRAINT points_non_negative CHECK (current_points >= 0)
);

-- CITY Table
CREATE TABLE cities
(
    city_id       UUID PRIMARY KEY      DEFAULT gen_random_uuid(),
    name          VARCHAR(100) NOT NULL,
    theme         VARCHAR(100) NOT NULL,
    description   TEXT NULL,
    image_url     VARCHAR(500) NULL,
    is_active     BOOLEAN      NOT NULL DEFAULT FALSE,
    phase         INTEGER      NOT NULL DEFAULT 1,
    display_order INTEGER      NOT NULL,
    created_at    TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMP    NOT NULL DEFAULT NOW(),
    deleted_at    TIMESTAMP NULL,

    CONSTRAINT phase_valid CHECK (phase IN (1, 2))
);

-- TICKET Table
CREATE TABLE tickets
(
    ticket_id      UUID PRIMARY KEY            DEFAULT gen_random_uuid(),
    user_id        UUID               NOT NULL,
    city_id        UUID               NOT NULL,
    ticket_type    ticket_type_enum   NOT NULL,
    ticket_number  VARCHAR(20)        NOT NULL UNIQUE,
    cost_points    INTEGER            NOT NULL,
    departure_time TIMESTAMP          NOT NULL,
    arrival_time   TIMESTAMP          NOT NULL,
    status         ticket_status_enum NOT NULL DEFAULT 'PURCHASED',
    created_at     TIMESTAMP          NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMP          NOT NULL DEFAULT NOW(),
    deleted_at     TIMESTAMP NULL,

    CONSTRAINT fk_ticket_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    CONSTRAINT fk_ticket_city FOREIGN KEY (city_id) REFERENCES cities (city_id) ON DELETE CASCADE,
    CONSTRAINT cost_points_positive CHECK (cost_points > 0),
    CONSTRAINT arrival_after_departure CHECK (arrival_time > departure_time)
);

-- GUESTHOUSE Table
CREATE TABLE guesthouses
(
    guesthouse_id   UUID PRIMARY KEY              DEFAULT gen_random_uuid(),
    city_id         UUID                 NOT NULL,
    name            VARCHAR(100)         NOT NULL,
    guesthouse_type guesthouse_type_enum NOT NULL,
    description     TEXT NULL,
    image_url       VARCHAR(500) NULL,
    is_active       BOOLEAN              NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP            NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP            NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMP NULL,

    CONSTRAINT fk_guesthouse_city FOREIGN KEY (city_id) REFERENCES cities (city_id) ON DELETE CASCADE
);

-- ROOM Table
CREATE TABLE rooms
(
    room_id          UUID PRIMARY KEY          DEFAULT gen_random_uuid(),
    guesthouse_id    UUID             NOT NULL,
    room_name        VARCHAR(100)     NOT NULL,
    room_number      INTEGER          NOT NULL,
    max_capacity     INTEGER          NOT NULL DEFAULT 6,
    current_capacity INTEGER          NOT NULL DEFAULT 0,
    status           room_status_enum NOT NULL DEFAULT 'ACTIVE',
    created_at       TIMESTAMP        NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMP        NOT NULL DEFAULT NOW(),
    deleted_at       TIMESTAMP NULL,

    CONSTRAINT fk_room_guesthouse FOREIGN KEY (guesthouse_id) REFERENCES guesthouses (guesthouse_id) ON DELETE CASCADE,
    CONSTRAINT capacity_check CHECK (current_capacity <= max_capacity),
    CONSTRAINT capacity_non_negative CHECK (current_capacity >= 0),
    CONSTRAINT max_capacity_positive CHECK (max_capacity > 0),
    CONSTRAINT unique_room_number UNIQUE (guesthouse_id, room_number)
);

-- ROOM_STAY Table
CREATE TABLE room_stays
(
    stay_id                 UUID PRIMARY KEY               DEFAULT gen_random_uuid(),
    room_id                 UUID                  NOT NULL,
    user_id                 UUID                  NOT NULL,
    ticket_id               UUID                  NOT NULL,
    check_in_time           TIMESTAMP             NOT NULL,
    scheduled_checkout_time TIMESTAMP             NOT NULL,
    actual_checkout_time    TIMESTAMP NULL,
    extension_count         INTEGER               NOT NULL DEFAULT 0,
    total_extension_cost    INTEGER               NOT NULL DEFAULT 0,
    status                  room_stay_status_enum NOT NULL DEFAULT 'CHECKED_IN',
    created_at              TIMESTAMP             NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP             NOT NULL DEFAULT NOW(),
    deleted_at              TIMESTAMP NULL,

    CONSTRAINT fk_stay_room FOREIGN KEY (room_id) REFERENCES rooms (room_id) ON DELETE CASCADE,
    CONSTRAINT fk_stay_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    CONSTRAINT fk_stay_ticket FOREIGN KEY (ticket_id) REFERENCES tickets (ticket_id) ON DELETE CASCADE,
    CONSTRAINT extension_non_negative CHECK (extension_count >= 0),
    CONSTRAINT extension_cost_non_negative CHECK (total_extension_cost >= 0),
    CONSTRAINT checkout_after_checkin CHECK (scheduled_checkout_time > check_in_time),
    CONSTRAINT actual_checkout_after_checkin CHECK (actual_checkout_time IS NULL OR actual_checkout_time > check_in_time)
);

-- CONVERSATION_CARD Table
CREATE TABLE conversation_cards
(
    card_id    UUID PRIMARY KEY   DEFAULT gen_random_uuid(),
    city_id    UUID NULL,
    question   TEXT      NOT NULL,
    category   VARCHAR(100) NULL,
    phase      INTEGER   NOT NULL DEFAULT 1,
    is_active  BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP NULL,

    CONSTRAINT fk_card_city FOREIGN KEY (city_id) REFERENCES cities (city_id) ON DELETE CASCADE,
    CONSTRAINT phase_valid CHECK (phase IN (1, 2))
);

-- CHAT_MESSAGE Table
CREATE TABLE chat_messages
(
    message_id   UUID PRIMARY KEY           DEFAULT gen_random_uuid(),
    room_id      UUID              NOT NULL,
    user_id      UUID              NOT NULL,
    content      TEXT              NOT NULL,
    card_id      UUID NULL,
    message_type message_type_enum NOT NULL DEFAULT 'TEXT',
    is_system    BOOLEAN           NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMP         NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMP         NOT NULL DEFAULT NOW(),
    deleted_at   TIMESTAMP NULL,
    expires_at   TIMESTAMP         NOT NULL,

    CONSTRAINT fk_message_room FOREIGN KEY (room_id) REFERENCES rooms (room_id) ON DELETE CASCADE,
    CONSTRAINT fk_message_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    CONSTRAINT fk_message_card FOREIGN KEY (card_id) REFERENCES conversation_cards (card_id) ON DELETE SET NULL,
    CONSTRAINT content_length CHECK (char_length(content) <= 300)
);

-- DIRECT_MESSAGE_ROOM Table
CREATE TABLE direct_message_rooms
(
    dm_room_id    UUID PRIMARY KEY             DEFAULT gen_random_uuid(),
    guesthouse_id UUID                NOT NULL,
    room_id       UUID                NOT NULL,
    user1_id      UUID                NOT NULL,
    user2_id      UUID                NOT NULL,
    status        dm_room_status_enum NOT NULL DEFAULT 'PENDING',
    created_at    TIMESTAMP           NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMP           NOT NULL DEFAULT NOW(),
    deleted_at    TIMESTAMP NULL,
    started_at    TIMESTAMP NULL,
    ended_at      TIMESTAMP NULL,

    CONSTRAINT fk_dm_room_guesthouse FOREIGN KEY (guesthouse_id) REFERENCES guesthouses (guesthouse_id) ON DELETE CASCADE,
    CONSTRAINT fk_dm_room_room FOREIGN KEY (room_id) REFERENCES rooms (room_id) ON DELETE CASCADE,
    CONSTRAINT fk_dm_room_user1 FOREIGN KEY (user1_id) REFERENCES users (user_id) ON DELETE CASCADE,
    CONSTRAINT fk_dm_room_user2 FOREIGN KEY (user2_id) REFERENCES users (user_id) ON DELETE CASCADE,
    CONSTRAINT different_users CHECK (user1_id != user2_id
)
    );

-- DIRECT_MESSAGE Table
CREATE TABLE direct_messages
(
    dm_id        UUID PRIMARY KEY   DEFAULT gen_random_uuid(),
    dm_room_id   UUID      NOT NULL,
    from_user_id UUID      NOT NULL,
    to_user_id   UUID      NOT NULL,
    content      TEXT      NOT NULL,
    is_read      BOOLEAN   NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at   TIMESTAMP NULL,

    CONSTRAINT fk_dm_room FOREIGN KEY (dm_room_id) REFERENCES direct_message_rooms (dm_room_id) ON DELETE CASCADE,
    CONSTRAINT fk_dm_from_user FOREIGN KEY (from_user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    CONSTRAINT fk_dm_to_user FOREIGN KEY (to_user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    CONSTRAINT content_length CHECK (char_length(content) <= 300),
    CONSTRAINT different_users CHECK (from_user_id != to_user_id
)
    );

-- DIARY Table
CREATE TABLE diaries
(
    diary_id          UUID PRIMARY KEY   DEFAULT gen_random_uuid(),
    user_id           UUID      NOT NULL,
    title             VARCHAR(255) NULL,
    content           TEXT      NOT NULL,
    mood              VARCHAR(50) NULL,
    diary_date        DATE      NOT NULL,
    city_id           UUID NULL,
    has_earned_points BOOLEAN   NOT NULL DEFAULT FALSE,
    created_at        TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at        TIMESTAMP NULL,

    CONSTRAINT fk_diary_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    CONSTRAINT fk_diary_city FOREIGN KEY (city_id) REFERENCES cities (city_id) ON DELETE SET NULL,
    CONSTRAINT content_length CHECK (char_length(content) <= 500),
    CONSTRAINT unique_user_diary_date UNIQUE (user_id, diary_date)
);

-- QUESTIONNAIRE Table
CREATE TABLE questionnaires
(
    questionnaire_id  UUID PRIMARY KEY   DEFAULT gen_random_uuid(),
    user_id           UUID      NOT NULL,
    city_id           UUID      NOT NULL,
    question_1_answer TEXT NULL,
    question_2_answer TEXT NULL,
    question_3_answer TEXT NULL,
    has_earned_points BOOLEAN   NOT NULL DEFAULT FALSE,
    created_at        TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at        TIMESTAMP NULL,

    CONSTRAINT fk_questionnaire_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    CONSTRAINT fk_questionnaire_city FOREIGN KEY (city_id) REFERENCES cities (city_id) ON DELETE CASCADE,
    CONSTRAINT answer1_length CHECK (question_1_answer IS NULL OR char_length(question_1_answer) <= 200),
    CONSTRAINT answer2_length CHECK (question_2_answer IS NULL OR char_length(question_2_answer) <= 200),
    CONSTRAINT answer3_length CHECK (question_3_answer IS NULL OR char_length(question_3_answer) <= 200),
    CONSTRAINT unique_user_city UNIQUE (user_id, city_id)
);

-- POINT_TRANSACTION Table
CREATE TABLE point_transactions
(
    transaction_id   UUID PRIMARY KEY                 DEFAULT gen_random_uuid(),
    user_id          UUID                    NOT NULL,
    transaction_type transaction_type_enum   NOT NULL,
    amount           INTEGER                 NOT NULL,
    reason           transaction_reason_enum NOT NULL,
    reference_type   VARCHAR(50) NULL,
    reference_id     UUID NULL,
    balance_before   INTEGER                 NOT NULL,
    balance_after    INTEGER                 NOT NULL,
    status           transaction_status_enum NOT NULL DEFAULT 'COMPLETED',
    description      TEXT NULL,
    created_at       TIMESTAMP               NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMP               NOT NULL DEFAULT NOW(),
    deleted_at       TIMESTAMP NULL,

    CONSTRAINT fk_transaction_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    CONSTRAINT amount_non_zero CHECK (amount != 0
) ,
    CONSTRAINT balance_non_negative CHECK (balance_before >= 0 AND balance_after >= 0)
);

-- ============================================================================
-- Indexes
-- ============================================================================

-- USER Indexes
CREATE INDEX idx_user_email ON users (email) WHERE deleted_at IS NULL;
CREATE INDEX idx_user_nickname ON users (nickname) WHERE deleted_at IS NULL;
CREATE INDEX idx_user_active_created ON users (is_active, created_at) WHERE deleted_at IS NULL;

-- CITY Indexes
CREATE INDEX idx_city_active_display ON cities (is_active, display_order) WHERE deleted_at IS NULL;
CREATE INDEX idx_city_phase ON cities (phase) WHERE deleted_at IS NULL;

-- TICKET Indexes
CREATE INDEX idx_ticket_user_created ON tickets (user_id, created_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_ticket_status_arrival ON tickets (status, arrival_time) WHERE deleted_at IS NULL;
CREATE INDEX idx_ticket_number ON tickets (ticket_number) WHERE deleted_at IS NULL;

-- GUESTHOUSE Indexes
CREATE INDEX idx_guesthouse_city_type_active ON guesthouses (city_id, guesthouse_type, is_active) WHERE deleted_at IS NULL;
CREATE INDEX idx_guesthouse_city_active ON guesthouses (city_id, is_active) WHERE deleted_at IS NULL;

-- ROOM Indexes
CREATE INDEX idx_room_guesthouse_status_capacity ON rooms (guesthouse_id, status, current_capacity) WHERE deleted_at IS NULL;
CREATE INDEX idx_room_guesthouse_number ON rooms (guesthouse_id, room_number) WHERE deleted_at IS NULL;

-- ROOM_STAY Indexes
CREATE INDEX idx_stay_room_status ON room_stays (room_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_stay_user_status ON room_stays (user_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_stay_scheduled_checkout ON room_stays (scheduled_checkout_time) WHERE deleted_at IS NULL;

-- CHAT_MESSAGE Indexes
CREATE INDEX idx_message_room_created ON chat_messages (room_id, created_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_message_expires ON chat_messages (expires_at) WHERE deleted_at IS NULL;

-- CONVERSATION_CARD Indexes
CREATE INDEX idx_card_city_active ON conversation_cards (city_id, is_active) WHERE deleted_at IS NULL;
CREATE INDEX idx_card_phase_active ON conversation_cards (phase, is_active) WHERE deleted_at IS NULL;

-- DIRECT_MESSAGE_ROOM Indexes
CREATE INDEX idx_dm_room_room_status ON direct_message_rooms (room_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_dm_room_guesthouse_status ON direct_message_rooms (guesthouse_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_dm_room_user2_status ON direct_message_rooms (user2_id, status) WHERE deleted_at IS NULL;

-- DIRECT_MESSAGE Indexes
CREATE INDEX idx_dm_room_created ON direct_messages (dm_room_id, created_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_dm_to_user_read ON direct_messages (to_user_id, is_read) WHERE deleted_at IS NULL;

-- DIARY Indexes
CREATE INDEX idx_diary_user_date ON diaries (user_id, diary_date) WHERE deleted_at IS NULL;
CREATE INDEX idx_diary_user_created ON diaries (user_id, created_at) WHERE deleted_at IS NULL;

-- QUESTIONNAIRE Indexes
CREATE INDEX idx_questionnaire_user_city ON questionnaires (user_id, city_id) WHERE deleted_at IS NULL;

-- POINT_TRANSACTION Indexes
CREATE INDEX idx_transaction_user_created ON point_transactions (user_id, created_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_transaction_user_type ON point_transactions (user_id, transaction_type) WHERE deleted_at IS NULL;

-- ============================================================================
-- Triggers for updated_at
-- ============================================================================

CREATE
OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at
= NOW();
RETURN NEW;
END;
$$
language 'plpgsql';

-- Apply updated_at trigger to all tables
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE
    ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_cities_updated_at
    BEFORE UPDATE
    ON cities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_tickets_updated_at
    BEFORE UPDATE
    ON tickets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_guesthouses_updated_at
    BEFORE UPDATE
    ON guesthouses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_rooms_updated_at
    BEFORE UPDATE
    ON rooms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_room_stays_updated_at
    BEFORE UPDATE
    ON room_stays
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_chat_messages_updated_at
    BEFORE UPDATE
    ON chat_messages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_conversation_cards_updated_at
    BEFORE UPDATE
    ON conversation_cards
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_direct_message_rooms_updated_at
    BEFORE UPDATE
    ON direct_message_rooms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_direct_messages_updated_at
    BEFORE UPDATE
    ON direct_messages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_diaries_updated_at
    BEFORE UPDATE
    ON diaries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_questionnaires_updated_at
    BEFORE UPDATE
    ON questionnaires
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_point_transactions_updated_at
    BEFORE UPDATE
    ON point_transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
