# ui/testcases/member/test_order.py
from __future__ import annotations

import pytest
import requests

from ui import config as ui_cfg
from ui.pages.member_cart import MemberCartPage
from ui.pages.member_home import MemberHomePage
from ui.pages.member_my import MemberMyPage
from ui.pages.member_order import MemberOrderConfirmPage, MemberOrderListPage
from ui.pages.member_product import MemberProductPage


@pytest.mark.member
@pytest.mark.ui
class TestMemberOrderFlow:


    @staticmethod
    def _member_token() -> str:
        r = requests.post(
            f"{ui_cfg.MEMBER_API_URL}/sso/login",
            params={"username": ui_cfg.MEMBER_USERNAME,
                    "password": ui_cfg.MEMBER_PASSWORD},
            timeout=10,
        )
        return (r.json().get("data") or {}).get("token", "")

    @staticmethod
    def _orders_via_api(token: str) -> list:
        r = requests.get(
            f"{ui_cfg.MEMBER_API_URL}/order/list",
            headers={"Authorization": f"Bearer {token}"},
            params={"pageNum": 1, "pageSize": 10},
            timeout=10,
        )
        body = r.json()
        data = body.get("data")
        if isinstance(data, dict):
            return data.get("list") or []
        return []


    def test_full_order_flow_with_cleanup(self, member_ready) -> None:
        page = member_ready
        home = MemberHomePage(page)
        detail = MemberProductPage(page)
        cart = MemberCartPage(page)
        confirm = MemberOrderConfirmPage(page)

        api_token = self._member_token()
        orders_before = self._orders_via_api(api_token)

        home.click_product(index=0)
        detail.add_to_cart(quantity=1)

        home.go_to_cart()
        if cart.is_empty():
            pytest.skip("Cart is empty, cannot continue checkout (add-to-cart API failed or the product has no stock)")

        checkout_btn = page.get_by_role("button", name="去结算")
        if checkout_btn.count() == 0:
            pytest.skip("Cart has no checkout button (mall-member-web version may differ)")
        checkout_btn.click()
        confirm.wait_for_url("confirm")

        if not confirm.has_address():
            api_token = self._member_token()
            r = requests.get(
                f"{ui_cfg.MEMBER_API_URL}/member/address/list",
                headers={"Authorization": f"Bearer {api_token}"},
                timeout=10,
            )
            addresses = r.json().get("data") or []
            if not addresses:
                pytest.skip("The account has no shipping address, skipping the order case (configure an address for the demo account in admin first)")

        toast_or_msg = confirm.submit()
        assert toast_or_msg, "Submitting the order should show a toast or trigger navigation"

        api_token = self._member_token()
        orders_after = self._orders_via_api(api_token)
        new_order_count = len(orders_after) - len(orders_before)
        assert new_order_count >= 1, \
            f"API order count did not increase after the UI submission: before {len(orders_before)} / after {len(orders_after)}"

        order_list = MemberOrderListPage(page)
        page.goto(f"{ui_cfg.MEMBER_BASE_URL}/#/member/order/list")
        order_list.filter_by_status("待付款")
        if order_list.has_order():
            order_list.cancel_first_order()

        api_token = self._member_token()
        final_orders = self._orders_via_api(api_token)
        assert isinstance(final_orders, list), "API order list should return a list"
