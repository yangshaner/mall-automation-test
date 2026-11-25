# testcases/member/test_order.py
import pytest
import allure

from common.assertions import ApiAssertion


@allure.feature("Frontend Order Management")
class TestMemberOrder:

    def setup_method(self):
        self.api_assert = ApiAssertion()

    @allure.story("Order List")
    @pytest.mark.parametrize("status", [-1, 0, 1, 2, 3, 4])
    def test_order_list_by_status(self, member_order_api, status):
        status_names = {-1: "All", 0: "Pending Payment", 1: "Pending Shipment",
                        2: "Shipped", 3: "Completed", 4: "Closed"}

        response = member_order_api.list(status=status)

        page_data = self.api_assert.assert_page_response(
            response,
            message=f"Failed to get {status_names.get(status)} orders",
            allow_empty_list=True,
            soft=False
        )

        if status != -1:
            for order in page_data.get("list", []):
                assert order.get("status") == status, f"Order status should be {status}"

    @allure.story("Order Detail")
    def test_order_detail(self, member_order_api):
        response = member_order_api.list(status=-1, page_size=1)
        list_result = response.json()
        orders = list_result.get("data", {}).get("list", [])

        if not orders:
            pytest.skip("No order available")

        order_id = orders[0].get("id")
        response = member_order_api.detail(order_id)
        result = self.api_assert.assert_success(response, "Failed to get order detail")

        data = result.get("data", {})
        self.api_assert.assert_field_exist(data, "orderSn", "Missing order number")
        self.api_assert.assert_field_exist(data, "orderItemList", "Missing order item list")
        self.api_assert.assert_field_exist(data, "status", "Missing order status")

    @allure.story("Generate Confirm Order")
    def test_generate_confirm_order(self, member_order_api, seed_cart_item):
        response = member_order_api.generate_confirm_order([seed_cart_item])
        result = self.api_assert.assert_success(response, "Failed to generate confirm order")

        data = result.get("data", {})
        print(f"Generate confirm order result: {result}")
        self.api_assert.assert_field_exist(data, "cartPromotionItemList", "Missing cart info")
        self.api_assert.assert_field_exist(data, "memberReceiveAddressList",
                                           "Missing shipping address")
        self.api_assert.assert_field_exist(data, "calcAmount", "Missing amount calculation")

    @allure.story("Cancel Order")
    def test_cancel_order(self, member_order_api):
        list_response = member_order_api.list(status=0, page_size=1)
        list_result = list_response.json()
        orders = list_result.get("data", {}).get("list", [])

        if not orders:
            pytest.skip("No pending-payment order")

        order_id = orders[0].get("id")
        response = member_order_api.cancel_user_order(order_id)
        print(f"Pending payment order response: {response}")
        self.api_assert.assert_success(response, "Failed to cancel order")

    @allure.story("Confirm Order")
    def test_confirm_order(self, member_order_api):
        list_response = member_order_api.list(status=2, page_size=1)
        list_result = list_response.json()
        orders = list_result.get("data", {}).get("list", [])

        if not orders:
            pytest.skip("No shipped order")

        order_id = orders[0].get("id")
        response = member_order_api.confirm_receiver_order(order_id)
        self.api_assert.assert_success(response, "Failed to confirm receipt", check_data=False)
