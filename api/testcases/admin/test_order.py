# testcases/admin/tets_order.py
import pytest
import allure
import time
from common.assertions import ApiAssertion, DBAssertion


@allure.feature("Order Management")
class TestOrder:

    def setup_method(self):
        self.api_assert = ApiAssertion()
        self.db_assert = DBAssertion()

    @allure.story("Order List")
    def test_get_order_list(self, order_api):
        response = order_api.list(page_num=1, page_size=10)
        result = self.api_assert.assert_success(response, "Failed to get order list")
        data = result.get("data", {})
        self.api_assert.assert_field_exist(data, 'list', "missing list")
        self.api_assert.assert_field_exist(data, "total", "missing total")

    @allure.story("Order List")
    @pytest.mark.parametrize("status, status_name", [
        (0, "Pending payment"),
        (1, "Pending shipment"),
        (2, "Shipped"),
        (3, "Completed"),
        (4, "Closed")
    ])
    def test_get_order_list_by_status(self, order_api, status, status_name: str):
        status_name = {0: "Pending payment", 1: "Pending shipment", 2: "Shipped", 3: "Completed", 4: "Closed"}
        response = order_api.list(page_num=1, page_size=10, status=status)
        self.api_assert.assert_success(response, f"Failed to query by status {status}")
        data = response.json().get("data", {})
        for order in data.get('list', []):
            assert order.get("status") == status, f"Order status should be {status}: {status_name}"

    @allure.story("Order List")
    def test_get_order_list_with_order_sn(self, order_api):
        list_resp = order_api.list(page_num=1, page_size=1)
        orders = list_resp.json().get('data', {}).get('list', [])
        if not orders:
            pytest.skip("No order available")
        order_sn = orders[0].get('orderSn')

        response = order_api.list(page_num=1, page_size=1, order_sn=order_sn)
        result = self.api_assert.assert_success(response, "Failed to query by order number")
        data = result.get('data', {})
        for order in data.get('list', []):
            assert order.get('orderSn') == order_sn, "Order number mismatch"

    @allure.story("Order Detail")
    def test_get_order_detail(self, order_api):
        list_resp = order_api.list(page_num=1, page_size=1)
        orders = list_resp.json().get("data", {}).get("list", [])
        if not orders:
            pytest.skip("No order available")

        order_id = orders[0].get("id")
        response = order_api.detail(order_id)
        result = self.api_assert.assert_success(response, "Failed to get order detail")
        data = result.get("data", {})
        self.api_assert.assert_field_exist(data, "orderSn", "missing order number")
        self.api_assert.assert_field_exist(data, "orderItemList", "missing order items")
        self.api_assert.assert_field_exist(data, "status", "missing order status")
        self.api_assert.assert_field_exist(data, "totalAmount", "missing total amount")
        assert isinstance(data.get('orderItemList'), list), "Order items should be an array"

    @allure.story("Order Note")
    def test_update_order_note(self, order_api):
        list_resp = order_api.list(page_num=1, page_size=1, status=0)
        orders = list_resp.json().get("data", {}).get("list", [])
        if not orders:
            pytest.skip("No pending-payment order available")

        order_id = orders[0].get("id")
        note = f"testNotes_{int(time.time())}"
        response = order_api.update_note(order_id, note, 0)
        self.api_assert.assert_success(response, "Failed to update order note")
        self.db_assert.assert_field_value('oms_order', 'note', note,
                                          'id = %s', (order_id,))

    @allure.story("Batch Delivery")
    def test_delivery(self, order_api):
        list_resp = order_api.list(page_num=1, page_size=1, status=1)
        orders = list_resp.json().get("data", {}).get("list", [])
        if not orders:
            pytest.skip("No pending-shipment order available")
        order_id = orders[0].get("id")
        delivery_sn = f"SF{int(time.time())}"
        delivery_data = [{
            'orderId': order_id,
            "deliveryCompany": "顺丰快递",
            "deliverySn": delivery_sn
        }]
        response = order_api.delivery(delivery_data)
        self.api_assert.assert_success(response, "Delivery failed")
        self.db_assert.assert_field_value('oms_order', 'status', 2,
                                          'id = %s', (order_id,))
        self.db_assert.assert_field_value('oms_order', 'delivery_company', '顺丰快递',
                                          'id = %s', (order_id,))
        self.db_assert.assert_field_value('oms_order', 'delivery_sn', delivery_sn,
                                          'id = %s', (order_id,))

    @allure.story("Update Receiver Info")
    def test_update_receiver_info(self, order_api):
        list_resp = order_api.list(page_num=1, page_size=1)
        orders = list_resp.json().get("data", {}).get("list", [])
        if not orders:
            pytest.skip("No order available")

        order_id = orders[0].get("id")
        data = {
            "orderId": order_id,
            "receiverName": f"testRecipient_{int(time.time())}",
            "receiverPhone": "13800138000",
            "receiverProvince": "guangdongsheng",
            "receiverCity": "shenzhenshi",
            "receiverRegion": "nanshanqu",
            "receiverDetailAddress": "No.1,Science Park Road",
            "status": orders[0].get('status')
        }
        response = order_api.update_receiver_info(data)
        self.api_assert.assert_success(response, "Failed to update receiver info")

        self.db_assert.assert_field_value('oms_order', 'receiver_name', data['receiverName'],
                                          'id = %s', (order_id,))

    @allure.story("Batch Close Orders")
    def test_batch_close_orders(self, order_api):
        list_resp = order_api.list(page_num=1, page_size=2, status=0)
        orders = list_resp.json().get("data", {}).get("list", [])
        if len(orders) < 1:
            pytest.skip("No pending-payment order available")

        order_ids = [o.get("id") for o in orders[:2]]
        response = order_api.close(order_ids, "test closed")
        self.api_assert.assert_success(response, "Failed to close orders")

        for oid in order_ids:
            self.db_assert.assert_field_value('oms_order', 'status', 4,
                                              'id = %s', (oid,))

    @allure.story("Batch Delete Orders")
    def text_batch_delete_orders(self, order_api):
        list_resp = order_api.list(page_num=1, page_size=2, status=4)
        orders = list_resp.json().get("data", {}).get("list", [])
        if len(orders) < 1:
            pytest.skip("No deletable order available")

        order_ids = [o.get("id") for o in orders[:2]]
        response = order_api.delete(order_ids)
        self.api_assert.assert_success(response, "Failed to delete orders")

        for oid in order_ids:
            self.db_assert.assert_field_value('oms_order', 'delete_status', 1,
                                              'id = %s', (oid,))
