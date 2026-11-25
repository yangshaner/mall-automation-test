import allure
from typing import Optional, List

from .base_assertion import BaseAssertion

class ApiAssertion(BaseAssertion):

    @allure.step("Assert API request succeeded")
    def assert_success(self, response, message: str = "API request failed",
                       check_response_code: bool = True, check_data: bool = True,
                       soft: bool = False):

        self.assert_response_status(response, 200, f"{message}: wrong HTTP status code", soft)

        if check_response_code:
            self.assert_response_code(response, 200,
                                      f"{message}: wrong business status code", soft)

        if check_data:
            self.assert_response_has_data(response, f"{message}: missing data field", soft)
            _data = response.json().get("data")
            if _data is not None and not isinstance(_data, (dict, list, int, str)):
                self._assert(
                    False,
                    f"{message}: unexpected data type, expected dict/list/int/str, "
                    f"got {type(_data).__name__}: {str(_data)[:80]}",
                    soft=soft
                )

        if not soft and self.has_soft_errors():
            self.flush_soft_assertions()

        return response.json()

    @allure.step("Assert API request failed")
    def assert_fail(self, response,
                    expected_code: Optional[int] = None,
                    expected_message: Optional[str] = None,
                    message: str = "API request failed",
                    soft: bool = False):
        if response.status_code >= 200:
            self.assert_response_status(response, response.status_code,
                                        f"{message}: HTTP status code", soft)
        else:
            data = response.json()
            if expected_code is not None:
                self.assert_not_equals(data.get("code"), 200,
                                       f"{message}: business status code should not be 200", soft)
            if expected_message is not None:
                self.assert_equals(data.get("code"), expected_code,
                                   f"{message}: business status code mismatch", soft)
            if expected_message:
                self.assert_response_massage(response, expected_message,
                                             f"{message}: response message mismatch", soft)

        if not soft and self.has_soft_errors():
            self.flush_soft_assertions()

        return response.json()

    @allure.step("Assert paged response")
    def assert_page_response(self, response,
                             expected_total:Optional[int] = None,
                             expected_page_size:Optional[int] = None,
                             min_items: int = 0,
                             allow_empty_list: bool = True,
                             message: str = "Invalid paged response",
                             soft: bool = False):
        data = self.assert_success(response, message, soft=soft)
        page_data = data.get('data', {})

        self.assert_field_exist(page_data, ['pageNum', 'pageSize', 'totalPage', 'total'],
                                f"{message}: missing pagination fields", soft)

        list_data = page_data.get('list')
        if list_data is None:
            total = data.get('total', 0)
            if total == 0 and allow_empty_list:
                list_data = []
            else:
                self.assert_field_exist(page_data, ['list'], f"{message}: missing list field", soft)
                list_data = []

        self.assert_type(list_data, list,
                         f"{message}: list should be an array", soft)

        if min_items > 0:
            self.assert_greater_equal(len(list_data), min_items,
                                      f"{message}: list length is less than {min_items}", soft)

        if expected_total is not None:
            self.assert_equals(page_data.get('total'), expected_total,
                               f"{message}: total mismatch", soft)

        if expected_page_size is not None:
            self.assert_equals(page_data.get('pageSize'), expected_page_size,
                               f"{message}: page size mismatch", soft)

        if not soft and self.has_soft_errors():
            self.flush_soft_assertions()

        return page_data

    def assert_list_response(self, response,
                             expected_count:Optional[int] = None,
                             min_count: int = 0,
                             message: str = "Invalid list response",
                             soft: bool = False):
        data = self.assert_success(response, message, soft=soft)

        list_data = data.get('data', [])
        self.assert_type(list_data, list, f"{message}: data should be an array", soft)

        if expected_count is not None:
            self.assert_equals(len(list_data), expected_count,
                               f"{message}: list count mismatch", soft)
        elif min_count > 0:
            self.assert_greater_equal(len(list_data), min_count,
                                      f"{message}: list length is less than {min_count}", soft)

        if not soft and self.has_soft_errors():
            self.flush_soft_assertions()

        return list_data

    @allure.step("Assert single object response")
    def assert_object_response(self, response,
                               required_fields: Optional[List[str]] = None,
                               message: str = "Invalid object response",
                               soft: bool = False):
        data = self.assert_success(response, message, soft=soft)

        obj_data = data.get('data', {})
        self.assert_true(bool(obj_data), f"{message}: data is empty", soft)

        if required_fields:
            self.assert_field_exist(obj_data, required_fields, f"{message}: missing required fields", soft)

        if not soft and self.has_soft_errors():
            self.flush_soft_assertions()

        return obj_data

    @allure.step("Assert creation succeeded")
    def assert_create_success(self, response,
                              expected_id_field: str = "id",
                              message: str = "Creation failed",
                              soft: bool = False):
        data = self.assert_success(response, message, soft=soft)

        obj_data = data.get('data', {})
        self.assert_field_exist(obj_data, [expected_id_field],
                                 f"{message}: missing ID field", soft)
        self.assert_is_not_none(obj_data.get(expected_id_field),
                                f"{message}: ID is empty", soft)

        if not soft and self.has_soft_errors():
            self.flush_soft_assertions()

        return obj_data.get(expected_id_field)

    @allure.step("Assert deletion succeeded")
    def assert_delete_success(self, response,
                              message: str = "Deletion failed",
                              soft: bool = False):
        return self.assert_success(response, message, False, soft)

    @allure.step("Assert update succeeded")
    def assert_update_success(self, response,
                              message: str = "Update failed",
                              soft: bool = False):
        return self.assert_success(response, message, False, soft)
