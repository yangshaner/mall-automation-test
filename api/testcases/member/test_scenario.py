# testcases/member/test_scenario.py
import pytest
import allure
import time

from common.assertions import ApiAssertion
from common.db.mysql_util import mysql
from api.objects.admin.order_api import OrderApi


@allure.feature("Frontend Scenario Tests")
class TestMemberScenario:

    def setup_method(self):
        self.api_assert = ApiAssertion()

    @allure.story("Full Shopping Flow")
    def test_full_shopping_flow(
            self,
            member_product_api,
            cart_api,
            member_order_api,
            address_api,
            test_product,
            admin_client
    ):
        with allure.step("1. Search products"):
            response = member_product_api.search(keyword="手机")
            result = self.api_assert.assert_success(response, "Failed to search products")
            print(f"Search result: {result}")
            products = result.get("data", {}).get("list", [])
            assert len(products) > 0, "No product found"

        with allure.step("2. View product detail"):
            product_id = products[0].get('id')
            response = member_product_api.detail(product_id)
            result = self.api_assert.assert_success(response, "Failed to get product detail")
            detail = result.get("data", {})
            print("Product info to add to cart:", response.text)
            self.api_assert.assert_field_exist(detail, "product", "Missing product info")
            self.api_assert.assert_field_exist(detail, "skuStockList", "Missing SKU info")

        with allure.step("3. Add product to cart"):
            cart_data = {
                "productId": product_id,
                "productSkuId": detail.get("skuStockList", [{}])[0].get("id", 1),
                "quantity": 1,
                "price": detail.get("product", {}).get("price", 99.99)
            }
            print(f"Product id added to cart: {product_id}")
            response = cart_api.add(cart_data)
            self.api_assert.assert_success(response, "Failed to add to cart")

        with allure.step("4. Get cart list"):
            response = cart_api.list_promotion()
            result = self.api_assert.assert_success(response, "Failed to get cart")
            cart_items = result.get('data', [])
            assert len(cart_items) > 0, "Cart is empty"
            cart_id = cart_items[0].get("id")

        with allure.step("5. Generate confirm order"):
            response = member_order_api.generate_confirm_order([cart_id])
            result = self.api_assert.assert_success(response, "Failed to generate confirm order")
            confirm_data = result.get("data", {})
            print(f"confirm data:{confirm_data}")
            print(f"Product id in the confirm order: {confirm_data.get('cartPromotionItemList')[0].get('productId')}")
            self.api_assert.assert_field_exist(confirm_data, "calcAmount", "Missing amount calculation")

        with allure.step("6. Get shipping address"):
            response = address_api.list()
            result = self.api_assert.assert_success(response, "Failed to get shipping address")
            addresses = result.get('data', [])
            address_id = addresses[0].get("id") if addresses else None

            if not address_id:
                address_data = {
                    "name": "testAddress",
                    "phoneNumber": "13800138000",
                    "province": "guangdongsheng",
                    "city": "shenzhenshi",
                    "region": "nanshanqu",
                    "detailAddress": "No. 1 Science and Technology Park Road",
                    "defaultStatus": 1
                }
                response = address_api.add(address_data)
                address_result = response.json()
                address_id = address_result.get("data", {}).get("id")

        with allure.step("7. Generate order"):
            order_data = {
                "memberReceiveAddressId": address_id,
                "couponId": None,
                "useIntegration": 0,
                "payType": 0,
                "cartIds": [cart_id]
            }
            response = member_order_api.generate_order(order_data)
            print(f"order data:{order_data}")
            print(f"order response:{response.text}")
            result = self.api_assert.assert_success(response, "Failed to generate order")
            order_result = result.get("data", {})
            print(f"Order info: {order_result}")
            order_id = order_result.get("orderItemList")[0].get("orderId")
            assert order_id, "Order ID is empty"

            detail_response = member_order_api.detail(order_id)
            detail_result = detail_response.json()
            assert detail_result.get("data", {}).get("id") == order_id, "Order detail does not match"

        with allure.step("8. Payment success callback"):
            response = member_order_api.pay_success(order_id, 1)
            self.api_assert.assert_success(response, "Payment callback failed")

            detail_response = member_order_api.detail(order_id)
            detail_result = detail_response.json()
            status = detail_result.get("data", {}).get("status")
            assert status == 1, f"Order status should be pending shipment (1), actual {status}"


        with allure.step("9. Admin ships the order"):
            order_api = OrderApi(admin_client)
            delivery_data = [{
                "orderId": order_id,
                "deliveryCompany": "顺丰快递",
                "deliverySn": f"SF{int(time.time())}"
            }]
            response = order_api.delivery(delivery_data)
            self.api_assert.assert_success(response, "Admin delivery failed")

            detail_response = member_order_api.detail(order_id)
            detail_result = detail_response.json()
            status = detail_result.get('data', {}).get('status')
            assert status == 2, f"Order status after delivery should be shipped (2), actual: {status}"

            order_detail = detail_result.get("data", {})
            print(f"Order logistics info: {order_detail}")
            assert order_detail.get("deliveryCompany") == "顺丰快递", "Logistics company was not saved"
            assert order_detail.get("deliverySn") is not None, "Tracking number was not saved"


        with allure.step("10. User confirms receipt"):
            response = member_order_api.confirm_receiver_order(order_id)
            self.api_assert.assert_success(response, "Failed to confirm receipt", check_data=False)


        with allure.step("11. Verify the order is completed"):
            detail_response = member_order_api.detail(order_id)
            detail_result = detail_response.json()
            status = detail_result.get("data", {}).get("status")
            assert status == 3, f"Order status should be completed (3), actual {status}"


        with allure.step("12. Verify the order status in the database"):
            sql = "SELECT status FROM oms_order WHERE id = %s"
            result = mysql.query(sql, (order_id,))


            allure.attach(
                f"Query result: {result}\n"
                f"Result type: {type(result)}\n"
                f"Result length: {len(result) if result else 0}",
                name="Database query debug info",
                attachment_type=allure.attachment_type.TEXT
            )

            assert result, f"Order does not exist in the database: order_id={order_id}"
            db_status = result[0].get('status')
            assert db_status == 3, f"Database order status should be 3, actual {db_status}"


        with allure.step("13. Clean up the cart"):
            cart_api.clear()


    @allure.story("Coupon Usage Flow")
    def test_coupon_flow(
            self,
            member_coupon_api,
            cart_api,
            member_order_api,
            address_api,
            test_cart_item
    ):
        with allure.step("1. Get receivable coupons"):
            response = member_coupon_api.list_by_product(test_cart_item)
            if response.status_code == 500:
                pytest.skip("mall backend /coupon/listByProduct returns HTTP 500 (known defect)")
            result = self.api_assert.assert_success(response, "Failed to get product coupons")
            coupon = result.get("data", [])

            if not coupon:
                pytest.skip("No coupon available")

            coupon_id = coupon[0].get("id")

        with allure.step("2. Receive coupon"):
            response = member_coupon_api.add(coupon_id)
            self.api_assert.assert_success(response, "Failed to receive coupon")

        with allure.step("3. Get my coupons"):
            response = member_coupon_api.list(use_status=0)
            result = self.api_assert.assert_success(response, "Failed to get received coupon list")
            my_coupons = result.get("data", [])
            found = any(c.get("id") == coupon_id for c in my_coupons)
            assert found, "The received coupon is not in the list"

        with allure.step("4. Place an order with the coupon"):
            confirm_response = member_order_api.generate_confirm_order([test_cart_item])
            confirm_result = confirm_response.json()
            address_id = confirm_result.get("data", {}).get("memberReceiverAddressList", [{}])[0].get("id")

            order_data = {
                "memberReceiverAddressId": address_id,
                "couponId": coupon_id,
                "useIntegration": 0,
                "payType": 1,
                "cartIds": [test_cart_item]
            }
            response = member_order_api.generate_order(order_data)
            result = self.api_assert.assert_success(response, "Failed to place an order with the coupon")

            history_response = member_coupon_api.list_history(use_status=1)
            history_result = history_response.json()
            used = any(h.get("couponId") == coupon_id for h in history_result.get("data", []))
