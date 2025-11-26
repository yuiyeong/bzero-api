"""API dependencies."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from bzero.core.database import get_async_db_session
from bzero.core.settings import get_settings
from bzero.domain.errors import UnauthorizedError
from bzero.domain.services.city import CityService
from bzero.domain.services.point_transaction import PointTransactionService
from bzero.domain.services.user import UserService
from bzero.infrastructure.auth.jwt_utils import verify_supabase_jwt
from bzero.infrastructure.repositories.city import SqlAlchemyCityRepository
from bzero.infrastructure.repositories.point_transaction import SqlAlchemyPointTransactionRepository
from bzero.infrastructure.repositories.user import SqlAlchemyUserRepository
from bzero.infrastructure.repositories.user_identity import SqlAlchemyUserIdentityRepository
from bzero.presentation.schemas.common import JWTPayload


security = HTTPBearer()


def get_jwt_payload(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> JWTPayload:
    """Verify JWT token and return payload.

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        JWTPayload: Extracted user info from verified JWT

    Raises:
        UnauthorizedError: When JWT verification fails (handled by global error handler)
    """
    settings = get_settings()
    payload = verify_supabase_jwt(
        token=credentials.credentials,
        secret=settings.auth.supabase_jwt_secret.get_secret_value(),
        algorithm=settings.auth.jwt_algorithm,
    )

    # 페이로드 예시)
    # {
    #     "aal": "aal1",
    #     "amr": [{"method": "password", "timestamp": 1764048031}],
    #     "app_metadata": {"provider": "email", "providers": ["email"]},
    #     "aud": "authenticated",
    #     "email": "test@test.com",
    #     "exp": 1764051631,
    #     "iat": 1764048031,
    #     "is_anonymous": False,
    #     "iss": "https://spphmqtqpxauvvgntilq.supabase.co/auth/v1",
    #     "phone": "",
    #     "role": "authenticated",
    #     "session_id": "dd7abc49-ca39-4f35-bb3f-7518ef888a91",
    #     "sub": "7a7d9a10-42fe-4476-8054-47d7045f7905",
    #     "user_metadata": {
    #         "email": "test@test.com",
    #         "email_verified": True,
    #         "phone_verified": False,
    #         "sub": "7a7d9a10-42fe-4476-8054-47d7045f7905",
    #     },
    # }

    provider = payload.get("app_metadata", {}).get("provider")
    provider_user_id = payload.get("sub")
    email = payload.get("email")
    phone = payload.get("phone")
    email_verified = payload.get("user_metadata", {}).get("email_verified", False)
    phone_verified = payload.get("user_metadata", {}).get("phone_verified", False)

    if not provider_user_id or not email:
        raise UnauthorizedError

    return JWTPayload(
        provider=provider,
        provider_user_id=provider_user_id,
        email=email,
        phone=phone,
        email_verified=email_verified,
        phone_verified=phone_verified,
    )


def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> SqlAlchemyUserRepository:
    """Create UserRepository instance."""
    return SqlAlchemyUserRepository(session)


def get_user_service(
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> UserService:
    """Create UserService instance."""
    user_repository = get_user_repository(session)
    user_identity_repository = SqlAlchemyUserIdentityRepository(session)
    return UserService(user_repository, user_identity_repository)


def get_point_transaction_service(
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> PointTransactionService:
    """Create PointTransactionService instance."""
    user_repository = get_user_repository(session)
    point_transaction_repository = SqlAlchemyPointTransactionRepository(session)
    return PointTransactionService(user_repository, point_transaction_repository)


def get_city_service(
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> CityService:
    """Create CityService instance."""
    city_repository = SqlAlchemyCityRepository(session)
    return CityService(city_repository)


# Type aliases
DBSession = Annotated[AsyncSession, Depends(get_async_db_session)]
CurrentJWTPayload = Annotated[JWTPayload, Depends(get_jwt_payload)]
CurrentUserService = Annotated[UserService, Depends(get_user_service)]
CurrentPointTransactionService = Annotated[PointTransactionService, Depends(get_point_transaction_service)]
CurrentCityService = Annotated[CityService, Depends(get_city_service)]
