# fixtures/product_fixtures.py
import pytest
import allure
import logging

from common.client.admin_client import AdminClient
from common.assertions import DBAssertion
from common.utils.id_fetcher import IDFetcherWithAllure
from api.objects.admin.brand_api import BrandApi
from api.objects.admin.category_api import CategoryApi
from api.objects.admin.product_api import ProductApi

logger = logging.getLogger(__name__)


def _bind_api(api_cls, client):
    return api_cls(client)


def _assert_create_ok(response, resource: str):
    result = response.json()
    assert response.status_code == 200 and result.get("code") == 200, \
        f"Failed to create {resource}: status={response.status_code}, body={response.text[:300]}"


@pytest.fixture(scope="session")
def admin_client_for_setup():
    client = AdminClient()

    with allure.step("Admin client login"):
        try:
            login_result= client._login()
            logger.info(f"Admin client login success: {login_result.get('user_info', {}).get('username', 'admin')}")

            info_response = client.get("/admin/info")
            if info_response.status_code == 200:
                info_data = info_response.json()
                if info_data.get('code') == 200:
                    logger.info("Admin client authentication verified")
                else:
                    logger.warning(f"Admin client authentication failed, {info_data.get('message')}")
            else:
                logger.warning(f"Admin client auth verify failed with status: {info_response.status_code}")
        except Exception as e:
            logger.error(f"Admin client logi failed: {e}")
            raise RuntimeError(f"Admin client logi failed, {e}")

    return client


@pytest.fixture
def test_product(admin_client_for_setup, data_generator):
    brand_api = _bind_api(BrandApi, admin_client_for_setup)
    category_api = _bind_api(CategoryApi, admin_client_for_setup)
    product_api = _bind_api(ProductApi, admin_client_for_setup)

    with allure.step("Create test product"):
        brand_data = data_generator.brand_data()
        brand_name = brand_data["name"]
        _assert_create_ok(brand_api.create(brand_data), "brand")
        brand_id = IDFetcherWithAllure.get_id_by_module(
            api_instance=brand_api,
            module="brand",
            search_value=brand_name,
            page_size=10,
            max_pages=100
        )
        assert brand_id, f"Failed to create brand, brand ID not found: {brand_name}"

        category_data = data_generator.product_category_data()
        category_name = category_data["name"]
        _assert_create_ok(category_api.create(category_data), "category")
        category_id = IDFetcherWithAllure.get_id_by_module(
            api_instance=category_api,
            module="category",
            search_value=category_name,
            page_size=100,
            max_pages=10,
            extra_params={"parent_id": 0}
        )
        assert category_id, f"Failed to create category, category ID not found: {category_name}"

        product_data = data_generator.product_data(brand_id, category_id)
        product_name = product_data["name"]
        _assert_create_ok(product_api.create(product_data), "product")
        product_id = IDFetcherWithAllure.get_id_by_module(
            api_instance=product_api,
            module="product",
            search_value=product_name,
            list_method_name="list",
            page_size=10,
            max_pages=100
        )
        assert product_id, f"Failed to create product, product ID not found: {product_name}"

        admin_client_for_setup.post("/product/update/verifyStatus",
                                    params={"ids": [product_id], "verifyStatus": 1, "detail": "审核通过"})
        admin_client_for_setup.post("/product/update/publishStatus",
                                    params={"ids": [product_id], "publishStatus": 1})
        allure.attach(str(product_id), "Product ID", allure.attachment_type.TEXT)
        yield product_id

    with allure.step("Clean up test product"):
        try:
            admin_client_for_setup.post("/product/update/deleteStatus",
                                        params={"ids": [product_id], "deleteStatus": 1})
            db_assert = DBAssertion()
            db_assert.assert_not_exist("pms_product", "id = %s" % product_id)
        except Exception as e:
            allure.attach(str(e), "Cleanup failed", allure.attachment_type.TEXT)


@pytest.fixture
def test_brand(admin_client_for_setup, data_generator):
    brand_api = _bind_api(BrandApi, admin_client_for_setup)
    with allure.step("Create test brand"):
        brand_data = data_generator.brand_data()
        brand_name = brand_data["name"]
        _assert_create_ok(brand_api.create(brand_data), "brand")

        brand_id = IDFetcherWithAllure.get_id_by_module(
            api_instance=brand_api,
            module="brand",
            search_value=brand_name,
            page_size=10,
            max_pages=100
        )
        assert brand_id, f"Failed to create brand, brand ID not found: {brand_name}"

        allure.attach(str(brand_id), "Brand ID", allure.attachment_type.TEXT)
        yield brand_id

    with allure.step("Clean up test brand"):
        try:
            brand_api.delete(brand_id)
        except Exception as e:
            allure.attach(str(e), "Cleanup failed", allure.attachment_type.TEXT)


@pytest.fixture
def test_category(admin_client_for_setup, data_generator):
    category_api = _bind_api(CategoryApi, admin_client_for_setup)
    with allure.step("Create test category"):
        category_data = data_generator.product_category_data()
        category_name = category_data["name"]
        _assert_create_ok(category_api.create(category_data), "category")

        category_id = IDFetcherWithAllure.get_id_by_module(
            api_instance=category_api,
            module="category",
            search_value=category_name,
            page_size=100,
            max_pages=10,
            extra_params={"parent_id": 0}
        )
        assert category_id, f"Failed to create category, category ID not found: {category_name}"

        allure.attach(str(category_id), "Category ID", allure.attachment_type.TEXT)
        yield category_id

    with allure.step("Clean up test category"):
        try:
            category_api.delete(category_id)
        except Exception as e:
            allure.attach(str(e), "Cleanup failed", allure.attachment_type.TEXT)
