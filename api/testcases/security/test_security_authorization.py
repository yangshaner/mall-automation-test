# testcase/security/test_security_authorization.py
import pytest
import allure

from common.assertions import ApiAssertion


@allure.feature("Security Test - Authorization and Access Control")
class TestSecurityAuthorization:

    def setup_method(self):
        self.api_assert = ApiAssertion()


    @allure.story("Unauthorized Access to Admin Endpoints")
    def test_unauthorized_admin_access(self, anon_session, admin_base_url):
        response = anon_session.get(f"{admin_base_url}/product/list", params={"pageNum": 1, "pageSize": 10})
        result = response.json()
        assert response.status_code in (401, 403) or result.get("code") != 200, \
            "Unauthorized access to admin endpoints should be denied"

    @allure.story("Unauthorized Access to Member Endpoints Requiring Auth")
    @pytest.mark.parametrize("path", [
        "/cart/list",
        "/order/list",
        "/member/coupon/list",
        "/member/productCollection/list",
    ])
    def test_unauthorized_member_protected(self, anon_session, member_base_url, path):
        response = anon_session.get(f"{member_base_url}{path}")
        result = response.json()
        assert response.status_code in (401, 403) or result.get("code") != 200, \
            f"Unauthorized access to {path} should be denied"

    @allure.story("Public Endpoints Require No Auth")
    @pytest.mark.parametrize("path,params", [
        ("/product/search", {"pageNum": 1, "pageSize": 5}),
        ("/home/content", None),
    ])
    def test_public_api_no_auth_needed(self, anon_session, member_base_url, path, params):
        response = anon_session.get(f"{member_base_url}{path}", params=params)
        result = response.json()
        assert response.status_code == 200, f"Public endpoint {path} returned an unexpected HTTP status code"
        assert result.get("code") == 200, f"Business code for public endpoint {path} should be 200"

    @allure.story("Access with Forged Token")
    def test_forged_token_access(self, anon_session, admin_base_url):
        headers = {"Authorization": "Bearer forged.invalid.token.string"}
        response = anon_session.get(
            f"{admin_base_url}/product/list",
            params={"pageNum": 1, "pageSize": 10},
            headers=headers
        )
        result = response.json()
        assert response.status_code in (401, 403) or result.get("code") != 200, \
            "Access to admin endpoints with a forged token should be denied"

    @allure.story("Cross-Platform Token Not Interchangeable")
    def test_member_token_cannot_access_admin(self, member_client, admin_base_url):
        member_token = member_client.get_token()
        if not member_token:
            pytest.skip("Member token not obtained")

        import requests
        response = requests.get(
            f"{admin_base_url}/product/list",
            params={"pageNum": 1, "pageSize": 10},
            headers={"Authorization": f"Bearer {member_token}"}
        )
        result = response.json()
        assert response.status_code in (401, 403) or result.get("code") != 200, \
            "A member token should not grant access to admin endpoints"


    @allure.story("Readonly User Escalation to Write Operation")
    def test_readonly_user_create_product_denied(self, admin_client_factory):
        try:
            client = admin_client_factory("readonly_user", "readonly")
        except Exception as e:
            pytest.skip(f"Readonly user login failed: {e}")

        product_data = {
            "name": "oversteppedTestProduct",
            "productSn": "SEC_TEST_001",
            "price": 99.99,
            "stock": 10,
            "brandId": 1,
            "productCategoryId": 1,
            "publishStatus": 1,
            "verifyStatus": 1,
        }
        response = client.post("/product/create", json=product_data)
        result = response.json()
        assert result.get("code") != 200 or response.status_code in (401, 403), \
            "A readonly user should not be able to create products"

    @allure.story("Product Admin Escalation to Order Operation")
    def test_product_admin_access_order_denied(self, admin_client_factory):
        try:
            client = admin_client_factory("product_admin", "prod1234")
        except Exception as e:
            pytest.skip(f"Product admin login failed: {e}")

        response = client.get("/order/list", params={"pageNum": 1, "pageSize": 10})
        result = response.json()
        assert result.get("code") != 200 or response.status_code in (401, 403), \
            "A product admin should not be able to access the order list"

    @allure.story("Order Admin Escalation to Product Operation")
    def test_order_admin_create_product_denied(self, admin_client_factory):
        try:
            client = admin_client_factory("order_admin", "order123")
        except Exception as e:
            pytest.skip(f"Order admin login failed: {e}")

        product_data = {
            "name": "oversteppedTestProduct_orderManager",
            "productSn": "SEC_TEST_002",
            "price": 99.99,
            "stock": 10,
            "brandId": 1,
            "productCategoryId": 1,
            "publishStatus": 1,
            "verifyStatus": 1,
        }
        response = client.post("/product/create", json=product_data)
        result = response.json()
        assert result.get("code") != 200 or response.status_code in (401, 403), \
            "An order admin should not be able to create products"

    @allure.story("Disabled User Login Denied")
    def test_disabled_user_login_denied(self, admin_base_url):
        import requests
        response = requests.post(
            f"{admin_base_url}/admin/login",
            json={"username": "disabled_user", "password": "macro123"}
        )
        result = response.json()
        assert result.get("code") != 200, "A disabled user should not be able to log in"

    @allure.story("Horizontal Privilege Escalation - Access Others' Orders")
    def test_horizontal_privilege_order(self, member_order_api):
        response = member_order_api.detail(999999999)
        result = response.json()
        if result.get("code") == 200:
            data = result.get("data") or {}
            order_items = data.get("orderItemList") or []
            has_order_identity = any(
                data.get(field) for field in ("orderSn", "id", "orderNo", "orderId")
            )
            assert len(order_items) == 0 and not has_order_identity, \
                "Accessing a nonexistent/foreign order should not return valid order data"
