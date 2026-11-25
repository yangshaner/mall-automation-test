import pytest
import allure

from common.assertions import ApiAssertion


@allure.feature("Frontend Order - Idempotency and Duplicate Prevention")
class TestOrderIdempotent:

    def setup_method(self):
        self.aa = ApiAssertion()

    @allure.story("List boundary: pageSize = 0")
    def test_order_list_page_size_zero(self, member_order_api):
        resp = member_order_api.list(status=-1, page_size=0)
        assert resp.status_code in (200, 400, 422)

    @allure.story("List boundary: oversized pageSize (10000)")
    def test_order_list_page_size_overflow(self, member_order_api):
        resp = member_order_api.list(status=-1, page_size=10000)
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body.get("data", {}), dict)

    @allure.story("List boundary: negative page number")
    def test_order_list_page_negative(self, member_order_api):
        resp = member_order_api.list(status=-1, page_num=-1)
        assert resp.status_code in (200, 400, 422)

    @allure.story("List boundary: page number 0")
    def test_order_list_page_zero(self, member_order_api):
        resp = member_order_api.list(status=-1, page_num=0)
        assert resp.status_code in (200, 400, 422)

    @allure.story("Detail exception: nonexistent order ID - mall backend defect (silently returns empty list)")
    def test_order_detail_nonexistent(self, member_order_api):
        resp = member_order_api.detail(99999)
        body = resp.json()
        assert body.get("code", 200) != 200, \
            (f"BUG: detail of a nonexistent order should return 404, "
             f"but mall returned code={body.get('code')} data.orderItemList=[]")

    @allure.story("Cancel exception: nonexistent order - mall backend defect (silently returns success)")
    def test_cancel_nonexistent_order(self, member_order_api):
        resp = member_order_api.cancel_user_order(99999)
        body = resp.json()
        assert body.get("code", 200) != 200, \
            (f"BUG: cancelling a nonexistent order should return 404, "
             f"but mall returned code={body.get('code')} message={body.get('message')}")

    @allure.story("Cancel idempotency: cancelling an already cancelled order should not fail")
    def test_cancel_already_cancelled(self, member_order_api):
        list_resp = member_order_api.list(status=4, page_size=1)
        orders = list_resp.json().get("data", {}).get("list", [])
        if not orders:
            pytest.skip("No closed order available for the idempotency test")
        order_id = orders[0].get("id")
        resp = member_order_api.cancel_user_order(order_id)
        assert resp.status_code in (200, 400, 422)

    @allure.story("Confirm receipt exception: an unshipped order cannot be confirmed")
    def test_confirm_undelivered_order(self, member_order_api):
        list_resp = member_order_api.list(status=0, page_size=1)
        orders = list_resp.json().get("data", {}).get("list", [])
        if not orders:
            pytest.skip("No pending-payment order available for the confirm receipt exception test")
        order_id = orders[0].get("id")
        resp = member_order_api.confirm_receiver_order(order_id)
        body = resp.json() if resp.status_code == 200 else {}
        assert body.get("code", 200) != 200 or resp.status_code != 200
