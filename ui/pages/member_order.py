# ui/pages/member_order.py
from __future__ import annotations

from playwright.sync_api import Locator, Page

from ui.pages.base_page import BasePage


class MemberOrderConfirmPage(BasePage):

    PATH_HINT = "confirm"

    def __init__(self, page: Page):
        super().__init__(page)
        self.submit_btn: Locator = page.get_by_text("提交订单")
        self.address_block: Locator = page.locator(
            '[class*="address"], .delivery-address'
        )

    def has_address(self) -> bool:
        return self.address_block.count() > 0

    def submit(self) -> str:
        self.submit_btn.click()
        try:
            self.page.wait_for_url("order", timeout=8000)
            return "Order placed successfully"
        except Exception:
            return self.toast_text() or ""


class MemberOrderListPage(BasePage):

    PATH_HINT = "order"

    def __init__(self, page: Page):
        super().__init__(page)
        self.order_cards: Locator = page.locator(
            '.order-item, .order-card, [class*="order"], [class*="Order"]'
        )

    def order_count(self) -> int:
        return self.order_cards.count()

    def has_order(self) -> bool:
        return self.order_count() > 0

    def filter_by_status(self, status: str) -> None:
        tab = self.page.get_by_text(status, exact=True)
        if tab.count() > 0:
            tab.click()
            self.wait_for_idle()

    def cancel_first_order(self) -> str:
        cancel = self.page.get_by_text("取消订单")
        if cancel.count() == 0:
            return "No cancel button"
        cancel.first.click()
        try:
            confirm = self.page.get_by_role("button", name="确 定")
            if confirm.count() > 0:
                confirm.click()
        except Exception:
            pass
        return self.toast_text() or ""
