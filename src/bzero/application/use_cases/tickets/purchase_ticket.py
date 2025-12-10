"""비행선 티켓 구매 유스케이스.

사용자가 특정 도시로 가는 비행선 티켓을 구매하는 비즈니스 로직을 담당합니다.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.results import TicketResult
from bzero.domain.ports import TaskScheduler
from bzero.domain.services import AirshipService, CityService, PointTransactionService, TicketService, UserService
from bzero.domain.value_objects import AuthProvider, Id, TransactionReason, TransactionReference


class PurchaseTicketUseCase:
    """비행선 티켓 구매 유스케이스.

    사용자가 선택한 도시와 비행선으로 티켓을 구매합니다.
    구매 시 포인트가 차감되고, 도착 시간에 자동으로 티켓이 완료 처리되도록
    백그라운드 작업이 예약됩니다.

    비즈니스 규칙:
        - 비용 = 도시 기본 비용 * 비행선 비용 배율
        - 소요 시간 = 도시 기본 시간 * 비행선 시간 배율
        - 구매 즉시 BOARDING 상태로 전환 (즉시 탑승)
        - 도착 시간에 Celery 작업으로 COMPLETED 상태로 전환
    """

    def __init__(
        self,
        session: AsyncSession,
        user_service: UserService,
        city_service: CityService,
        airship_service: AirshipService,
        ticket_service: TicketService,
        point_transaction_service: PointTransactionService,
        task_scheduler: TaskScheduler,
    ):
        self._session = session
        self._user_service = user_service
        self._city_service = city_service
        self._airship_service = airship_service
        self._ticket_service = ticket_service
        self._point_transaction_service = point_transaction_service
        self._task_scheduler = task_scheduler

    async def execute(
        self,
        provider: str,
        provider_user_id: str,
        city_id: str,
        airship_id: str,
    ) -> TicketResult:
        """티켓 구매를 실행합니다.

        Args:
            provider: 인증 제공자 (예: "supabase")
            provider_user_id: 인증 제공자의 사용자 ID
            city_id: 목적지 도시 ID (hex 문자열)
            airship_id: 이용할 비행선 ID (hex 문자열)

        Returns:
            생성된 티켓 정보

        Raises:
            NotFoundUserError: 사용자를 찾을 수 없는 경우
            NotFoundCityError: 도시를 찾을 수 없거나 비활성화된 경우
            NotFoundAirshipError: 비행선을 찾을 수 없거나 비활성화된 경우
            InsufficientBalanceError: 포인트가 부족한 경우
        """
        # 1. 사용자 조회
        user = await self._user_service.find_user_by_provider_and_provider_user_id(
            provider=AuthProvider(provider),
            provider_user_id=provider_user_id,
        )

        # 2. 도시 및 비행선 조회 (활성화 상태 검증 포함)
        city = await self._city_service.get_active_city_by_id(Id.from_hex(city_id))
        airship = await self._airship_service.get_active_airship_by_id(Id.from_hex(airship_id))

        # 3. 티켓 생성 (포인트 잔액 검증 포함, 즉시 BOARDING 상태)
        ticket = await self._ticket_service.purchase_ticket(user, city, airship)

        # 4. 포인트 차감
        await self._point_transaction_service.spend_by(
            user=user,
            amount=ticket.cost_points,
            reason=TransactionReason.TICKET,
            reference_type=TransactionReference.TICKETS,
            reference_id=ticket.ticket_id,
        )

        # 5. 트랜잭션 커밋
        await self._session.commit()

        # 6. 도착 시간에 티켓 완료 처리 작업 예약 (Celery)
        self._task_scheduler.schedule_ticket_completion(
            ticket_id=ticket.ticket_id.to_hex(),
            eta=ticket.arrival_datetime,
        )

        return TicketResult.create_from(ticket)
