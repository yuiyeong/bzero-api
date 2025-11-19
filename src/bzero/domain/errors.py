from enum import Enum


class ErrorCode(str, Enum):
    INTERNAL_ERROR = "예상하지 못한 에러가 발생했습니다."

    INVALID_AMOUNT = "금액이 잘못되었습니다."
    INVALID_EMAIL = "이메일 형식이 잘못되었습니다."
    INVALID_NICKNAME = "닉네임 형식이 잘못되었습니다."
    INVALID_PROFILE = "프로필 형식이 잘못되었습니다."


class BeZeroError(Exception):
    def __init__(self, code: ErrorCode):
        super().__init__(code.name)
        self.code = code


class AuthError(BeZeroError):
    """인증/인가 관련 에러의 기본 클래스."""


class BadRequestError(BeZeroError):
    """요청 값이 잘못되었을 때 발생하는 에러."""


class NotFoundError(BeZeroError):
    """리소스를 찾지 못했을 때 발생하는 에러."""


class DuplicatedError(BeZeroError):
    """리소스를 중복되었을 때 발생하는 에러."""


class InvalidAmountError(BadRequestError):
    def __init__(self):
        super().__init__(ErrorCode.INVALID_AMOUNT)


class InvalidEmailError(BadRequestError):
    def __init__(self):
        super().__init__(ErrorCode.INVALID_EMAIL)


class InvalidNicknameError(BadRequestError):
    def __init__(self):
        super().__init__(ErrorCode.INVALID_NICKNAME)


class InvalidProfileError(BadRequestError):
    def __init__(self):
        super().__init__(ErrorCode.INVALID_PROFILE)
