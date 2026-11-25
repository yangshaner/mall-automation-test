# testcases/member/test_login.py
import pytest
import allure

from common.assertions import ApiAssertion

@allure.feature("Member Login")
class TestMemberLogin:

    def setup_method(self):
        self.api_assert = ApiAssertion()

    @allure.story("Member Login")
    def test_login_success(self, member_login_api_unauthenticated, member_credentials):
        response = member_login_api_unauthenticated.login(
            member_credentials["username"], member_credentials["password"]
        )
        result = self.api_assert.assert_success(response, "Member login failed")

        token_data = result.get('data', {})
        self.api_assert.assert_field_exist(token_data, "token", "Missing token")
        self.api_assert.assert_field_exist(token_data, "tokenHead", "Missing tokenHead")

    @allure.story("Member Login")
    def test_login_wrong_password(self, member_login_api_unauthenticated, member_credentials):
        response = member_login_api_unauthenticated.login(member_credentials["username"], "wrong_password")
        result = response.json()
        assert result.get('code') != 200, "Login should fail with a wrong password"

    @allure.story("Member Login")
    def test_login_empty_username(self, member_login_api_unauthenticated, member_credentials):
        response = member_login_api_unauthenticated.login("", member_credentials["password"])
        result = response.json()
        assert result.get('code') != 200, "Login should fail with an empty username"

    @allure.story("Get Auth Code")
    def test_get_auth_code(self, member_login_api):
        response = member_login_api.get_auth_code("13800138000")
        self.api_assert.assert_success(response, "Failed to get auth code")


    @allure.story("Get Member Info")
    def test_get_member_info(self, member_login_api):
        response = member_login_api.get_info()
        result = self.api_assert.assert_success(response, "Failed to get member info")

        data = result.get('data', {})
        self.api_assert.assert_field_exist(data, 'username', "Missing username")
        self.api_assert.assert_field_exist(data, 'status', "Missing status")

    @allure.story("Refresh Token")
    def test_refresh_token(self, member_login_api):
        response = member_login_api.refresh_token()
        result = self.api_assert.assert_success(response, "Failed to refresh token")

        token_data = result.get('data', {})
        self.api_assert.assert_field_exist(token_data, 'token', "Missing new token")
