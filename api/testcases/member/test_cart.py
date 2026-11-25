# testcases/member/test_cart.py
import pytest
import allure

from common.assertions import ApiAssertion


@allure.feature("Cart Management")
class TestCart:

    def setup_method(self):
        self.api_assert = ApiAssertion()

    @allure.story("Cart List")
    def test_cart_list(self, cart_api):
        response = cart_api.list()
        print("Cart business status code", response.json())
        result = self.api_assert.assert_success(response, "Failed to get cart list")

        data = result.get("data", [])
        print(f"Business data returned when adding to cart: {data}")
        assert isinstance(data, list), "Cart data should be a list"

    @allure.story("Add to Cart")
    def test_add_to_cart(self, cart_api, test_product):
        data = {
            "productId": test_product,
            "productSkuId": 1,
            "quantity": 1,
            "price": 99.99
        }
        response = cart_api.add(data)
        self.api_assert.assert_success(response, "Failed to add to cart")

        list_response = cart_api.list()
        list_result = list_response.json()
        items = list_result.get("data", [])
        found = any(item.get("productId") == test_product for item in items)
        assert found, "Product was not added to the cart"

    @allure.story("Update Cart Quantity")
    def test_update_quantity(self, cart_api, test_cart_item):
        response = cart_api.update_quantity(test_cart_item, 3)
        self.api_assert.assert_success(response, "Failed to update quantity")

        list_response = cart_api.list()
        list_result = list_response.json()
        items = list_result.get("data", [])
        item = next((i for i in items if i.get("id") == test_cart_item), None)
        if item:
            assert item.get("quantity") == 3, "Quantity was not updated"

    @allure.story("Delete Cart Item")
    def test_delete_cart_item(self, cart_api, test_cart_item):
        response = cart_api.delete([test_cart_item])
        self.api_assert.assert_success(response, "Failed to delete cart item")

        list_response = cart_api.list()
        list_result = list_response.json()
        items = list_result.get("data", [])
        found = any(item.get("id") == test_cart_item for item in items)
        assert not found, "Cart item was not deleted"

    @allure.story("Clear Cart")
    def test_clear_cart(self, cart_api):
        response = cart_api.clear()
        print("Response of clearing the cart:", response)
        self.api_assert.assert_success(response, "Failed to clear cart")

        list_response = cart_api.list()
        list_result = list_response.json()
        items = list_result.get("data", [])
        assert len(items) == 0, "Cart was not cleared"

    @allure.story("Cart Promotion Info")
    def test_cart_promotion(self, cart_api, seed_cart_item):
        response = cart_api.list_promotion()
        result = self.api_assert.assert_success(response, "Failed to get promotion info")

        data = result.get("data", [])
        assert isinstance(data, list), "Promotion info should be a list"
        if data:
            item = data[0]
            self.api_assert.assert_field_exist(item, "promotionMessage", "Missing promotion info")
