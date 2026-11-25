# testcases/member/test_collection.py
import pytest
import allure
import requests

from common.assertions import ApiAssertion


@allure.feature("Member Product Collection")
class TestCollection:

    def setup_method(self):
        self.api_assert = ApiAssertion()

    @pytest.fixture(autouse=True)
    def _skip_if_collection_unavailable(self, collection_available):
        if not collection_available:
            pytest.skip("Collection API unavailable (server timeout / missing collection table), "
                        "skipping collection tests")

    @allure.story("Collection List")
    def test_collection_list(self, collection_api, test_collection):
        response = collection_api.list(page_num=1, page_size=10)
        page_data = self.api_assert.assert_page_response(
            response,
            message="Failed to get collection list",
            allow_empty_list=True
        )

        product_list = page_data.get("list", [])
        assert len(product_list) > 0, "Collection was created but the collection list is empty"

    @allure.story("Add Collection")
    def test_add_collection(self, collection_api, test_product, data_generator):
        data = {
            "productId": test_product,
            "productName": f"testProduct_{data_generator.random_string(4)}",
            "productPic": "test.png",
            "productPrice": "99.99"
        }
        try:
            response = collection_api.add(data)
            self.api_assert.assert_success(response, "Failed to add product collection", check_data=False)

            list_response = collection_api.list(page_num=1, page_size=50)
            list_result = list_response.json()
            items = list_result.get("data", {}).get("list", [])
            assert any(item.get("productId") == test_product for item in items), \
                "Product does not appear in the collection list after being collected"
        finally:
            collection_api.delete(test_product)

    @allure.story("Collection Detail")
    def test_collection_detail(self, collection_api, test_product):
        try:
            response = collection_api.detail(test_product)
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Collection detail request error: {type(e).__name__}")

        if response.status_code in (404, 405):
            allure.attach(response.text[:300], "Collection detail endpoint does not exist", allure.attachment_type.TEXT)
            pytest.skip(f"The current backend version does not provide the collection detail "
                        f"endpoint (HTTP {response.status_code})")

        self.api_assert.assert_success(response, "Failed to get collection product detail", check_data=False)

    @allure.story("Delete Collection")
    def test_delete_collection(self, collection_api, test_product, data_generator):
        data = {
            "productId": test_product,
            "productName": f"testProduct_{data_generator.random_string(4)}",
            "productPic": "test.png",
            "productPrice": "99.99"
        }
        add_response = collection_api.add(data)
        self.api_assert.assert_success(add_response, "Failed to add collection as precondition",
                                       check_data=False)

        response = collection_api.delete(test_product)
        self.api_assert.assert_success(response, "Failed to delete product collection", check_data=False)

        list_response = collection_api.list(page_num=1, page_size=50)
        list_result = list_response.json()
        items = list_result.get("data", {}).get("list", [])
        assert not any(item.get("productId") == test_product for item in items), \
            "Product collection was not deleted"

    @allure.story("Clear Collection")
    def test_clear_collection(self, collection_api, test_product, data_generator):
        data = {
            "productId": test_product,
            "productName": f"testProduct_{data_generator.random_string(4)}",
            "productPic": "test.png",
            "productPrice": "99.99"
        }
        collection_api.add(data)

        response = collection_api.clear()
        self.api_assert.assert_success(response, "Failed to clear product collections", check_data=False)

        list_response = collection_api.list(page_num=1, page_size=50)
        list_result = list_response.json()
        items = list_result.get("data", {}).get("list", [])
        assert len(items) == 0, "Product collection list was not cleared"
