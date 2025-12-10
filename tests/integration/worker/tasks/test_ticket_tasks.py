"""Celery 티켓 태스크 통합 테스트."""

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from uuid_utils import uuid7

from bzero.core.settings import get_settings
from bzero.domain.value_objects import TicketStatus
from bzero.infrastructure.db.airship_model import AirshipModel
from bzero.infrastructure.db.city_model import CityModel
from bzero.infrastructure.db.ticket_model import TicketModel
from bzero.infrastructure.db.user_model import UserModel
from bzero.worker.tasks.ticket import complete_ticket_task


@pytest.fixture
def timezone() -> ZoneInfo:
    """Seoul timezone"""
    return get_settings().timezone


def create_user_model(session: Session) -> UserModel:
    """테스트용 사용자 모델을 생성합니다."""
    now = datetime.now()
    user_model = UserModel(
        user_id=str(uuid7()),
        email="test@example.com",
        nickname="테스트유저",
        profile_emoji="🌟",
        current_points=1000,
        created_at=now,
        updated_at=now,
    )
    session.add(user_model)
    session.flush()
    return user_model


def create_city_model(session: Session) -> CityModel:
    """테스트용 도시 모델을 생성합니다."""
    now = datetime.now()
    city_model = CityModel(
        city_id=str(uuid7()),
        name="세렌시아",
        theme="관계",
        image_url="https://example.com/city.jpg",
        description="노을빛 항구 마을",
        base_cost_points=300,
        base_duration_hours=24,
        display_order=1,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    session.add(city_model)
    session.flush()
    return city_model


def create_airship_model(session: Session) -> AirshipModel:
    """테스트용 비행선 모델을 생성합니다."""
    now = datetime.now()
    airship_model = AirshipModel(
        airship_id=str(uuid7()),
        name="일반 비행선",
        description="편안한 여행",
        image_url="https://example.com/airship.jpg",
        cost_factor=1,
        duration_factor=1,
        display_order=1,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    session.add(airship_model)
    session.flush()
    return airship_model


def create_ticket_model(
    session: Session,
    user_id: str,
    city_id: str,
    airship_id: str,
    status: TicketStatus,
    timezone: ZoneInfo,
    ticket_id: str | None = None,
) -> TicketModel:
    """테스트용 티켓 모델을 생성합니다."""
    now = datetime.now(timezone)
    _ticket_id = ticket_id or str(uuid7())

    ticket_model = TicketModel(
        ticket_id=_ticket_id,
        user_id=user_id,
        ticket_number=f"B0-{now.year}-test123",
        cost_points=300,
        status=status.value,
        departure_datetime=now,
        arrival_datetime=now + timedelta(hours=24),
        city_id=city_id,
        city_name="세렌시아",
        city_theme="관계",
        city_image_url="https://example.com/city.jpg",
        city_description="노을빛 항구 마을",
        city_base_cost_points=300,
        city_base_duration_hours=24,
        airship_id=airship_id,
        airship_name="일반 비행선",
        airship_image_url="https://example.com/airship.jpg",
        airship_description="편안한 여행",
        airship_cost_factor=1.0,
        airship_duration_factor=1.0,
        created_at=now,
        updated_at=now,
    )

    session.add(ticket_model)
    session.flush()

    return ticket_model


@pytest.fixture
def sample_test_data(test_sync_session: Session) -> dict:
    """테스트에 필요한 기본 데이터(User, City, Airship)를 생성합니다."""
    user = create_user_model(test_sync_session)
    city = create_city_model(test_sync_session)
    airship = create_airship_model(test_sync_session)

    return {
        "user_id": str(user.user_id),
        "city_id": str(city.city_id),
        "airship_id": str(airship.airship_id),
    }


class TestCompleteTicketTask:
    """complete_ticket_task 태스크 통합 테스트"""

    def test_complete_ticket_success(
        self,
        test_sync_session: Session,
        sample_test_data: dict,
        timezone: ZoneInfo,
    ):
        """BOARDING 상태의 티켓을 COMPLETED로 변경할 수 있어야 합니다."""
        # Given: BOARDING 상태의 티켓 생성
        ticket_model = create_ticket_model(
            test_sync_session,
            user_id=sample_test_data["user_id"],
            city_id=sample_test_data["city_id"],
            airship_id=sample_test_data["airship_id"],
            status=TicketStatus.BOARDING,
            timezone=timezone,
        )
        ticket_id_hex = ticket_model.ticket_id

        # get_sync_db_session을 patch하여 test_sync_session 반환
        @contextmanager
        def mock_get_sync_db_session() -> Iterator[Session]:
            yield test_sync_session

        with patch(
            "bzero.worker.tasks.ticket.get_sync_db_session",
            mock_get_sync_db_session,
        ):
            # When: 태스크 직접 호출
            result = complete_ticket_task(ticket_id_hex)

        # Then: 성공 결과 확인
        assert result["ticket_id"] == ticket_id_hex
        assert result["result"] == "success"

        # DB에서 상태 확인
        stmt = select(TicketModel).where(TicketModel.ticket_id == ticket_id_hex)
        db_result = test_sync_session.execute(stmt)
        updated_ticket = db_result.scalar_one()
        assert updated_ticket.status == TicketStatus.COMPLETED.value

    def test_complete_ticket_not_found(
        self,
        test_sync_session: Session,
    ):
        """존재하지 않는 티켓 ID로 호출하면 실패해야 합니다."""
        # Given: 존재하지 않는 티켓 ID
        non_existent_ticket_id = str(uuid7())

        @contextmanager
        def mock_get_sync_db_session() -> Iterator[Session]:
            yield test_sync_session

        with patch(
            "bzero.worker.tasks.ticket.get_sync_db_session",
            mock_get_sync_db_session,
        ):
            # When: 태스크 직접 호출
            result = complete_ticket_task(non_existent_ticket_id)

        # Then: 실패 결과 확인
        assert result["ticket_id"] == non_existent_ticket_id
        assert "failed" in result["result"]
        assert "티켓" in result["result"]  # 한글 에러 메시지 확인

    def test_complete_ticket_invalid_status_purchased(
        self,
        test_sync_session: Session,
        sample_test_data: dict,
        timezone: ZoneInfo,
    ):
        """PURCHASED 상태의 티켓은 complete할 수 없어야 합니다."""
        # Given: PURCHASED 상태의 티켓 생성
        ticket_model = create_ticket_model(
            test_sync_session,
            user_id=sample_test_data["user_id"],
            city_id=sample_test_data["city_id"],
            airship_id=sample_test_data["airship_id"],
            status=TicketStatus.PURCHASED,
            timezone=timezone,
        )
        ticket_id_hex = ticket_model.ticket_id

        @contextmanager
        def mock_get_sync_db_session() -> Iterator[Session]:
            yield test_sync_session

        with patch(
            "bzero.worker.tasks.ticket.get_sync_db_session",
            mock_get_sync_db_session,
        ):
            # When: 태스크 직접 호출
            result = complete_ticket_task(ticket_id_hex)

        # Then: 실패 결과 확인
        assert result["ticket_id"] == ticket_id_hex
        assert "failed" in result["result"]
        assert "티켓 상태" in result["result"]  # 한글 에러 메시지 확인

        # DB 상태가 변경되지 않았는지 확인
        stmt = select(TicketModel).where(TicketModel.ticket_id == ticket_id_hex)
        db_result = test_sync_session.execute(stmt)
        unchanged_ticket = db_result.scalar_one()
        assert unchanged_ticket.status == TicketStatus.PURCHASED.value

    def test_complete_ticket_invalid_status_completed(
        self,
        test_sync_session: Session,
        sample_test_data: dict,
        timezone: ZoneInfo,
    ):
        """이미 COMPLETED 상태의 티켓은 이미 처리가 된 것이므로, 다시 처리하지 않는 것으로 멱등성을 보장합니다."""
        # Given: COMPLETED 상태의 티켓 생성
        ticket_model = create_ticket_model(
            test_sync_session,
            user_id=sample_test_data["user_id"],
            city_id=sample_test_data["city_id"],
            airship_id=sample_test_data["airship_id"],
            status=TicketStatus.COMPLETED,
            timezone=timezone,
        )
        ticket_id_hex = ticket_model.ticket_id

        @contextmanager
        def mock_get_sync_db_session() -> Iterator[Session]:
            yield test_sync_session

        with patch(
            "bzero.worker.tasks.ticket.get_sync_db_session",
            mock_get_sync_db_session,
        ):
            # When: 태스크 직접 호출
            result = complete_ticket_task(ticket_id_hex)

        # Then: 성공 결과 확인
        assert result["ticket_id"] == ticket_id_hex
        assert result["result"] == "success"

    def test_complete_ticket_invalid_status_cancelled(
        self,
        test_sync_session: Session,
        sample_test_data: dict,
        timezone: ZoneInfo,
    ):
        """CANCELLED 상태의 티켓은 이미 처리가 된 것이므로, 다시 처리하지 않는 것으로 멱등성을 보장합니다."""
        # Given: CANCELLED 상태의 티켓 생성
        ticket_model = create_ticket_model(
            test_sync_session,
            user_id=sample_test_data["user_id"],
            city_id=sample_test_data["city_id"],
            airship_id=sample_test_data["airship_id"],
            status=TicketStatus.CANCELLED,
            timezone=timezone,
        )
        ticket_id_hex = ticket_model.ticket_id

        @contextmanager
        def mock_get_sync_db_session() -> Iterator[Session]:
            yield test_sync_session

        with patch(
            "bzero.worker.tasks.ticket.get_sync_db_session",
            mock_get_sync_db_session,
        ):
            # When: 태스크 직접 호출
            result = complete_ticket_task(ticket_id_hex)

        # Then: 성공 결과 확인
        assert result["ticket_id"] == ticket_id_hex
        assert result["result"] == "success"
