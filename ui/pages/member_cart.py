# ui/pages/member_cart.py
from __future__ import annotations

from playwright.sync_api import Locator, Page

from ui.pages.base_page import BasePage


class MemberCartPage(BasePage):

    PATH_HINT = "cart"

    def __init__(self, page: Page):
        super().__init__(page)
        self.cart_items: Locator = page.locator(
            '.cart-item, .cart-list-item, [class*="cart-item"], [class*="CartItem"]'
        )
        self.checkout_btn: Locator = page.get_by_text("去结算")
        self.clear_btn: Locator = page.get_by_text("清空购物车")

    def item_count(self) -> int:
        return self.cart_items.count()

    def is_empty(self) -> bool:
        if self.item_count() == 0:
            empty_hint = self.page.get_by_text("购物车是空的")
            if empty_hint.count() > 0:
                return True
            return True
        return False

    def total_price_text(self) -> str:
        try:
            el = self.page.locator('[class*="total"], [class*="Total"], [class*="price"]')
            return el.first.inner_text(timeout=3000).strip()
        except Exception:
            return ""

    def clear(self) -> str:
        self.clear_btn.click()
        try:
            confirm = self.page.get_by_role("button", name="确 定")
            if confirm.count() > 0:
                confirm.click()
        except Exception:
            pass
        return self.toast_text()
