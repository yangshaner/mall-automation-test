import json
import logging
import allure
from typing import Any, List, Union
from functools import wraps


logger = logging.getLogger(__name__)

class AssertionError(Exception):
    pass

def soft_assert(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, '_soft_assert'):
            self._soft_assert = []

        try:
            result = func(self, *args, **kwargs)
            return result
        except AssertionError as e:
            self._soft_assert.append(str(e))
            logger.warning(f"Soft assertion failed: {e}")
            return None
        except Exception as e:
            self._soft_assert.append(f"Assertion error: {e}")
            logger.error(f"Assertion error: {e}")
            return None

    return wrapper


class BaseAssertion:

    def __init__(self):
        self._soft_errers = []

    def _assert(self, condition: bool, message: str,
                expected: Any = None, actual: Any = None,
                soft: bool = False,
                expected_label: str = "Expected",
                actual_label: str = "Actual"):
        if not condition:
            full_message = message
            if expected is not None and actual is not None:
                full_message = f"{message}\n{expected_label}:{expected}\n{actual_label}:{actual}"
            elif expected is not None:
                full_message = f"{message}\n{expected_label}: {expected}"
            elif actual is not None:
                full_message = f"{message}\n{actual_label}:{actual}"

            if soft:
                self._soft_errers.append(full_message)
                logger.warning(f"Soft assertion failed: {full_message}")
            else:
                allure.attach(
                    full_message,
                    name="Assertion failure details",
                    attachment_type=allure.attachment_type.TEXT)
                raise AssertionError(full_message)
        return True

    def assert_equals(self, expected: Any, actual: Any,
        message: str = "Values are not equal", soft: bool = False):
        return self._assert(
            actual == expected,
            message,
            expected,
            actual,
            soft
        )

    def assert_not_equals(self, actual: Any, expected: Any,
                         message: str = "Values should not be equal", soft: bool = False):
        return self._assert(
            actual != expected,
            message,
            expected,
            actual,
            soft
        )

    def assert_true(self, condiction: bool, message: str = "Condition is not True",
                    soft: bool = False):
        return self._assert(condiction, message, True, condiction, soft)

    def assert_false(self, condiction: bool, message: str = "Condition is not False",
                     soft: bool = False):
        return self._assert(not condiction, message, False, condiction, soft)

    def assert_is_none(self, obj: Any, message: str = "Object is not None",
                       soft: bool = False):
        return self._assert(obj is None, message, None, obj, soft)

    def assert_is_not_none(self, obj: Any, message: str = "Object is None",
                           soft: bool = False):
        return self._assert(obj is not None, message, "not None", obj, soft)

    def assert_in(self, member: Any, container: Union[list, tuple, set, dict, str],
                  message: str = "Member is not in the container", soft: bool = False):
        return self._assert(member in container, message, container, member, soft)

    def assert_not_in(self, member: Any, container: Union[list, tuple, set, dict, str],
                      message: str = "Member is in the container", soft: bool = False):
        return self._assert(member not in container, message, container, member, soft)

    def assert_greater(self, actual: Union[int, float], expected: Union[int, float],
                       message: str = "Actual value is not greater than expected", soft: bool = False):
        return self._assert(actual > expected, message, expected, actual, soft)

    def assert_greater_equal(self, actual: Union[int, float], expected: Union[int, float],
                             message: str = "Actual value is not greater than or equal to expected", soft: bool = False):
            return self._assert(actual >= expected, message, expected, actual, soft)

    def assert_less(self, actual: Union[int, float], expected: Union[int, float],
                    message: str = "Actual value is not less than expected", soft: bool = False):
        return self._assert(actual < expected, message, expected, actual, soft)

    def assert_less_equal(self, actual: Union[int, float], expected: Union[int, float],
                          message: str = "Actual value is not less than or equal to expected", soft: bool = False):
        return self._assert(actual <= expected, message, expected, actual, soft)

    def assert_between(self, value: Union[int, float], min_val: Union[int, float],
                       max_val: Union[int, float], message: str = "Value is out of range", soft: bool = False):
        return self._assert(min_val <= value <= max_val, message, f"Range: [{min_val},{max_val}]", value, soft)

    def assert_type(self, obj: Any, expected_type: type, message: str = "Type mismatch", soft: bool = False):
        return self._assert(isinstance(obj, expected_type), message,
                            expected_type.__name__, type(obj).__name__, soft,
                            expected_label="Expected type",
                            actual_label="Actual type"
                        )

    def assert_contains(self, container: Union[list, tuple, dict, str], item: Any,
                       message: str = "Container does not contain the target element", soft: bool = False):
        if isinstance(container, dict):
            contains = item in container or item in container.values()
        else:
            contains = item in container
        return self._assert(contains, message, container, item, soft,
                            expected_label="Container content",
                            actual_label="Target element")

    def assert_length(self, container: Union[list, tuple, dict, str], expected_length: int,
                      message: str = "Length mismatch", soft: bool = False):
        actual_length = len(container)
        return self._assert(actual_length == expected_length, message, expected_length, actual_length, soft)

    def assert_regex_match(self, text: str, pattern: str,
                           message: str = "Regular expression does not match", soft: bool = False ):
        import re
        return self._assert(re.search(pattern, text) is not None, message, pattern, text, soft,
                            expected_label="Regex pattern",
                            actual_label="Text content")

    def assert_json_equals(self, actual: Union[str, dict], expected: Union[str, dict],
                           message: str = "JSON values are not equal", soft: bool = False):
        if isinstance(actual, str):
            actual = json.loads(actual)
        if isinstance(expected, str):
            expected = json.loads(expected)
        return self.assert_equals(actual, expected, message, soft)

    def assert_json_contains(self, actual: Union[str, dict], expected: Union[str, dict],
                             message: str = "JSON does not contain the target content", soft: bool = False):
        if isinstance(actual, str):
            actual = json.loads(actual)
        if isinstance(expected, str):
            expected = json.loads(expected)

        def _deep_contains(a, b):
            if isinstance(b, dict):
                for k, v in b.items():
                    if k not in a:
                        return False
                    if not _deep_contains(a[k], v):
                        return False
                return True
            elif isinstance(b, list):
                for item in b:
                    if item not in a:
                        return False
                return True
            else:
                return b == a
        return self._assert(_deep_contains(actual, expected), message, expected, actual, soft,
                            expected_label="Expected content",
                            actual_label="Actual JSON")

    def assert_field_exist(self, obj: dict, required_fields: Union[List[str], str],
                            message: str = "Missing required field", soft: bool = False):
        if isinstance(required_fields, str):
            required_fields = [required_fields]

        missing_fields = [f for f in required_fields if f not in obj]
        if missing_fields:
            error_msg = f"{message}: missing fields {missing_fields}"
            error_msg += f"\nExisting fields: {list(obj.keys())}"

            if soft:
                self._soft_errers.append(error_msg)
                logger.warning(f"Soft assertion failed: {error_msg}")
                return False
            else:
                raise AssertionError(error_msg)
        return True

    def assert_field_type(self, obj: dict, field: str, expected_types: type,
                          message: str = "Field type mismatch", soft: bool = False):
        if field not in obj:
            error_msg = f"Field '{field}' does not exist"
            if soft:
                self._soft_errers.append(error_msg)
                return False
            else:
                raise AssertionError(error_msg)

        return self.assert_type(obj[field], expected_types, message, soft)

    def assert_field_equals(self, obj: dict, field: str, expected: Any,
                            message: str = "Field value mismatch", soft: bool = False):
        if field not in obj:
            error_msg = f"Field '{field}' does not exist"
            if soft:
                self._soft_errers.append(error_msg)
                return False
            else:
                raise AssertionError(error_msg)

        actual = obj[field]
        return self._assert(actual == expected,
                            f"{message} (field: {field})",
                            expected,
                            actual,
                            soft,
                            expected_label="Expected",
                            actual_label="Actual")


    def assert_filed_not_equals(self, obj: dict, field: str, expected: Any,
                                message: str = "Field values should not be equal", soft: bool = False):
        if field not in obj:
            error_msg = f"Field '{field}' does not exist"
            if soft:
                self._soft_errers.append(error_msg)
                return False
            else:
                raise AssertionError(error_msg)

        actual = obj[field]
        return self._assert(
            actual != expected,
        f"{message} (field:f{field})",
            expected,
            actual,
            soft,
            expected_label="Expected value not equal to",
            actual_label="Actual"
        )

    def assert_filed_greater(self, obj: dict, field: str, expected: Union[int, float],
                                message: str = "Field value is not greater than expected", soft: bool = False):
        if field not in obj:
            error_msg = f"Field '{field}' does not exist"
            if soft:
                self._soft_errers.append(error_msg)
                return False
            else:
                raise AssertionError(error_msg)

        actual = obj[field]
        return self._assert(
            actual > expected,
           f"{message} (field:'{field}')",
            expected,
            actual,
            soft,
            expected_label="Expected value greater than",
            actual_label="Actual"
        )


    def assert_field_less(self, obj: dict, field: str, expected: Union[int, float],
                          message: str = "Field value is not less than expected", soft: bool = False):
        if field not in obj:
            error_msg = f"Field '{field}' does not exist"
            if soft:
                self._soft_errers.append(error_msg)
                return False
            else:
                raise AssertionError(error_msg)

        actual = obj[field]
        return self._assert(
            actual < expected,
            f"{message} (field: {field})",
            expected,
            actual,
            soft,
            expected_label="Expected value less than",
            actual_label="Actual"
        )

    def assert_response_status(self, response, expected_status: int = 200,
                               message: str = "HTTP status code mismatch", soft: bool = False):
        return self._assert(
            response.status_code == expected_status,
            message,
            expected_status,
            response.status_code,
            soft,
            expected_label="Expected HTTP status code",
            actual_label="Actual HTTP status code"
        )

    def assert_response_code(self, response, expected_code: int = 200,
                             message: str = "Business status code mismatch", soft: bool = False):
        try:
            data = response.json()
            actual_code = data.get('code')
        except:
            actual_code = None

        return self._assert(
            actual_code == expected_code,
            message,
            expected_code,
            actual_code,
            soft,
            expected_label="Expected business status code",
            actual_label="Actual business status code"
        )

    def assert_response_massage(self, response, expected_message: str,
                                message: str = "Response message mismatch", soft: bool = False):
        try:
            data = response.json()
            actual_message = data.get('message')
        except:
            actual_message = None

        return self._assert(
            actual_message == expected_message,
            message,
            expected_message,
            actual_message,
            soft,
            expected_label="Expected response message",
            actual_label="Actual response message"
        )

    def assert_response_has_data(self, response, message: str = "Response is missing the data field", soft: bool = False):

        try:
            data = response.json()
            has_data = 'data' in data and data['data'] is not None
            actual_data = data.get('data')
        except:
            has_data = False
            actual_data = None

        return self._assert(
            has_data,
            message,
            "data exists and is not empty",
            actual_data,
            soft,
            expected_label="Expected condition",
            actual_label="Actual data value"
        )


    def assert_response_data_not_empty(self, response,
                                       message: str = "Response data is empty", soft: bool = False):
        try:
            data = response.json().get('data')
            is_not_empty = bool(data)
        except:
            is_not_empty = False
            data = None

        return self._assert(
            is_not_empty,
            message,
            "non-empty data",
            data,
            soft,
            expected_label="Expected condition",
            actual_label="Actual data value"
        )

    def get_soft_errors(self) -> List[str]:
        return self._soft_errers

    def has_soft_errors(self) -> bool:
        return len(self._soft_errers) > 0

    def clear_soft_errors(self):
        self._soft_errers = []

    def flush_soft_assertions(self):
        if self._soft_errers:
            errors = "\n".join(self._soft_errers)
            self._soft_errers = []
            raise AssertionError(f"Soft assertions failed:\n{errors}")
