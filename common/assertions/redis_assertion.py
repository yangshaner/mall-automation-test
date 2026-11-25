import allure
from typing import Any

from .base_assertion import BaseAssertion
from common.db.redis_util import redis_util


class RedisAssertion(BaseAssertion):

    def __init__(self):
        super().__init__()
        self._redis = redis_util

    @allure.step("Assert Redis key exists")
    def assert_key_exists(self, key: str,
                           message: str = "Redis key does not exist",
                          soft: bool = False):
        exists = self._redis.exists(key)
        return self._assert(exists, f"{message}: key={key}",
                            "exists", exists, soft)

    @allure.step("Assert Redis key does not exist")
    def assert_key_not_exists(self, key: str,
                              message: str = "Redis key exists",
                              soft: bool = False):
        exists = self._redis.exists(key)
        return self._assert(not exists, f"{message}: key={key}",
                            "does not exist", exists, soft)

    @allure.step("Assert Redis value is equal")
    def assert_value_equals(self, key: str, expected: Any,
                            message: str = "Redis value mismatch",
                            soft: bool = False):
        actual = self._redis.get(key)
        return self.assert_equals(actual, expected, message, soft)

    @allure.step("Assert Redis Hash value")
    def assert_hash_field(self, key: str, field: str, expected: Any,
                          message: str = "Hash field value mismatch",
                          soft: bool = False):
        actual = self._redis.hget(key, field)
        return self.assert_equals(actual, expected, message, soft)

    @allure.step("Assert Redis Hash exists")
    def assert_hash_exists(self, key: str, field: str,
                           message: str = "Hash field does not exist",
                           soft: bool = False):
        actual = self._redis.hget(key, field)
        return self.assert_is_not_none(actual, message, soft)

    @allure.step("Assert Redis Set contains member")
    def assert_set_contains(self, key: str, member: Any,
                            message: str = "Set does not contain the member",
                            soft: bool = False):
        members = self._redis.smembers(key)
        return self.assert_in(member, members, message, soft)

    @allure.step("Assert Redis List length")
    def assert_list_length(self, ket: str, expected_length: int,
                           message: str = "List length mismatch",
                           soft: bool = False):
        items = self._redis.lrange(ket, 0, -1)
        return self.assert_equals(len(items), expected_length, message, soft)
