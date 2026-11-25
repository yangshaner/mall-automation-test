# ui/pages/admin_dashboard.py
from __future__ import annotations

from playwright.sync_api import Locator, Page

from ui.pages.base_page import BasePage


class AdminDashboardPage(BasePage):

    def __init__(self, page: Page):
        super().__init__(page)
        self.sidebar = self.page.locator("aside .el-menu")


    def navigate_to(self, menu_item_text: str) -> None:
        menu_item = self.sidebar.get_by_text(menu_item_text, exact=True).first
        menu_item.click()
        self.wait_for_loading()


    def breadcrumb(self) -> str:
        return self.page.locator(".el-breadcrumb").inner_text(timeout=3000)
