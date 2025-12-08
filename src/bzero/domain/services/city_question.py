from bzero.domain.errors import CityNotFoundError
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


class CityQuestionService:
    """도시별 질문 서비스

    도시별 질문 3개를 제공합니다.
    질문은 코드로 관리하며 DB에 저장하지 않습니다.
    """

    def get_questions_by_city(self, city_id: Id) -> list[str]:
        """도시 ID로 질문 3개 조회

        Args:
            city_id: 도시 ID

        Returns:
            질문 3개 리스트

        Raises:
            CityNotFoundError: 존재하지 않는 도시 ID인 경우
        """
        # TODO: 도시 ID 값을 실제 데이터와 매칭하여 반환해야 함
        # 현재는 도시 이름으로 구분하거나, 별도 매핑 테이블이 필요할 수 있음
        # 여기서는 하드코딩된 ID를 사용하거나, 도시 리포지토리를 통해 이름을 가져올 수 있음

        # 임시로 도시 ID에 따른 질문 반환 로직 (실제로는 도시 name을 기준으로)
        # 이 부분은 시드 데이터의 도시 ID와 맞춰야 합니다
        city_id_value = city_id.value

        # 시드 데이터의 실제 도시 ID와 매핑 필요
        # 여기서는 city_id 문자열에 따라 분기 (추후 개선 필요)
        # 실제 구현에서는 CityRepository를 주입받아 city.name으로 판단할 수 있음
        raise CityNotFoundError
