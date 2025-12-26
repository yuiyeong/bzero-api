
from uuid import UUID as StandardUUID

from uuid_utils import uuid7

from bzero.domain.value_objects import Id


def test_id_uuid_conversion():
    # Test default factory
    id_obj = Id()
    print(f"Type of value from default factory: {type(id_obj.value)}")
    assert type(id_obj.value) is StandardUUID
    assert isinstance(id_obj.value, StandardUUID)

    # Test with uuid7 input
    u7 = uuid7()
    id_obj2 = Id(u7)
    print(f"Type of value from uuid7 input: {type(id_obj2.value)}")
    assert type(id_obj2.value) is StandardUUID

    # Test with string input
    u_str = str(uuid7())
    id_obj3 = Id(u_str)
    print(f"Type of value from string input: {type(id_obj3.value)}")
    assert type(id_obj3.value) is StandardUUID

if __name__ == "__main__":
    try:
        test_id_uuid_conversion()
        print("All Id checks passed!")
    except AssertionError as e:
        print(f"Assertion failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
