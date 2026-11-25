import allure
from contextlib import contextmanager
from typing import Any

from .api_assertion import ApiAssertion
from .db_assertion import DBAssertion
from .redis_assertion import RedisAssertion

class SoftAssertion():

    def __init__(self):
        self.errors = []
        self.api = ApiAssertion()
        self.db = DBAssertion()
        self.redis = RedisAssertion()

    @contextmanager
    def context(self):
        self.errors = []
        self.api.clear_soft_errors()
        self.db.clear_soft_errors()
        self.redis.clear_soft_errors()

        try:
            yield self
        finally:
            self.errors.extend(self.api.get_soft_errors())
            self.errors.extend(self.db.get_soft_errors())
            self.errors.extend(self.redis.get_soft_errors())

            if self.errors:
                error_msg = "\n".join(self.errors)
                allure.attach(error_msg, name="Soft assertion failures summary",
                              attachment_type=allure.attachment_type.TEXT)

    def flush(self):
        if self.errors:
            errors = "\n".join(self.errors)
            self.errors = []
            raise AssertionError(f"Soft assertions failed:\n{errors}")

    def assert_success(self, response, message: str = "API request failed"):
        return self.api.assert_success(response, message, soft=True)

    def assert_field_equals(self, response, field: str, expected: Any,
                            message: str = "Field value mismatch"):
        data = response.json().get('data', {})
        return self.api.assert_field_equals(data, field, expected, message, soft=True)

    def assert_db_exists(self, table: str, condition: str, params=None,
                         message: str = "Data does not exist"):
        return self.db.assert_exists(table, condition, params, message, soft=True)

    def assert_db_field(self, table: str, field: str, expected: Any,
                        condition: str, params=None, message: str = "Field value mismatch"):
        return self.db.assert_field_value(table, field, expected, condition, params, message, soft=True)

    def assert_redis_value(self, key: str, expected: Any,
                           message: str = "Redis value mismatch"):
        return self.redis.assert_value_equals(key, expected, message, soft=True)
