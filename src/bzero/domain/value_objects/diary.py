from enum import Enum


class DiaryMood(str, Enum):
    """일기 감정 상태."""

    HAPPY = "happy"
    PEACEFUL = "peaceful"
    GRATEFUL = "grateful"
    REFLECTIVE = "reflective"
    SAD = "sad"
    ANXIOUS = "anxious"
    HOPEFUL = "hopeful"
    TIRED = "tired"
