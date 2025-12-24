"""채팅 메시지 도메인 서비스 (동기).

Celery 백그라운드 태스크에서 만료 메시지 삭제 등의 배치 작업을 처리합니다.
"""

from datetime import datetime

from bzero.domain.repositories.chat_message import ChatMessageSyncRepository


class ChatMessageSyncService:
    """채팅 메시지 도메인 서비스 (동기).

    Celery 백그라운드 태스크에서 만료 메시지 삭제 등의 배치 작업을 처리합니다.

    Attributes:
        _chat_message_repository: 채팅 메시지 저장소 (동기)
    """

    def __init__(self, chat_message_sync_repository: ChatMessageSyncRepository):
        """ChatMessageSyncService를 초기화합니다.

        Args:
            chat_message_sync_repository: 채팅 메시지 동기 저장소 인터페이스
        """
        self._chat_message_repository = chat_message_sync_repository

    def delete_expired_messages(self, before_datetime: datetime) -> int:
        """만료 시간이 지난 메시지를 soft delete 처리합니다.

        매일 자정에 Celery Beat가 실행하는 배치 작업입니다.
        expires_at < before_datetime 조건을 만족하는 메시지를 삭제합니다.

        Args:
            before_datetime: 이 시간 이전에 만료된 메시지를 삭제 (예: 현재 시간)

        Returns:
            삭제된 메시지 개수
        """
        # 1. 만료된 메시지 조회
        expired_messages = self._chat_message_repository.find_expired_messages(before_datetime)

        if not expired_messages:
            return 0

        # 2. 메시지 ID 목록 추출
        message_ids = [msg.message_id for msg in expired_messages]

        # 3. Soft delete 처리
        deleted_count = self._chat_message_repository.delete_messages(message_ids)

        return deleted_count
