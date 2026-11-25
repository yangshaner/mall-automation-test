# ui/pages/member_my.py
from __future__ import annotations

from playwright.sync_api import Locator, Page

from ui.pages.base_page import BasePage


class MemberMyPage(BasePage):

    PATH_HINT = "pages/user"

    def __init__(self, page: Page):
        super().__init__(page)
        self.tab_bar: Locator = page.locator(
            '.uni-tabs__nav, [class*="tab-bar"], [class*="TabBar"]'
        )
        self.bottom_tab_mine: Locator = page.get_by_text("我的", exact=True)
        self.add_address_btn: Locator = page.get_by_text("新增地址")
        self.fav_items: Locator = page.locator(
            '[class*="collect"], [class*="fav"], [class*="favorite"]'
        )

    def switch_tab(self, name: str) -> None:
        tab = self.page.get_by_text(name, exact=True)
        if tab.count() > 0:
            tab.click()
            self.wait_for_idle()

    def go_to_mine(self) -> None:
        self.bottom_tab_mine.click()
        self.wait_for_idle()

    def address_count(self) -> int:
        items = self.page.locator(
            '[class*="address"], .uni-list-item, [class*="Address"]'
        )
        return items.count()

    def has_address(self) -> bool:
        return self.address_count() > 0

    def fav_count(self) -> int:
        return self.fav_items.count()
