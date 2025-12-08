from dataclasses import dataclass

from bzero.domain.errors import InvalidQuestionnaireAnswerError


@dataclass(frozen=True)
class QuestionAnswer:
    """문답지 답변 값 객체 (최대 200자)"""

    MAX_LENGTH = 200

    value: str

    def __post_init__(self):
        if not self.value or len(self.value) > self.MAX_LENGTH:
            raise InvalidQuestionnaireAnswerError
