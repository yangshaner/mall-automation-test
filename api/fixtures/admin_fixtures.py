# fixtures//admin_fixtures.py

import pytest
import allure
from typing import Any

from api.objects.admin.product_api import ProductApi
from api.objects.admin.brand_api import BrandApi
from api.objects.admin.order_api import OrderApi
from api.objects.admin.category_api import CategoryApi
from api.objects.admin.coupon_api import CouponApi
from api.objects.admin.admin_api import AdminApi
from common.client.admin_client import AdminClient
from common.config.config_loader import config
from common.db.mysql_util import mysql
from common.utils.data_generator import DataGenerator
from common.assertions import ApiAssertion
from common.utils.id_fetcher import IDFetcherWithAllure


@pytest.fixture(scope="session")
def admin_client():
    client = AdminClient()
    client._login()
    return client


@pytest.fixture(scope="session")
def admin_client_unauthenticated():
    return AdminClient()


@pytest.fixture(scope="session")
def admin_credentials():
    account = config.get("admin", {})
    return {
        "username": account["username"],
        "password": account["password"]
    }


@pytest.fixture(scope="session")
def product_api(admin_client):
    return ProductApi(admin_client)


@pytest.fixture(scope="session")
def brand_api(admin_client):
    return BrandApi(admin_client)


@pytest.fixture(scope="session")
def category_api(admin_client):
    return CategoryApi(admin_client)


@pytest.fixture(scope="session")
def order_api(admin_client):
    return OrderApi(admin_client)


@pytest.fixture(scope="session")
def coupon_api(admin_client):
    return CouponApi(admin_client)


@pytest.fixture(scope="session")
def admin_api(admin_client):
    return AdminApi(admin_client)


@pytest.fixture(scope="session")
def admin_api_unauthenticated(admin_client_unauthenticated):
    return AdminApi(admin_client_unauthenticated)


@pytest.fixture(scope="session")
def data_generator():
    return DataGenerator()


@pytest.fixture(scope="session")
def db_assert():

    class DBAssert:
        @staticmethod
        def assert_exists(table: str, condition: str, params: tuple = None):
            sql = f"select count(*) as count from {table} where {condition}"
            result = mysql.query(sql, params)
            assert result[0].get('count', 0) > 0, f"data does not exist：{table} where {condition}"
            return result[0].get('count')

        @staticmethod
        def assert_not_exists(table: str, condition: str, params: tuple = None):
            sql = f"select count(*) as count from {table} where {condition}"
            result = mysql.query(sql, params)
            assert result[0].get('count', 0) == 0, f"data exist：{table} where {condition}"

        @staticmethod
        def assert_field_value(table: str, field: str, expected: Any, condition: str, params: tuple = None):
            sql = f"select {field} from {table} where {condition}"
            result = mysql.query(sql, params)
            assert result, f"No data found：{table} where {condition}"
            actual = result[0].get(field)
            assert actual == expected, f"field {field} expected {expected}，actual {actual}"

    return DBAssert


@pytest.fixture
def test_brand(brand_api, data_generator, db_assert):
    with allure.step("Create a test brand"):
        data = data_generator.brand_data()
        response = brand_api.create(data)
        assert response.status_code == 200
        ApiAssertion().assert_success(response, "Brand creation failed")

        brand_name = data['name']
        brand_id = IDFetcherWithAllure.get_id_by_module(
            api_instance=brand_api,
            module='brand',
            search_value=brand_name,
            page_size=10,
            max_pages=100
        )
        assert brand_id, "Brand creation failed，no ID returned. "

        db_assert.assert_exists('pms_brand', 'id = %s', (brand_id,))

        allure.attach(str(brand_id), "Brand ID", allure.attachment_type.TEXT)
        yield brand_id

    with allure.step("Clean up test brand"):
        brand_api.delete(brand_id)
        db_assert.assert_not_exists('pms_brand', 'id = %s', (brand_id,))


@pytest.fixture
def test_category(category_api, data_generator, db_assert):
    with allure.step("Create test category"):
        data = data_generator.product_category_data()
        response = category_api.create(data)
        assert response.status_code == 200

        category_name = data['name']
        category_id = IDFetcherWithAllure.get_id_by_module(
            api_instance=category_api,
            module='category',
            search_value=category_name,
            page_size=10,
            max_pages=100,
            extra_params={'parent_id': 0}
        )
        assert category_id, "Creation of category failed, no ID returned."

        allure.attach(str(category_id), "Category ID", allure.attachment_type.TEXT)
        yield category_id

    with allure.step("Clean up test category"):
        category_api.delete(category_id)
        db_assert.assert_not_exists('pms_product_category', 'id = %s', (category_id,))

@pytest.fixture
def test_product(product_api, data_generator, test_brand, test_category, db_assert):
    with allure.step("Create test product"):
        data = data_generator.product_data(test_brand, test_category)
        response = product_api.create(data)
        assert response.status_code == 200
        ApiAssertion().assert_success(response, "Failed to create product")

        product_name = data['name']
        product_id = IDFetcherWithAllure.get_id_by_module(
            api_instance=product_api,
            module='product',
            search_value=product_name,
            list_method_name='list',
            page_size=10,
            max_pages=100
        )
        assert product_id, f"Creating the product failed, no product ID was not found: {product_name}"

        db_assert.assert_exists('pms_product', 'id = %s', (product_id,))

        allure.attach(str(product_id), "Product ID", allure.attachment_type.TEXT)
        yield product_id


@pytest.fixture
def test_coupon(coupon_api, data_generator, db_assert):
    with allure.step("Create test coupon"):
        data = data_generator.coupon_data()
        response = coupon_api.create(data)
        assert response.status_code == 200
        result = response.json()
        coupon_id = result.get('data', {}).get('id')
        assert coupon_id, "Creating a coupon failed, no ID returned. "

        db_assert.assert_exists('sms_coupon', 'id = %s', (coupon_id,))

        allure.attach(str(coupon_id), "Coupon ID", allure.attachment_type.TEXT)
        yield coupon_id

    with allure.step("Clean up test coupons"):
        coupon_api.delete(coupon_id)
        db_assert.assert_not_exists('sms_coupon', 'id = %s', (coupon_id,))
