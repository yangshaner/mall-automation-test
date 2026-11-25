# ui/pages/member_home.py
from __future__ import annotations

from playwright.sync_api import Locator, Page

from ui.pages.base_page import BasePage


class MemberHomePage(BasePage):

    def __init__(self, page: Page):
        super().__init__(page)
        self.search_input: Locator = page.locator('.uni-input-input[type="search"]')
        self.tab_labels = page.locator('.uni-tabbar__label')
        self.floor_items: Locator = page.locator(".floor-item")
        self.guess_items: Locator = page.locator(".guess-item")
        self.cate_items: Locator = page.locator(".cate-item")
        self.carousel_items: Locator = page.locator(".carousel-item")


    def _ensure_on_home(self) -> None:
        if "/#/" not in self.page.url or "/product" in self.page.url or \
           "/pages/user" in self.page.url or "/pages/cart" in self.page.url:
            self.page.goto(f"{self.page.url.split('#')[0]}#/", wait_until='networkidle', timeout=20000)
        else:
            self.page.reload(wait_until='networkidle', timeout=15000)
        self.wait_for_idle()
        self.dismiss_overlays()
        try:
            self.tab_labels.first.wait_for(state="visible", timeout=8000)
        except Exception:
            pass

    def _click_tab(self, tab_name: str) -> None:
        self._ensure_on_home()
        tab = self.tab_labels.filter(has_text=tab_name).first
        tab.wait_for(state="visible", timeout=8000)
        tab.click(force=False)
        self.wait_for_idle()

    def go_to_cart(self) -> None:
        self._click_tab("购物车")

    def go_to_mine(self) -> None:
        self._click_tab("我的")

    def go_to_category(self) -> None:
        self._click_tab("分类")


    def search(self, keyword: str) -> None:
        self.page.evaluate("""() => {
            const input = document.querySelector('.uni-input-input[type="search"]');
            if (input) {
                input.removeAttribute('disabled');
                input.focus();
            }
        }""")
        try:
            self.search_input.fill(keyword)
        except Exception:
            self.search_input.click(force=True)
            self.search_input.fill(keyword)
        self.search_input.press("Enter")
        self.wait_for_idle()


    def product_count(self) -> int:
        return self.guess_items.count() + self.floor_items.count()

    def guess_count(self) -> int:
        return self.guess_items.count()

    def floor_count(self) -> int:
        return self.floor_items.count()

    def category_count(self) -> int:
        return self.cate_items.count()

    def click_product(self, index: int = 0) -> None:
        if self.floor_items.count() > index:
            self.floor_items.nth(index).click()
        elif self.guess_items.count() > 0:
            self.guess_items.first.click()
        else:
            raise AssertionError("No clickable product cards on the home page")
        self.wait_for_url("product/product")
