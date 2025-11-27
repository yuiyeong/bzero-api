from enum import Enum


class ErrorCode(str, Enum):
    INTERNAL_ERROR = "예상하지 못한 에러가 발생했습니다."

    INVALID_PARAMETER = "파라미터를 확인해주세요."
    INVALID_AMOUNT = "금액이 잘못되었습니다."
    INVALID_EMAIL = "이메일 형식이 잘못되었습니다."
    INVALID_NICKNAME = "닉네임 형식이 잘못되었습니다."
    INVALID_PROFILE = "프로필 형식이 잘못되었습니다."
    INVALID_POINT_TRANSACTION_STATUS = "트랜잭션 상태가 잘못되었습니다."

    UNAUTHORIZED = "인증되지 않은 요청입니다."

    CITY_NOT_FOUND = "찾을 수 없는 도시입니다."
    NOT_FOUND_USER = "찾을 수 없는 사용자입니다."

    DUPLICATED_REWARD = "이미 지급된 보상입니다."
    DUPLICATED_USER = "이미 존재하는 사용자입니다."

    PROFILE_INCOMPLETE = "프로필이 완료되지 않았습니다."


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


class InvalidPointTransactionStatusError(BadRequestError):
    def __init__(self):
        super().__init__(ErrorCode.INVALID_POINT_TRANSACTION_STATUS)


class CityNotFoundError(NotFoundError):
    def __init__(self):
        super().__init__(ErrorCode.CITY_NOT_FOUND)


class NotFoundUserError(NotFoundError):
    def __init__(self):
        super().__init__(ErrorCode.NOT_FOUND_USER)


class DuplicatedRewardError(DuplicatedError):
    def __init__(self):
        super().__init__(ErrorCode.DUPLICATED_REWARD)


class UnauthorizedError(AuthError):
    def __init__(self):
        super().__init__(ErrorCode.UNAUTHORIZED)


class DuplicatedUserError(DuplicatedError):
    def __init__(self):
        super().__init__(ErrorCode.DUPLICATED_USER)


class ProfileIncompleteError(BadRequestError):
    def __init__(self):
        super().__init__(ErrorCode.PROFILE_INCOMPLETE)
