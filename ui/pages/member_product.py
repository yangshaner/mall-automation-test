# ui/pages/member_product.py
from __future__ import annotations

from playwright.sync_api import Locator, Page

from ui.pages.base_page import BasePage


class MemberProductPage(BasePage):

    def __init__(self, page: Page):
        super().__init__(page)
        self.product_name: Locator = page.locator(
            'h1, h2, [class*="name"], [class*="title"], .uni-text'
        )
        self.price: Locator = page.locator(
            '[class*="price"], .uni-price'
        )
        self.add_to_cart_btn: Locator = page.get_by_role("button", name="加入购物车")
        self.buy_now_btn: Locator = page.get_by_role("button", name="立即购买")


    def product_name_text(self) -> str:
        try:
            first = self.product_name.first
            first.wait_for(state="visible", timeout=8000)
            return first.inner_text().strip()
        except Exception:
            return ""

    def price_text(self) -> str:
        try:
            return self.price.first.inner_text(timeout=5000).strip()
        except Exception:
            return ""


    def add_to_cart(self, quantity: int = 1) -> str:
        btn = self.page.locator('.add-cart-btn')
        btn.wait_for(state="visible", timeout=10000)
        btn.click()
        try:
            return self.toast_text()
        except Exception:
            return ""

    def buy_now(self) -> str:
        btn = self.page.locator('.buy-now-btn')
        btn.wait_for(state="visible", timeout=10000)
        btn.click()
        try:
            return self.toast_text()
        except Exception:
            return ""
