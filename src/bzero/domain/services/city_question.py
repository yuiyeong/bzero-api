from bzero.domain.errors import CityNotFoundError
from bzero.domain.repositories.city import CityRepository
from bzero.domain.value_objects import Id

# 세렌시아 (관계의 도시) 질문
SERENCIA_QUESTIONS = [
    "요즘 나에게 힘이 되어주는 사람은?",
    "최근에 누군가와 나눈 의미 있는 대화는?",
    "관계에서 내가 가장 중요하게 생각하는 것은?",
]

# 로렌시아 (회복의 도시) 질문
LORENCIA_QUESTIONS = [
    "요즘 나를 가장 지치게 하는 것은?",
    "나만의 휴식 방법이 있다면?",
    "회복이 필요할 때 가장 먼저 하고 싶은 일은?",
]

# 엠마시아 (희망의 도시) 질문
EMMASIA_QUESTIONS = [
    "최근에 나를 설레게 한 것은?",
    "내가 이루고 싶은 꿈이 있다면?",
    "미래의 나에게 하고 싶은 말은?",
]

# 다마린 (고요의 도시) 질문
DAMARIN_QUESTIONS = [
    "요즘 마음이 고요할 때는 언제인가?",
    "내가 가장 평온함을 느끼는 순간은?",
    "고요함 속에서 떠오르는 생각은?",
]

# 갈리시아 (성찰의 도시) 질문
GALICIA_QUESTIONS = [
    "최근에 내가 성장했다고 느낀 순간은?",
    "지금의 나를 만든 경험이 있다면?",
    "앞으로 더 발전하고 싶은 부분은?",
]

# 도시 이름 -> 질문 매핑
CITY_QUESTIONS_MAP = {
    "세렌시아": SERENCIA_QUESTIONS,
    "로렌시아": LORENCIA_QUESTIONS,
    "엠마시아": EMMASIA_QUESTIONS,
    "다마린": DAMARIN_QUESTIONS,
    "갈리시아": GALICIA_QUESTIONS,
}


class CityQuestionService:
    """도시별 질문 서비스

    도시별 질문 3개를 제공합니다.
    질문은 코드로 관리하며 DB에 저장하지 않습니다.
    """

    def __init__(self, city_repository: CityRepository):
        self._city_repository = city_repository

    async def get_questions_by_city(self, city_id: Id) -> list[str]:
        """도시 ID로 질문 3개 조회

        Args:
            city_id: 도시 ID

        Returns:
            질문 3개 리스트

        Raises:
            CityNotFoundError: 존재하지 않는 도시 ID인 경우
        """
        # 1. 도시 조회
        city = await self._city_repository.find_by_id(city_id)
        if not city:
            raise CityNotFoundError

        # 2. 도시 이름으로 질문 매핑
        questions = CITY_QUESTIONS_MAP.get(city.name)
        if not questions:
            raise CityNotFoundError

        return questions
