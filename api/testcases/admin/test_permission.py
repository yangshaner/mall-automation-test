# testcases/admin/test_permission.py
import pytest
import allure

from common.assertions import ApiAssertion
from common.utils.role_manager import role_manager
from common.client.admin_client import AdminClient

from common.utils.data_generator import DataGenerator

@allure.feature("Admin Permission Management")
class TestAdminPermission:

    def setup_method(self):
        self.api_assert = ApiAssertion()

    @allure.story("Role Permission Configuration")
    def test_role_permission_config(self):
        roles = role_manager.get_all_roles()
        assert len(roles) > 0, "No roles configured"

        admin_role = role_manager.get_role(1)
        assert admin_role, "Super admin role does not exist"
        assert "admin:*" in admin_role.permissions, "Super admin is missing the admin:* permission"

        readonly_role = role_manager.get_role(4)
        assert readonly_role, "Readonly user role does not exist"
        assert "product:read" in readonly_role.permissions, "Readonly user is missing the product:read permission"

    @allure.story("Get User Permission")
    def test_user_permission(self):
        users = role_manager.get_all_users()
        assert len(users) > 0, "No test users configured"

        for user in users:
            perms = role_manager.get_user_permission(user.username)
            assert perms is not None, f"User {user.username} has no permissions"

            for role_id in user.roles:
                role = role_manager.get_role(role_id)
                if role:
                    for perm in role.permissions:
                        assert perm in perms, f"User {user.username} is missing role permission {perm}"

    @allure.story("Permission Check")
    @pytest.mark.parametrize("username,permission,expected", [
        ("admin", "product:write", True),
        ("admin", "order:delete", True),
        ("product_admin", "product:write", True),
        ("product_admin", "order:write", False),
        ("order_admin", "order:write", True),
        ("order_admin", "product:write", False),
        ("readonly_user", "product:read", True),
        ("readonly_user", "product:write", False),
    ])
    def test_permission(self, username, permission, expected):
        has_permission = role_manager.has_permission(username, permission)
        assert has_permission == expected, f"Permission {permission} for user {username} should be {expected}"

    @allure.story("Resource Access Control")
    @pytest.mark.parametrize("username,resource_id,expected", [
        ("admin", 1, True),
        ("product_admin", 1, True),
        ("order_admin", 1, False),
        ("product_admin", 4, False),
    ])
    def test_resource_permission(self, username, resource_id, expected):
        can_access = role_manager.can_access_resource(username, resource_id)
        if can_access is None:
            can_access = False
        assert can_access == expected, f"Access to resource {resource_id} for user {username} should be {expected}"


    @pytest.mark.skipif(1==1, reason="readonly user does not seem to be an actual client")
    @allure.story("Real API Permission Verification")
    def test_api_permission_denied(self):
        client = AdminClient()
        login_response = client.post("/admin/login", json={
            "username": "readonly_user",
            "password": "readonly"
        })
        if login_response.status_code != 200:
            pytest.skip("Readonly user login failed, please confirm the user exists")

        login_data = login_response.json()
        if login_data.get('code') != 200:
            pytest.skip(f"Readonly user login failed: {login_data.get('message')}")

        token = login_data.get('data', {}).get('token', '')
        client.set_token(token)

        print(repr(login_data.get('data', {}).get('tokenHead')))
        print(repr(login_data.get('data', {}).get('token')))
        print(repr(token))
        print("cookies:", client.session.cookies.get_dict())
        print("headers:", client.session.headers)
        print("username:", client._username)
        print("password:", client._password)


        product_data = {
            "name": f"permissionTestProducts{DataGenerator.random_string(4)}",
            "productSn": "PERM_TEST_001",
            "price": 99.99,
            "stock": 100,
            "brandId": 1,
            "productCategoryId": 1,
            'description': f'This is the test description of the permission testing product.',
            'subTitle': f'Test Subtitle{DataGenerator.random_string(4)}',
            'publishStatus': 1,
            'verifyStatus': 1,
            'sort': DataGenerator.random_int(0, 100)
        }
        response = client.post("/product/create", json=product_data)

        if response.status_code == 200:
            result = response.json()
            print("readonly user create product response:", result)
            assert result.get('code') != 200, "Readonly user should not have permission to create products"
        else:
            assert response.status_code in [401, 403], f"Expected 401 or 403, got {response.status_code}"

    @allure.story("Login Tests for Different Roles")
    @pytest.mark.parametrize("username,password,expected_success", [
        ("admin", "macro123",  True),
        ("product_admin", "prod1234", True),
        ("order_admin", "order123",  True),
        ("readonly_user", "readonly", True),
        ("nonexistent_user", "", False)
    ])
    def test_different_users_login(self, username, password, expected_success):
        client = AdminClient()
        response = client.post("/admin/login", json={
            "username": username,
            "password": password
        })

        print(f"{username} response code:", response.status_code)
        if expected_success:
            result = self.api_assert.assert_success(response, f"User {username} login should succeed")
            data = result.get('data', {})
            self.api_assert.assert_field_exist(data, "token", "missing token")
        else:
            if response.status_code == 200:
                result = response.json()
                assert result.get('code') != 200, f"User {username} login should fail"
            else:
                assert response.status_code in [401, 403], f"Expected 401 or 403, got {response.status_code}"

    @allure.story("Get User Info")
    def test_get_user_info_by_username(self, admin_api):
        response = admin_api.list(page_num=1, page_size=1)
        result = self.api_assert.assert_success(response, "Failed to get user list")
        users = result.get('data', {}).get('list', [])

        if not users:
            pytest.skip("No user available")

        user_id = users[0].get('id')
        response = admin_api.detail(user_id)
        result = self.api_assert.assert_success(response, "Failed to get user info")
        data = result.get('data', {})
        self.api_assert.assert_field_exist(data, "username", "missing username")
        self.api_assert.assert_field_exist(data, "status", "missing status")
        self.api_assert.assert_field_exist(data, "createTime", "missing create time")
