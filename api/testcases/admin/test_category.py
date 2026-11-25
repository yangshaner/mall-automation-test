# testcases/admin/test_category.py
import pytest
import allure
import time

from common.assertions import ApiAssertion, DBAssertion
from common.utils.id_fetcher import IDFetcherWithAllure
from api.fixtures.admin_fixtures import data_generator
from common.db.mysql_util import mysql


@allure.feature("Product Category Management")
class TestCategory:

    def setup_method(self):
        self.api_assert = ApiAssertion()
        self.db_assert = DBAssertion()

    @allure.story("Category Tree")
    def test_get_category_tree(self, category_api):
        response = category_api.list_with_children()
        self.api_assert.assert_success(response, "Failed to get category tree")
        data = response.json().get('data', [])
        assert isinstance(data, list), "A list should be returned"
        if data:
            first = data[0]
            self.api_assert.assert_field_exist(data[0], "id", "missing id")
            self.api_assert.assert_field_exist(data[0], "name", "missing name")
            self.api_assert.assert_field_exist(data[0], "children", "missing children")
            assert isinstance(first.get('children'), list), "children should be a list"

    @allure.story("Category List")
    def test_get_category_list(self, category_api):
        response = category_api.list(parent_id=0, page_num=1, page_size=10)
        result = self.api_assert.assert_success(response, "Failed to get paginated list")
        data = result.get('data', [])
        self.api_assert.assert_field_exist(data, 'list', "missing list")
        self.api_assert.assert_field_exist(data, 'total', "missing total")

    @allure.story("Create Category")
    def test_create_category(self, category_api, data_generator):
        category_name = f"testCategory_{data_generator.random_string(4)}"
        data = {
            "parentId": 0,
            "name": category_name,
            "productUnit": "件",
            "sort": 9999,
            "showStatus": 1,
            "navStatus": 0
        }
        response = category_api.create(data)
        self.api_assert.assert_success(response, "Failed to create category")

        time.sleep(0.5)

        print(f"New category name: {category_name}")

        category_id = IDFetcherWithAllure.get_id_by_module(
            api_instance=category_api,
            module='category',
            search_value=category_name,
            page_size=10,
            max_pages=100,
            extra_params={'parent_id': 0}
        )

        if not category_id:
            category_id = IDFetcherWithAllure.get_id_by_module(
                api_instance=category_api,
                module='category',
                search_value=category_name,
                page_size=10,
                max_pages=100,
                exact_match=False,
                extra_params={'parent_id': 0}
            )

        print(f"Created category id: {category_id}")
        assert category_id, f"Created category not found: {category_name}"
        self.db_assert.assert_exists('pms_product_category', 'id = %s', (category_id,))
        self.db_assert.assert_field_value('pms_product_category', 'name', data['name'],
                                          'id = %s', (category_id,))
        category_api.delete(category_id)
        self.db_assert.assert_not_exists('pms_product_category', 'id = %s', (category_id,))

    @allure.story("Update Category")
    def test_update_category(self, category_api, data_generator):
        category_name = f"TEST_{data_generator.random_string(4)}"
        data = {
            "parentId": 0,
            "name": category_name,
            "productUnit": "件",
            "sort": 9999,
            "showStatus": 1,
            "navStatus": 0
        }
        response = category_api.create(data)
        self.api_assert.assert_success(response, "Failed to create category")

        time.sleep(0.5)
        category_id = mysql.get_id_by_field('pms_product_category', 'name', category_name)
        assert category_id, f"Created category not found: {category_name}"

        update_data = {
            "parentId": 0,
            "name": f"updated_{category_name}",
            "sort": 50,
            "showStatus": 1,
            "navStatus": 0
        }
        print(f"category update id:{category_id}")
        print(f"category update name:{category_name}")
        response = category_api.update(category_id, update_data)
        self.api_assert.assert_success(response, "Failed to update category")
        self.db_assert.assert_field_value('pms_product_category', 'name', update_data['name'],
                                          'id = %s', (category_id,))
        self.db_assert.assert_field_value('pms_product_category', 'sort', update_data['sort'],
                                          'id = %s', (category_id,))

        category_api.delete(category_id)

    @allure.story("Category Detail")
    def test_get_category_detail(self, category_api, data_generator):
        category_name = f"testCategory_{data_generator.random_string(4)}"
        data = {
            "parentId": 0,
            "name": category_name,
            "productUnit": "件",
            "sort": 50,
            "showStatus": 1,
            "navStatus": 0
        }
        response = category_api.create(data)
        self.api_assert.assert_success(response, "Failed to create category")

        category_id = mysql.get_id_by_field('pms_product_category', 'name', category_name)
        assert category_id, f"Created category not found: {category_name}"

        response = category_api.detail(category_id)
        result = self.api_assert.assert_success(response, "Failed to get category detail")
        detail = result.get('data', {})
        assert detail.get('id') == category_id, "Category ID mismatch"
        assert detail.get('name') == category_name, "Category name mismatch"
        self.api_assert.assert_field_exist(detail, 'level', "missing level")
        self.api_assert.assert_field_exist(detail, 'sort', "missing sort")

        category_api.delete(category_id)

    @allure.story("Show Status")
    @pytest.mark.parametrize("show_status", [0, 1])
    def test_update_show_status(self, category_api, data_generator, show_status):
        category_name = f"testCategory_{data_generator.random_string(4)}"
        data = {
            "parentId": 0,
            "name": category_name,
            "productUnit": "件",
            "sort": 9999,
            "showStatus": 1,
            "navStatus": 0
        }
        response = category_api.create(data)
        self.api_assert.assert_success(response, "Failed to create category")

        category_id = mysql.get_id_by_field('pms_product_category', 'name', category_name)
        assert category_id, f"Created category not found: {category_name}"

        response = category_api.update_show_status([category_id], show_status)
        self.api_assert.assert_success(response, "Failed to update show status")
        self.db_assert.assert_field_value('pms_product_category', 'show_status', show_status,
                                          'id = %s', (category_id,))

        category_api.delete(category_id)

    @allure.story("Navigation Status")
    @pytest.mark.parametrize("nav_status", [0, 1])
    def test_update_nav_status(self, category_api, data_generator, nav_status):
        category_name = f"testCategory_{data_generator.random_string(4)}"
        data = {
            "parentId": 0,
            "name": category_name,
            "productUnit": "件",
            "sort": 9999,
            "showStatus": 1,
            "navStatus": 0
        }
        response = category_api.create(data)
        self.api_assert.assert_success(response, "Failed to create category")

        category_id = mysql.get_id_by_field('pms_product_category', 'name', category_name)
        assert category_id, "Created category not found"

        response = category_api.update_nav_status([category_id], nav_status)
        self.api_assert.assert_success(response, "Failed to update navigation status")
        self.db_assert.assert_field_value('pms_product_category', 'nav_status', nav_status,
                                          'id = %s', (category_id,))

        category_api.delete(category_id)

    @allure.story("Delete Category")
    def test_delete_category(self, category_api, data_generator):
        category_name = f"testCategory_{data_generator.random_string(4)}"
        data = {
            "parentId": 0,
            "name": category_name,
            "productUnit": "件",
            "sort": 9999,
            "showStatus": 1,
            "navStatus": 0
        }
        response = category_api.create(data)
        self.api_assert.assert_success(response, "Failed to create category")

        category_id = mysql.get_id_by_field('pms_product_category', 'name', category_name)
        assert category_id, "Created category not found"

        self.db_assert.assert_exists('pms_product_category', 'id = %s', (category_id,))
        category_api.delete(category_id)
        self.api_assert.assert_success(response, "Failed to delete category")

        self.db_assert.assert_not_exists('pms_product_category', 'id = %s', (category_id,))
