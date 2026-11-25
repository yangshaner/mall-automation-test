# testcases/member/test_coupon.py
import pytest
import allure

from common.assertions import ApiAssertion


@allure.feature("Member Coupons")
class TestMemberCoupon:

    def setup_method(self):
        self.api_assert = ApiAssertion()

    @allure.story("Coupon List")
    @pytest.mark.parametrize("use_status", [0, 1, 2])
    def test_coupon_list_by_status(self, member_coupon_api, use_status):
        response = member_coupon_api.list(use_status=use_status)
        self.api_assert.assert_list_response(
            response,
            message=f"Failed to get coupon list (useStatus={use_status})"
        )

    @allure.story("Coupon History List")
    def test_coupon_history_list(self, member_coupon_api):
        response = member_coupon_api.list_history()
        self.api_assert.assert_list_response(
            response,
            message="Failed to get coupon history list"
        )

    @allure.story("Product Related Coupons")
    def test_coupon_list_by_product(self, member_coupon_api, test_product):
        response = member_coupon_api.list_by_product(test_product)
        self.api_assert.assert_list_response(
            response,
            message="Failed to get product related coupons"
        )

    @allure.story("Cart Related Coupons")
    @pytest.mark.parametrize("coupon_type", [0, 1])
    def test_coupon_list_by_cart(self, member_coupon_api, coupon_type):
        response = member_coupon_api.list_cart(coupon_type)
        self.api_assert.assert_list_response(
            response,
            message=f"Failed to get cart coupons (type={coupon_type})"
        )

    @allure.story("Receive Coupon")
    def test_receive_coupon(self, member_coupon_api, test_product):
        product_coupon_response = member_coupon_api.list_by_product(test_product)
        product_coupons = product_coupon_response.json().get("data", [])
        if not product_coupons:
            pytest.skip("No receivable coupon for the current product")

        coupon_id = product_coupons[0].get("id")
        assert coupon_id, "Coupon data is missing id"

        response = member_coupon_api.add(coupon_id)
        result = response.json()

        if result.get("code") != 200:
            message = result.get("message", "")
            if "已经" in message or "重复" in message or "exist" in message.lower():
                pytest.skip(f"Coupon has already been received: {message}")
        self.api_assert.assert_success(response, "Failed to receive coupon", check_data=False)

    @allure.story("Receive Coupon")
    def test_receive_nonexistent_coupon(self, member_coupon_api):
        response = member_coupon_api.add(999999999)
        result = response.json()
        assert result.get("code") != 200, "A nonexistent coupon should not be received successfully"
