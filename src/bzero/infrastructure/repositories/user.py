from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bzero.domain.entities.user import User
from bzero.domain.repositories.user import UserRepository
from bzero.domain.value_objects import Balance, Email, Id, Nickname, Profile
from bzero.infrastructure.db.user_model import UserModel


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, user: User) -> User:
        model = self._to_model(user)

        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)

        return self._to_entity(model)

    async def find_by_user_id(self, user_id: Id) -> User | None:
        stmt = select(UserModel).where(
            UserModel.user_id == user_id.value,
            UserModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_email(self, email: Email) -> User | None:
        stmt = select(UserModel).where(
            UserModel.email == email.value,
            UserModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_nickname(self, nickname: Nickname) -> User | None:
        stmt = select(UserModel).where(
            UserModel.nickname == nickname.value,
            UserModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    @staticmethod
    def _to_model(user: User) -> UserModel:
        return UserModel(
            user_id=user.user_id.value,
            email=user.email.value,
            password_hash=user.password_hash,
            nickname=user.nickname.value,
            profile_emoji=user.profile.value,
            current_points=user.current_points.value,
        )

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        return User(
            user_id=Id(model.user_id),
            email=Email(model.email),
            password_hash=model.password_hash,
            nickname=Nickname(model.nickname),
            profile=Profile(model.profile_emoji),
            current_points=Balance(model.current_points),
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )
