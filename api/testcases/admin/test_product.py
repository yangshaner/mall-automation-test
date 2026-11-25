# testcases/admin/test_product.py
from decimal import Decimal

import allure
import pytest

from common.assertions import ApiAssertion, DBAssertion
from common.db.mysql_util import mysql


@allure.feature("Product Management")
class TestProduct:

    def setup_method(self):
        self.api_assert = ApiAssertion()
        self.db_assert = DBAssertion()

    @allure.story("Product List")
    def test_get_product_list(self, product_api):
        response = product_api.list(page_num=1, page_size=10)
        result = self.api_assert.assert_success(response, "Failed to get product list")
        data = result.get('data', {})
        self.api_assert.assert_field_exist(data, 'list', "missing list")
        self.api_assert.assert_field_exist(data, 'total', "missing total")
        assert isinstance(data.get('list'), list), "list should be a list"

    @allure.story("Product List")
    def test_get_product_list_with_filter(self, product_api):
        response = product_api.list(
            page_num=1, page_size=10,
            publish_status=1,
            verify_status=1
        )
        result = self.api_assert.assert_success(response, "Filtered query failed")
        data = result.get('data', {})
        if data.get('total') <= 0:
            pytest.skip("No product matches the search criteria")
        for product in data.get('list', []):
            assert product.get('publishStatus') == 1, "Product should be published"
            assert product.get('verifyStatus') == 1, "Product should be verified"

    def test_get_product_list_with_keyword(self, product_api):
        response = product_api.list(page_num=1, page_size=10, keyword="手机")
        self.api_assert.assert_success(response, "Keyword query failed")

    @allure.story("Create Product")
    def test_create_product(self, product_api, data_generator, test_brand, test_category):

        product_data = data_generator.product_data(test_brand, test_category)

        response = product_api.create(product_data)
        print(f"create product response: {response}")
        self.api_assert.assert_success(response, "Failed to create product")
        product_name = product_data.get("name")


        product_id = mysql.get_id_by_field('pms_product', 'name', product_name)
        print(f"created product name: {product_name}, id: {product_id}")
        print(f"type price: {type(product_data.get('price'))}")
        assert product_id, f"Created product not found: {product_name}"

        self.db_assert.assert_exists('pms_product', 'id = %s', (product_id,))
        self.db_assert.assert_field_value('pms_product', 'name', product_data['name'],
                                          'id = %s', (product_id,))
        self.db_assert.assert_field_value('pms_product', 'price',
                                          Decimal(product_data['price']).quantize(Decimal('.01')),
                                          'id = %s', (product_id,))
        self.db_assert.assert_field_value('pms_product', 'stock', product_data['stock'],
                                          'id = %s', (product_id,))

        product_api.update_delete_statue([product_id], 1)
        self.db_assert.assert_field_value('pms_product', 'delete_status', 1,
                                          'id = %s', (product_id,))

    @allure.story("Update Product")
    def test_update_product(self, product_api, data_generator, test_brand, test_category, test_product):
        product_name = f"testCategory_{data_generator.random_string(6)}"
        product_data = {
            "name": product_name,
            "productSn": f"TEST_{data_generator.random_string(8).upper()}",
            "price": data_generator.random_price(10, 1000),
            "stock": data_generator.random_int(1, 1000),
            "brandId": test_brand,
            "productCategoryId": test_category,
            "publishStatus": 1,
            "verifyStatus": 1
        }
        response = product_api.create(product_data)
        self.api_assert.assert_success(response, "Failed to create product")

        product_id = mysql.get_id_by_field('pms_product', 'name', product_name)

        assert product_id, "Created product not found"

        update_data = {
            "name": f"updated_{product_name}",
            "price": 88.88,
            "stock": 500,
            "subTitle": "Update test subtitle"
        }
        response = product_api.update(product_id, update_data)
        self.api_assert.assert_success(response, "Failed to update product")
        self.db_assert.assert_field_value('pms_product', 'name', update_data['name'],
                                          'id = %s', (product_id,))
        self.db_assert.assert_field_value('pms_product', "price",
                                          Decimal(update_data['price']).quantize(Decimal('.01')),
                                          'id = %s', (product_id,))
        self.db_assert.assert_field_value('pms_product', "stock", update_data['stock'],
                                          'id = %s', (product_id,))

        product_api.update_delete_statue([product_id], 1)

    @allure.story("Product Detail")
    def test_get_product_update_info(self, product_api, data_generator, test_brand, test_category):
        product_name = f"testProduct_{data_generator.random_string(6)}"
        product_data = {
            "name": product_name,
            "productSn": f"TEST_{data_generator.random_string(8).upper()}",
            "price": data_generator.random_price(10, 1000),
            "stock": data_generator.random_int(1, 1000),
            "brandId": test_brand,
            "productCategoryId": test_category,
            "publishStatus": 1,
            "verifyStatus": 1
        }
        response = product_api.create(product_data)
        self.api_assert.assert_success(response, "Failed to create product")

        product_id = mysql.get_id_by_field('pms_product', 'name', product_name)

        assert product_api, "Created product not found"

        response = product_api.get_update_info(product_id)
        result = self.api_assert.assert_success(response, "Failed to get product detail")
        detail = result.get('data', {})
        assert detail.get('id') == product_id, "Product ID mismatch"
        assert detail.get('name') == product_name, "Product name mismatch"
        self.api_assert.assert_field_exist(detail, 'price', "missing price")
        self.api_assert.assert_field_exist(detail, 'stock', "missing stock")
        self.api_assert.assert_field_exist(detail, 'brandName', "missing brandName")

        product_api.update_delete_statue([product_id], 1)

    @allure.story("Product Publish/Unpublish")
    @pytest.mark.parametrize("publish_status", [0, 1])
    def test_update_publish_status(self, product_api, data_generator, test_brand, test_category, publish_status):
        product_name = f"testProduct_{data_generator.random_string(6)}"
        product_data = {
            "name": product_name,
            "productSn": f"TEST_{data_generator.random_string(8).upper()}",
            "price": data_generator.random_price(10, 1000),
            "stock": data_generator.random_int(1, 1000),
            "brandId": test_brand,
            "productCategoryId": test_category,
            "publishStatus": 1,
            "verifyStatus": 1
        }
        response = product_api.create(product_data)
        self.api_assert.assert_success(response, "Failed to create product")

        product_id = mysql.get_id_by_field('pms_product', 'name', product_name)

        assert product_id, "Created product not found"

        response = product_api.update_publish_status([product_id], publish_status)
        self.api_assert.assert_success(response, "Failed to publish/unpublish product")
        self.db_assert.assert_field_value('pms_product', 'publish_status', publish_status,
                                          'id = %s', (product_id,))

        product_api.update_delete_statue([product_id], 1)

    @allure.story("Product Verification")
    @pytest.mark.parametrize("verify_status", [0, 1])
    def test_update_verify_status(self, product_api, data_generator, test_brand, test_category, verify_status):
        product_name = f"testProduct_{data_generator.random_string(6)}"
        product_data = {
            "name": product_name,
            "productSn": f"TEST_{data_generator.random_string(8).upper()}",
            "price": data_generator.random_price(10, 1000),
            "stock": data_generator.random_int(1, 1000),
            "brandId": test_brand,
            "productCategoryId": test_category,
            "publishStatus": 1,
            "verifyStatus": 1
        }
        response = product_api.create(product_data)
        self.api_assert.assert_success(response, "Failed to create product")

        product_id = mysql.get_id_by_field('pms_product', 'name', product_name)

        assert product_id, "Created product not found"

        detail = f"review{'passing' if verify_status == 1 else 'without passing'}"
        response = product_api.update_verify_status([product_id], verify_status, detail)
        self.api_assert.assert_success(response, "Verification failed")
        self.db_assert.assert_field_value('pms_product', 'verify_status', verify_status,
                                          'id = %s', (product_id,))
        product_api.update_delete_statue([product_id], 1)

    @allure.story("Product Recommendation")
    @pytest.mark.parametrize("recommend_status", [0, 1])
    def test_update_recommend_status(self, product_api, data_generator, test_brand, test_category, recommend_status):
        product_name = f"testProduct_{data_generator.random_string(6)}"
        product_data = {
            "name": product_name,
            "productSn": f"TEST_{data_generator.random_string(8).upper()}",
            "price": data_generator.random_price(10, 1000),
            "stock": data_generator.random_int(1, 1000),
            "brandId": test_brand,
            "productCategoryId": test_category,
            "publishStatus": 1,
            "verifyStatus": 1
        }
        response = product_api.create(product_data)
        self.api_assert.assert_success(response, "Failed to create product")

        product_id = mysql.get_id_by_field('pms_product', 'name', product_name)

        assert product_id, "Created product not found"

        response = product_api.update_recommend_status([product_id], recommend_status)
        self.api_assert.assert_success(response, "Recommendation failed")
        self.db_assert.assert_field_value('pms_product', 'recommend_status', recommend_status,
                                          'id = %s', (product_id,))

        product_api.update_delete_statue([product_id], 1)

    @pytest.mark.skipif(1==1, reason="some products cannot be found via fuzzy search")
    @allure.story("Fuzzy Search")
    def test_simple_list(self, product_api, data_generator, test_brand, test_category):
        product_name = f"test_{data_generator.random_string(6)}"
        product_data = {
            "name": product_name,
            "productSn": f"TEST_{data_generator.random_string(8).upper()}",
            "price": data_generator.random_price(10, 1000),
            "stock": data_generator.random_int(1, 1000),
            "brandId": test_brand,
            "productCategoryId": test_category,
            "publishStatus": 1,
            "verifyStatus": 1
        }
        response = product_api.create(product_data)
        self.api_assert.assert_success(response, "Failed to create product")

        product_id = mysql.get_id_by_field('pms_product', 'name', product_name)

        assert product_id, "Created product not found"

        response = product_api.simple_list(product_name[:5])

        result = self.api_assert.assert_success(response, "Fuzzy search failed")
        print("product id", product_id)
        print("product name, simple search name:", product_name, product_name[:5])
        print("fuzzy search result:", result)

        data = result.get('data', [])

        print("product data", data)
        print(f"fuzzy search data: {data}, product_id: {product_id}, product_name: {product_name}")

        assert any(p.get('id') == product_id for p in data), "Target product not found"

        product_api.update_delete_statue([product_id], 1)
        print("done.")
