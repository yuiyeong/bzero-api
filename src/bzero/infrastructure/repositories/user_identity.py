from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bzero.domain.entities.user_identity import UserIdentity
from bzero.domain.repositories.user_identity import UserIdentityRepository
from bzero.domain.value_objects import AuthProvider, Id
from bzero.infrastructure.db.user_identity_model import UserIdentityModel


class SqlAlchemyUserIdentityRepository(UserIdentityRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, identity: UserIdentity) -> UserIdentity:
        model = self._to_model(identity)

        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)

        return self._to_entity(model)

    async def find_by_provider_user_id(self, provider: AuthProvider, provider_user_id: str) -> UserIdentity | None:
        stmt = select(UserIdentityModel).where(
            UserIdentityModel.provider == provider.value,
            UserIdentityModel.provider_user_id == provider_user_id,
            UserIdentityModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    @staticmethod
    def _to_model(identity: UserIdentity) -> UserIdentityModel:
        return UserIdentityModel(
            identity_id=identity.identity_id.value,
            user_id=identity.user_id.value,
            provider=identity.provider.value,
            provider_user_id=identity.provider_user_id,
        )

    @staticmethod
    def _to_entity(model: UserIdentityModel) -> UserIdentity:
        return UserIdentity(
            identity_id=Id(model.identity_id),
            user_id=Id(model.user_id),
            provider=AuthProvider(model.provider),
            provider_user_id=model.provider_user_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )
