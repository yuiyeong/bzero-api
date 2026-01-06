from bzero.domain.value_objects.reward import RewardType


class TestRewardType:
    """RewardType 값 객체 단위 테스트"""

    def test_reward_type_daily_login_value(self):
        """DAILY_LOGIN 타입의 값은 'daily_login'이다"""
        # Given/When/Then
        assert RewardType.DAILY_LOGIN.value == "daily_login"

    def test_reward_type_is_string_enum(self):
        """RewardType은 문자열 Enum이다"""
        # Given/When/Then
        assert isinstance(RewardType.DAILY_LOGIN, str)
        assert RewardType.DAILY_LOGIN == "daily_login"

    def test_reward_type_from_string(self):
        """문자열로부터 RewardType을 생성할 수 있다"""
        # Given
        value = "daily_login"

        # When
        reward_type = RewardType(value)

        # Then
        assert reward_type == RewardType.DAILY_LOGIN

    def test_reward_type_name(self):
        """RewardType의 name은 대문자 언더스코어 형식이다"""
        # Given/When/Then
        assert RewardType.DAILY_LOGIN.name == "DAILY_LOGIN"
