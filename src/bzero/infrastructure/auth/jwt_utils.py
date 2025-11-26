import jwt

from bzero.core.loggers import app_logger
from bzero.domain.errors import UnauthorizedError


logger = app_logger()


def verify_supabase_jwt(token: str, secret: str, algorithm: str = "HS256") -> dict:
    """
    Supabase JWT를 검증하고 payload를 반환합니다.

    Args:
        token: JWT 토큰
        secret: JWT secret key
        algorithm: JWT 알고리즘 (기본값: HS256)

    Returns:
        JWT payload (dict)

    Raises:
        UnauthorizedError: JWT 검증 실패 시
    """
    try:
        return jwt.decode(
            token,
            secret,
            algorithms=[algorithm],
            audience="authenticated",  # Supabase 로그인 사용자의 audience
        )
    except jwt.ExpiredSignatureError as e:
        logger.warning(f"Error from ExpiredSignatureError: {e}")
        raise UnauthorizedError from None
    except jwt.InvalidTokenError as err:
        logger.warning(f"Error from InvalidTokenError: {err}")
        raise UnauthorizedError from None


def extract_user_id_from_jwt(token: str, secret: str, algorithm: str = "HS256") -> str:
    """
    JWT에서 Supabase user_id (sub claim)를 추출합니다.

    Args:
        token: JWT 토큰
        secret: JWT secret key
        algorithm: JWT 알고리즘 (기본값: HS256)

    Returns:
        Supabase user_id (sub claim)

    Raises:
        UnauthorizedError: JWT 검증 실패 또는 sub claim이 없을 때
    """
    payload = verify_supabase_jwt(token, secret, algorithm)

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError

    return user_id
