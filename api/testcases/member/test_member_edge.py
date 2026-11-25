import pytest
import allure
import requests

from common.assertions import ApiAssertion
from common.config.config_loader import ConfigLoader


_base_url = ConfigLoader().get("member.base_url", "").rstrip("/")


@allure.feature("Frontend Login/Register - Boundary and Exception")
class TestLoginEdge:

    def setup_method(self):
        self.aa = ApiAssertion()

    @allure.story("Login boundary: password too long (128 chars)")
    def test_login_password_too_long(self, member_login_api):
        resp = member_login_api.login("demo", "a" * 128)
        assert resp.status_code in (200, 400, 404, 422)

    @allure.story("Login boundary: username with only spaces")
    def test_login_username_whitespace(self, member_login_api):
        resp = member_login_api.login("   ", "Test@123456")
        body = resp.json()
        assert body.get("code", 200) != 200

    @allure.story("Login exception: SQL injection username")
    @pytest.mark.parametrize("payload", [
        "' OR '1'='1",
        "admin'--",
        "1'; DROP TABLE ums_member;--",
    ])
    def test_login_sql_injection_username(self, member_login_api, payload):
        resp = member_login_api.login(payload, "Test@123456")
        body = resp.json()
        assert body.get("code", 200) != 200, f"SQL injection payload={payload} should not log in successfully"

    @allure.story("Login exception: XSS username")
    def test_login_xss_username(self, member_login_api):
        resp = member_login_api.login("<script>alert(1)</script>", "Test@123456")
        assert resp.status_code in (200, 400, 422)

    @allure.story("Unauthenticated access: cart list should return 401")
    def test_cart_list_requires_auth(self):
        if not _base_url:
            pytest.skip("member base_url is not configured")
        resp = requests.get(f"{_base_url}/cart/list", timeout=10)
        body = resp.json() if resp.status_code == 200 else {}
        assert resp.status_code == 401 or body.get("code", 200) != 200

    @allure.story("Unauthenticated access: placing an order should return 401")
    def test_order_requires_auth(self):
        if not _base_url:
            pytest.skip("member base_url is not configured")
        resp = requests.get(f"{_base_url}/order/list", timeout=10)
        body = resp.json() if resp.status_code == 200 else {}
        assert resp.status_code == 401 or body.get("code", 200) != 200


@allure.feature("Frontend Address Management - Boundary and Exception")
class TestAddressEdge:

    def setup_method(self):
        self.aa = ApiAssertion()

    @allure.story("Add address boundary: invalid phone format - mall backend defect (no format validation)")
    def test_add_address_bad_phone(self, address_api):
        resp = address_api.add({
            "name": "Test", "phone": "123",
            "province": "Beijing", "city": "Beijing",
            "receiverDetailAddress": "testAddress", "defaultStatus": 0,
        })
        body = resp.json()
        assert body.get("code", 200) != 200, \
            f"BUG: an invalid phone number should be rejected, but mall returned code={body.get('code')}"

    @allure.story("Add address boundary: name too long")
    def test_add_address_long_name(self, address_api):
        resp = address_api.add({
            "name": "A" * 64, "phone": "13800138000",
            "province": "Beijing", "city": "Beijing",
            "receiverDetailAddress": "testAddress", "defaultStatus": 0,
        })
        assert resp.status_code in (200, 400, 422, 404, 500)

    @allure.story("Add address boundary: empty detail address - mall backend defect (required field not validated)")
    def test_add_address_empty_detail(self, address_api):
        resp = address_api.add({
            "name": "Test", "phone": "13800138000",
            "province": "Beijing", "city": "Beijing",
            "receiverDetailAddress": "", "defaultStatus": 0,
        })
        body = resp.json()
        assert body.get("code", 200) != 200, \
            f"BUG: empty receiverDetailAddress should be rejected, but mall returned code={body.get('code')}"

    @allure.story("Add address boundary: empty phone - mall backend defect (required field not validated)")
    def test_add_address_empty_phone(self, address_api):
        resp = address_api.add({
            "name": "Test", "phone": "",
            "province": "Beijing", "city": "Beijing",
            "receiverDetailAddress": "Haidian District Test", "defaultStatus": 0,
        })
        body = resp.json()
        assert body.get("code", 200) != 200, \
            f"BUG: empty phone should be rejected, but mall returned code={body.get('code')}"

    @allure.story("Delete exception: delete a nonexistent address")
    def test_delete_nonexistent_address(self, address_api):
        resp = address_api.delete(99999)
        assert resp.status_code in (200, 404, 500)
