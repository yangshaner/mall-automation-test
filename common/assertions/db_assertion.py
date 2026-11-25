import  allure
from typing import Optional, Any, List, Tuple

from .base_assertion import BaseAssertion
from common.db.mysql_util import mysql


class DBAssertion(BaseAssertion):

    def __init__(self):
        super().__init__()
        self._mysql = mysql

    @allure.step("Assert database record exists")
    def assert_exists(self, table: str, condition: str,
                     params: Optional[Tuple] = None,
                     message: str = "Data does not exist",
                     soft: bool = False):
        sql = f"SELECT COUNT(*) as cnt FROM {table} WHERE {condition}"
        result = self._mysql.query(sql, params)
        count = result[0].get("cnt", 0) if result else 0
        return self._assert(
            count > 0,
            f"{message}: {table} WHERE {condition}",
            "exists",
            count,
            soft
        )

    @allure.step("Assert database record does not exist")
    def assert_not_exists(self, table: str, condition: str,
                         params: Optional[Tuple] = None,
                         message: str = "Data exists",
                         soft: bool = False):
        sql = f"SELECT COUNT(*) as cnt FROM {table} WHERE {condition}"
        result = self._mysql.query(sql, params)
        count = result[0].get("cnt", 0) if result else 0
        return self._assert(
            count == 0,
            f"{message}: {table} WHERE {condition}",
            "does not exist",
            count,
            soft
        )

    @allure.step("Assert field values are equal")
    def assert_field_value(self, table: str, field: str,
                           expected: Any, condition: str,
                           params: Optional[Tuple] = None,
                           message: str = f"Field value mismatch",
                           soft: bool = False):
        sql = f"SELECT {field} FROM {table} WHERE {condition}"
        result = self._mysql.query(sql, params)
        if not result:
            return self._assert(False, f"Data not found: {table} WHERE {condition}", soft=soft)

        actual = result[0].get(field)
        print(f"actual:{actual}, actual_type:{type(actual)}, expected:{expected}, expected_type:{type(expected)}")
        message = f"{field}"+message
        return self.assert_equals(actual, expected, message, soft)

    @allure.step("Assert field value is in list")
    def assert_field_in_list(self, table: str, field: str,
                             expected_list: List[Any], condition: str,
                             params: Optional[Tuple] = None,
                             message: str = "Field value is not in the list",
                             soft: bool = False):
        sql = f"SELECT {field} FROM {table} WHERE {condition}"
        result = self._mysql.query(sql, params)
        if not result:
            return self._assert(False, f"Data not found: {table} WHERE {condition}", soft=soft)

        actual = result[0].get(field)
        return self.assert_in(actual, expected_list, message, soft)

    @allure.step("Assert record count")
    def assert_count(self, table: str, expected_count: int,
                     condition: Optional[str] = None,
                     params: Optional[Tuple] = None,
                     message: str = "Record count mismatch",
                     soft: bool = False):
        sql = f"SELECT COUNT(*) as cnt FROM {table}"
        if condition:
            sql += f" WHERE {condition}"
        result = self._mysql.query(sql, params)
        count = result[0].get("cnt", 0) if result else 0
        return self.assert_equals(count, expected_count, message, soft)

    @allure.step("Assert query result is not empty")
    def assert_query_result(self, sql: str,
                            params: Optional[Tuple] = None,
                            message: str = "Query result is empty",
                            soft: bool = False):
        result = self._mysql.query(sql, params)
        return self._assert(bool(result), message, "non-empty result", result, soft)

    @allure.step("Assert query result is empty")
    def assert_query_empty(self, sql: str,
                           params: Optional[Tuple] = None,
                           message: str = "Query result should be empty",
                           soft: bool = False):
        result = self._mysql.query(sql, params)
        return self._assert(not result, message, "empty result", result, soft)

    @allure.step("Assert field is not null")
    def assert_field_not_null(self, table: str, field: str,
                               condition: str, params: Optional[Tuple] = None,
                               message: str = "Field is empty",
                               soft: bool = False):
        sql = f"SELECT {field} FROM {table} WHERE {condition}"
        result = self._mysql.query(sql, params)
        if not result:
            return self._assert(False, f"Data not found: {table} WHERE {condition}", soft=soft)

        actual = result[0].get(field)
        return self.assert_is_not_none(actual, message, soft)

    @allure.step("Assert field is null")
    def assert_field_null(self, table: str, field: str,
                          condition: str, params: Optional[Tuple] = None,
                          message: str = "Field is empty", soft: bool = False):
        sql = f"SELECT {field} FROM {table} WHERE {condition}"
        result = self._mysql.query(sql, params)
        if not result:
            return self._assert(False, f"Data not found: {table} WHERE {condition}", soft=soft)

        actual = result[0].get(field)
        return self.assert_is_none(actual, message, soft)
