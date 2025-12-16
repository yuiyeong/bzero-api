from enum import Enum


class ErrorCode(str, Enum):
    INTERNAL_ERROR = "예상하지 못한 에러가 발생했습니다."

    INVALID_PARAMETER = "파라미터를 확인해주세요."
    INVALID_ID = "ID 형식이 잘못되었습니다."
    INVALID_AMOUNT = "금액이 잘못되었습니다."
    INVALID_EMAIL = "이메일 형식이 잘못되었습니다."
    INVALID_NICKNAME = "닉네임 형식이 잘못되었습니다."
    INVALID_PROFILE = "프로필 형식이 잘못되었습니다."
    INVALID_POINT_TRANSACTION_STATUS = "트랜잭션 상태가 잘못되었습니다."
    INVALID_TICKET_STATUS = "티켓 상태가 잘못되었습니다."
    INSUFFICIENT_BALANCE = "잔액이 부족합니다."
    INVALID_CITY_STATUS = "도시 상태가 잘못되었습니다."
    INVALID_AIRSHIP_STATUS = "비행선 상태가 잘못되었습니다."
    ALREADY_COMPLETED_TICKET = "이미 완료된 티켓입니다."
    INVALID_ROOM_STATUS = "방의 상태가 잘못되었습니다."
    ROOM_CAPACITY_LOCK_CONFLICT = "방 수용 인원 업데이트 중 잠금 충돌이 발생했습니다."

    UNAUTHORIZED = "인증되지 않은 요청입니다."
    FORBIDDEN_TICKET = "티켓을 가져올 수 없는 사용자입니다."
    FORBIDDEN_ROOM_FOR_USER = "사용자가 접근할 수 없는 방입니다."

    CITY_NOT_FOUND = "찾을 수 없는 도시입니다."
    NOT_FOUND_USER = "찾을 수 없는 사용자입니다."
    NOT_FOUND_AIRSHIP = "찾을 수 없는 비행선입니다."
    NOT_FOUND_TICKET = "찾을 수 없는 티켓입니다."
    NOT_FOUND_GUEST_HOUSE = "게스트 하우스를 찾을 수 없습니다."
    NOT_FOUND_ROOM = "방을 찾을 수 없습니다."
    NOT_FOUND_ROOM_STAY = "체류 정보가 없습니다."

    DUPLICATED_REWARD = "이미 지급된 보상입니다."
    DUPLICATED_USER = "이미 존재하는 사용자입니다."

    PROFILE_INCOMPLETE = "프로필이 완료되지 않았습니다."


class BeZeroError(Exception):
    def __init__(self, code: ErrorCode):
        super().__init__(code.name)
        self.code = code


class AuthError(BeZeroError):
    """인증 관련 에러의 기본 클래스."""


class AccessDeniedError(AuthError):
    """인가 관련 에러의 기본 클래스"""


class BadRequestError(BeZeroError):
    """요청 값이 잘못되었을 때 발생하는 에러."""


class NotFoundError(BeZeroError):
    """리소스를 찾지 못했을 때 발생하는 에러."""


class DuplicatedError(BeZeroError):
    """리소스를 중복되었을 때 발생하는 에러."""


class ForbiddenTicketError(AccessDeniedError):
    def __init__(self):
        super().__init__(ErrorCode.FORBIDDEN_TICKET)


class ForbiddenRoomForUserError(AccessDeniedError):
    def __init__(self):
        super().__init__(ErrorCode.FORBIDDEN_ROOM_FOR_USER)


class InvalidIdError(BadRequestError):
    def __init__(self):
        super().__init__(ErrorCode.INVALID_ID)


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


class InvalidTicketStatusError(BadRequestError):
    def __init__(self):
        super().__init__(ErrorCode.INVALID_TICKET_STATUS)


class InsufficientBalanceError(BadRequestError):
    def __init__(self):
        super().__init__(ErrorCode.INSUFFICIENT_BALANCE)


class InvalidCityStatusError(BadRequestError):
    def __init__(self):
        super().__init__(ErrorCode.INVALID_CITY_STATUS)


class InvalidAirshipStatusError(BadRequestError):
    def __init__(self):
        super().__init__(ErrorCode.INVALID_AIRSHIP_STATUS)


class AlreadyCompletedTicketError(BadRequestError):
    def __init__(self):
        super().__init__(ErrorCode.ALREADY_COMPLETED_TICKET)


class InvalidRoomStatusError(BadRequestError):
    def __init__(self):
        super().__init__(ErrorCode.INVALID_ROOM_STATUS)


class RoomCapacityLockError(BadRequestError):
    def __init__(self):
        super().__init__(ErrorCode.ROOM_CAPACITY_LOCK_CONFLICT)


class CityNotFoundError(NotFoundError):
    def __init__(self):
        super().__init__(ErrorCode.CITY_NOT_FOUND)


class NotFoundUserError(NotFoundError):
    def __init__(self):
        super().__init__(ErrorCode.NOT_FOUND_USER)


class NotFoundAirshipError(NotFoundError):
    def __init__(self):
        super().__init__(ErrorCode.NOT_FOUND_AIRSHIP)


class NotFoundTicketError(NotFoundError):
    def __init__(self):
        super().__init__(ErrorCode.NOT_FOUND_TICKET)


class NotFoundGuestHouseError(NotFoundError):
    def __init__(self):
        super().__init__(ErrorCode.NOT_FOUND_GUEST_HOUSE)


class NotFoundRoomError(NotFoundError):
    def __init__(self):
        super().__init__(ErrorCode.NOT_FOUND_ROOM)


class NotFoundRoomStayError(NotFoundError):
    def __init__(self):
        super().__init__(ErrorCode.NOT_FOUND_ROOM_STAY)


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
