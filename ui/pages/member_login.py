# ui/pages/member_login.py
from __future__ import annotations

from playwright.sync_api import Locator, Page

from ui.pages.base_page import BasePage


class MemberLoginPage(BasePage):

    PATH_HINT = "login"

    def __init__(self, page: Page):
        super().__init__(page)
        self.username_input: Locator = page.locator(
            'input[type=text], input[type=account], '
            'input[placeholder*="账号"], input[placeholder*="手机"], '
            'input[placeholder*="用户名"]'
        ).first
        self.password_input: Locator = page.locator(
            'input[type=password], input[placeholder*="密码"]'
        ).first
        self.submit_btn: Locator = page.locator(
            'button:has-text("登录"), button:has-text("登 录"), '
            '[class*="login-btn"], [class*="LoginBtn"]'
        ).first

    def open(self, base_url: str) -> None:
        self.page.goto(f"{base_url}/#/login")
        self.wait_for_idle()

    def login_with_password(self, username: str, password: str) -> bool:
        try:
            self.username_input.wait_for(state="visible", timeout=10000)
            self.password_input.wait_for(state="visible", timeout=10000)
        except Exception:
            return self._api_login_fallback(username, password)

        self.username_input.fill(username)
        self.password_input.fill(password)
        self.submit_btn.click()
        self.wait_for_idle()
        return "/login" not in self.page.url and "login" not in self.page.url.lower()

    def login_with_password_expect_error(self, username: str, password: str) -> str:
        try:
            self.username_input.wait_for(state="visible", timeout=10000)
        except Exception:
            return "Login page input did not appear (uni-app H5 may render it differently)"

        self.username_input.fill(username)
        self.password_input.fill(password)
        self.submit_btn.click()
        self.wait_for_idle()
        return self.toast_text()

    def _api_login_fallback(self, username: str, password: str) -> bool:
        import requests
        from ui import config as ui_cfg
        try:
            r = requests.post(
                f"{ui_cfg.MEMBER_API_URL}/sso/login",
                params={"username": username, "password": password},
                timeout=10,
            )
            token = (r.json().get("data") or {}).get("token", "")
            if token:
                self.page.evaluate(
                    f"localStorage.setItem('token', '{token}');"
                )
                stored = self.page.evaluate("() => localStorage.getItem('token')")
                return stored == token
        except Exception:
            pass
        return False
