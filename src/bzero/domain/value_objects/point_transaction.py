from enum import Enum


class TransactionType(str, Enum):
    EARN = "earn"
    SPEND = "spend"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class TransactionReason(str, Enum):
    SIGNED_UP = "signed_up"
    DIARY = "diary"
    QUESTIONNAIRE = "questionnaire"
    TICKET = "ticket"
    EXTENSION = "extension"
    REFUND = "refund"
    ETC = "etc"


class TransactionReference(str, Enum):
    USERS = "users"
    DIARIES = "diaries"
    TICKETS = "tickets"
    QUESTIONNAIRES = "questionnaires"
