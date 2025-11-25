from abc import ABC, abstractmethod

from bzero.domain.entities.user_identity import UserIdentity
from bzero.domain.value_objects import AuthProvider


class UserIdentityRepository(ABC):
    @abstractmethod
    async def create(self, identity: UserIdentity) -> UserIdentity:
        """사용자 인증 정보를 생성하고 저장합니다."""

    @abstractmethod
    async def find_by_provider_user_id(self, provider: AuthProvider, provider_user_id: str) -> UserIdentity | None:
        """provider와 provider_user_id로 사용자 인증 정보를 조회합니다. 없으면 None을 반환합니다."""
