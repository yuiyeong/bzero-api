"""채팅 REST API.

대화 카드 관련 REST API 엔드포인트를 제공합니다.
실시간 채팅은 Socket.IO를 사용합니다 (/ws).
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from bzero.application.use_cases.chat_messages import GetRandomCardUseCase
from bzero.core.database import get_async_db_session
from bzero.domain.services import ConversationCardService
from bzero.infrastructure.repositories.conversation_card import SqlAlchemyConversationCardRepository


router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/cities/{city_id}/conversation-cards/random")
async def get_random_conversation_card(
    city_id: str,
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
):
    """도시별 랜덤 대화 카드 조회 (REST API).

    Args:
        city_id: 도시 ID (hex 문자열)
        session: 데이터베이스 세션

    Returns:
        랜덤으로 선택된 대화 카드
    """
    conversation_card_service = ConversationCardService(
        conversation_card_repository=SqlAlchemyConversationCardRepository(session),
    )
    use_case = GetRandomCardUseCase(conversation_card_service)
    return await use_case.execute(city_id)
