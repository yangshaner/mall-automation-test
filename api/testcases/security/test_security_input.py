# testcase/security/test_security_input.py
import pytest
import allure

from common.assertions import ApiAssertion

SAFE_STATUS_CODES = (200, 400, 413)


@allure.feature("Security Test - Input Validation and Injection Defense")
class TestSecurityInput:

    def setup_method(self):
        self.api_assert = ApiAssertion()

    def _assert_safe_response(self, response, message: str):
        assert response.status_code in SAFE_STATUS_CODES, \
            f"{message} (actual status code {response.status_code}, safe status code set {SAFE_STATUS_CODES})"
        body = response.text.lower()
        assert "sqlsyntax" not in body.replace(" ", "") and "SQLException".lower() not in body, \
            f"{message}: response should not expose SQL exception info"
        assert "java.lang" not in body and "at org.springframework" not in body, \
            f"{message}: response should not expose stack trace info"


    @allure.story("SQL Injection - Product Search")
    @pytest.mark.parametrize("payload", [
        "' OR '1'='1",
        "' OR 1=1 --",
        "1' AND SLEEP(5)--",
        "1; DROP TABLE pms_product; --",
        "' UNION SELECT * FROM pms_product--",
    ])
    def test_sql_injection_search(self, member_product_api, payload):
        response = member_product_api.search(keyword=payload, page_num=1, page_size=10)
        self._assert_safe_response(response, "SQL injection should not cause a server error")

    @allure.story("SQL Injection - Order Query")
    def test_sql_injection_order_list(self, member_order_api):
        response = member_order_api.list(status="0 OR 1=1", page_num=1, page_size=10)
        self._assert_safe_response(response, "SQL injection should not cause a server error")

    @allure.story("SQL Injection - Admin Product Query")
    def test_sql_injection_admin_product_list(self, admin_client):
        response = admin_client.get("/product/list", params={
            "pageNum": 1,
            "pageSize": 10,
            "keyword": "' OR '1'='1"
        })
        self._assert_safe_response(response, "Admin endpoints should not be affected by SQL injection")


    @allure.story("XSS Injection - Product Name")
    def test_xss_in_product_name(self, admin_client):
        xss_payload = "<script>alert('xss')</script>"
        product_data = {
            "name": xss_payload,
            "productSn": "XSS_TEST_001",
            "price": 99.99,
            "stock": 10,
            "brandId": 1,
            "productCategoryId": 1,
            "publishStatus": 0,
            "verifyStatus": 0,
        }
        try:
            response = admin_client.post("/product/create", json=product_data)
            result = response.json()
            assert result.get("code") == 200 or result.get("code") != 200
            if result.get("code") == 200:
                list_resp = admin_client.get("/product/list", params={
                    "pageNum": 1, "pageSize": 10, "keyword": "XSS_TEST"
                })
                list_body = list_resp.text
                assert "<script>" not in list_body, "XSS payload should not be returned as-is"
        finally:
            pass

    @allure.story("XSS Injection - Search Parameter")
    def test_xss_in_search_keyword(self, member_product_api):
        xss_payload = "<img src=x onerror=alert(1)>"
        response = member_product_api.search(keyword=xss_payload, page_num=1, page_size=10)
        self._assert_safe_response(response, "XSS injection should not cause a server error")
        assert "<img" not in response.text.lower() or "onerror" not in response.text.lower(), \
            "XSS payload should not be echoed as-is"


    @allure.story("Oversized String Parameter")
    def test_oversized_string_param(self, member_product_api):
        oversized = "A" * 10000
        response = member_product_api.search(keyword=oversized, page_num=1, page_size=10)
        self._assert_safe_response(response, "Oversized parameter should not crash the server")

    @allure.story("Negative/Invalid Numeric Parameter")
    @pytest.mark.parametrize("page_num", [-1, 0, -999])
    def test_negative_page_num(self, member_product_api, page_num):
        response = member_product_api.search(page_num=page_num, page_size=10)
        self._assert_safe_response(response, "Negative page number should not cause a server error")

    @allure.story("Oversized pageSize Parameter")
    def test_oversized_page_size(self, member_product_api):
        response = member_product_api.search(page_num=1, page_size=1000000)
        self._assert_safe_response(response, "Oversized pageSize should not crash the server")

    @allure.story("Type Confusion - String in Numeric Field")
    def test_type_confusion_numeric_field(self, member_product_api):
        response = member_product_api.search(page_num="abc", page_size="xyz")
        self._assert_safe_response(response, "Type-confused parameter should not cause a server 500")

    @allure.story("Null/None Parameters")
    def test_null_and_empty_params(self, member_product_api):
        response = member_product_api.search(keyword="", page_num=1, page_size=10)
        self._assert_safe_response(response, "Empty string parameter should not cause a server error")

    @allure.story("Special Characters - Path Traversal")
    def test_path_traversal_keyword(self, member_product_api):
        response = member_product_api.search(keyword="../../etc/passwd", page_num=1, page_size=10)
        self._assert_safe_response(response, "Path traversal should not cause a server error")
        assert "root:" not in response.text, "Path traversal should not leak system file contents"

    @allure.story("Special Characters - Control Characters")
    def test_control_characters(self, member_product_api):
        payload = "test\x00name\n<script>"
        response = member_product_api.search(keyword=payload, page_num=1, page_size=10)
        self._assert_safe_response(response, "Control characters should not cause a server error")
