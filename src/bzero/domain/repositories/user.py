from abc import ABC, abstractmethod

from bzero.domain.entities.user import User
from bzero.domain.value_objects import AuthProvider, Email, Id, Nickname


class UserRepository(ABC):
    @abstractmethod
    async def create(self, user: User) -> User:
        """사용자를 생성하고 저장합니다."""

    @abstractmethod
    async def find_by_user_id(self, user_id: Id) -> User | None:
        """사용자 ID로 사용자를 조회합니다. 없으면 None을 반환합니다."""

    @abstractmethod
    async def find_by_email(self, email: Email) -> User | None:
        """이메일로 사용자를 조회합니다. 없으면 None을 반환합니다."""

    @abstractmethod
    async def find_by_nickname(self, nickname: Nickname) -> User | None:
        """닉네임으로 사용자를 조회합니다. 없으면 None을 반환합니다."""

    @abstractmethod
    async def find_by_provider_and_provider_user_id(self, provider: AuthProvider, provider_user_id: str) -> User | None:
        """AuthProvider 와 provider user id 로 사용자를 조회합니다. 없으면 None을 반환합니다."""

    @abstractmethod
    async def update(self, user: User) -> User:
        """사용자 정보 업데이트"""
