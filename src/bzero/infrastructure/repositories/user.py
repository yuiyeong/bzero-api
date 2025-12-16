from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bzero.domain.entities.user import User
from bzero.domain.errors import NotFoundUserError
from bzero.domain.repositories.user import UserRepository
from bzero.domain.value_objects import AuthProvider, Balance, Email, Id, Nickname, Profile
from bzero.infrastructure.db.user_identity_model import UserIdentityModel
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

    async def find_by_provider_and_provider_user_id(self, provider: AuthProvider, provider_user_id: str) -> User | None:
        stmt = (
            select(UserModel)
            .join(UserIdentityModel, UserModel.user_id == UserIdentityModel.user_id)
            .where(
                UserIdentityModel.provider == provider.value,
                UserIdentityModel.provider_user_id == provider_user_id,
                UserIdentityModel.deleted_at.is_(None),
                UserModel.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def update(self, user: User) -> User:
        stmt = (
            update(UserModel)
            .where(
                UserModel.user_id == user.user_id.value,
                UserModel.deleted_at.is_(None),
            )
            .values(
                nickname=user.nickname.value if user.nickname else None,
                profile_emoji=user.profile.value if user.profile else None,
                current_points=user.current_points.value,
            )
            .returning(UserModel)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            raise NotFoundUserError

        return self._to_entity(model)

    async def find_all_by_user_ids(self, user_ids: tuple[Id]) -> list[User]:
        stmt = select(UserModel).where(
            UserModel.user_id.in_([uid.value for uid in user_ids]),
            UserModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    @staticmethod
    def _to_model(entity: User) -> UserModel:
        return UserModel(
            user_id=entity.user_id.value,
            email=entity.email.value if entity.email else None,
            nickname=entity.nickname.value if entity.nickname else None,
            profile_emoji=entity.profile.value if entity.profile else None,
            current_points=entity.current_points.value,
            deleted_at=entity.deleted_at,
        )

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        return User(
            user_id=Id(model.user_id),
            email=Email(model.email) if model.email else None,
            nickname=Nickname(model.nickname) if model.nickname else None,
            profile=Profile(model.profile_emoji) if model.profile_emoji else None,
            current_points=Balance(model.current_points),
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )
