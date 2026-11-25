# testcases/admin/test_login.py
import pytest
import allure

from common.assertions import ApiAssertion


@allure.feature("Admin Login Authentication")
class TestAdminLogin:

    def setup_method(self):
        self.api_assert = ApiAssertion()

    @allure.story("Login")
    def test_login_success(self, admin_api_unauthenticated, admin_credentials):
        response = admin_api_unauthenticated.login(
            admin_credentials["username"], admin_credentials["password"]
        )
        result = self.api_assert.assert_success(
            response, "Admin login failed", check_response_code=False, check_data=False)
        data = result.get('data', {})
        self.api_assert.assert_field_exist(data, "token", "missing token")
        self.api_assert.assert_field_exist(data, "tokenHead", "missing tokenHead")

        token = data.get('token')
        assert len(token) > 0, "token is empty"
        assert data.get('tokenHead') in ['Bearer ', ''], 'invalid tokenHead format'

    @allure.story("Login")
    def test_login_wrong_password(self, admin_api_unauthenticated, admin_credentials):
        response = admin_api_unauthenticated.login(admin_credentials["username"], "wrong_password")
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            result = response.json()
            assert result.get('code') != 200, "Wrong password should not return success"

    @allure.story("Login")
    def test_login_empty_username(self, admin_api_unauthenticated, admin_credentials):
        response = admin_api_unauthenticated.login("", admin_credentials["password"])
        result = response.json()
        assert result.get('code') != 200, "Empty username should fail"

    @allure.story("Login")
    def test_login_empty_password(self, admin_api_unauthenticated, admin_credentials):
        response = admin_api_unauthenticated.login(admin_credentials["username"], "")
        result = response.json()
        assert result.get('code') != 200, "Empty password should fail"

    @allure.story("Logout")
    def test_logout(self, admin_client):
        response = admin_client.post("/admin/logout")
        self.api_assert.assert_success(response, "Logout failed", check_data=False)

    @allure.story("Refresh Token")
    def test_refresh_token(self, admin_client):
        response = admin_client.get("/admin/refreshToken")
        result = self.api_assert.assert_success(response, "Failed to refresh token")
        data = result.get('data', {})
        self.api_assert.assert_field_exist(data, "token", "missing token after refresh")
        self.api_assert.assert_field_exist(data, "tokenHead", "missing tokenHead after refresh")

    @allure.story("Get Current User Info")
    def test_get_admin_info(self, admin_client):
        response = admin_client.get("/admin/info")
        result = self.api_assert.assert_success(response, "Failed to get user info")
        data = result.get('data', {})
        self.api_assert.assert_field_exist(data, "username", "missing username")
        self.api_assert.assert_field_exist(data, "roles", "missing roles")

    @allure.story("User Registration")
    def test_register_user(self, admin_api, data_generator):
        username = f"test_{data_generator.random_string(6)}"
        data = {
            "username": username,
            "password": "12345678",
            "nickName": f"testUser_{username}",
            "email": f"{username}@test.com"
        }
        response = admin_api.register(data)
        result = self.api_assert.assert_success(response, "User registration failed")
        user_data = result.get('data', {})
        self.api_assert.assert_field_exist(user_data, 'id', "missing user ID")

        user_id = user_data.get('id')
        if user_id:
            admin_api.delete(user_id)
