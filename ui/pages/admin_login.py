# ui/pages/admin_login.py
from __future__ import annotations

from playwright.sync_api import Locator, Page

from ui.pages.base_page import BasePage


class AdminLoginPage(BasePage):

    PATH_HINT = "login"

    def __init__(self, page: Page):
        super().__init__(page)
        self.username_input: Locator = page.get_by_placeholder("请输入用户名")
        self.password_input: Locator = page.get_by_placeholder("请输入密码")
        self.submit_btn: Locator = page.get_by_role("button", name="登录")
        self.sidebar: Locator = page.locator(
            '.el-aside, .sidebar, [class*="sidebar"], [class*="menu"]'
        )

    def open(self, base_url: str) -> None:
        self.page.goto(f"{base_url}/#/login")
        self.username_input.wait_for(state="visible", timeout=10000)

    def login(self, username: str, password: str) -> bool:
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.submit_btn.click()
        try:
            self.page.wait_for_url(lambda url: "/login" not in url, timeout=15000)
            return True
        except Exception:
            return False

    def login_expect_error(self, username: str, password: str) -> str:
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.submit_btn.click()
        self.wait_for_idle()
        toast = self.toast_text()
        if toast:
            return toast
        field_err = self.page.locator(
            ".el-form-item__error, .el-input__error, .el-message-box, [class*='error']"
        ).first
        if field_err.is_visible(timeout=2000):
            txt = field_err.inner_text().strip()
            if txt:
                return txt
        return ""
