# ui/pages/base_page.py
from __future__ import annotations

import logging

from playwright.sync_api import Locator, Page, TimeoutError as PWTimeout

logger = logging.getLogger(__name__)


class BasePage:

    TITLE: str = ""
    PATH_HINT: str = ""

    def __init__(self, page: Page):
        self.page = page


    def url(self) -> str:
        return self.page.url

    def title(self) -> str:
        return self.page.title()

    def screenshot(self, name: str = "page") -> bytes:
        return self.page.screenshot(full_page=True)


    def wait_for_url(self, hint: str, timeout_ms: int = 15000) -> bool:
        try:
            self.page.wait_for_url(f"**/*{hint}**", timeout=timeout_ms)
            return True
        except PWTimeout:
            return False

    def wait_for_idle(self, timeout_ms: int = 5000) -> None:
        try:
            self.page.wait_for_load_state('networkidle', timeout=timeout_ms)
        except PWTimeout:
            logger.debug("wait_for_idle timed out, continuing")


    def button_by_text(self, text: str, exact: bool = True) -> Locator:
        return self.page.get_by_role("button", name=text, exact=exact)

    def input_by_placeholder(self, placeholder: str) -> Locator:
        return self.page.get_by_placeholder(placeholder)

    def input_by_label(self, label: str) -> Locator:
        return self.page.get_by_label(label)

    def link_by_text(self, text: str) -> Locator:
        return self.page.get_by_role("link", name=text)

    def text_by_text(self, text: str, exact: bool = False) -> Locator:
        return self.page.get_by_text(text, exact=exact)


    def fill(self, locator: Locator, value: str, clear_first: bool = True) -> None:
        if clear_first:
            locator.fill("")
        locator.fill(value)

    def click(self, locator: Locator, wait_for_navigation: bool = False) -> None:
        if wait_for_navigation:
            with self.page.expect_navigation():
                locator.click()
        else:
            locator.click()


    def dismiss_overlays(self) -> None:
        try:
            for mask_sel in ['.uni-mask:visible', '.uni-mask-enter-active',
                             '.uni-popup__wrapper', '[class*="mask"][class*="visible"]']:
                masks = self.page.locator(mask_sel)
                for i in range(masks.count()):
                    try:
                        masks.nth(i).click(force=True, timeout=500)
                    except Exception:
                        pass

            self.page.keyboard.press("Escape")

            self.wait_for_idle(timeout_ms=1500)
        except Exception:
            pass


    def get_toast(self) -> Locator:
        return self.page.locator(
            '.el-message, .el-notification, .uni-popup__wrapper, '
            '[class*="toast"], [class*="Toast"], [class*="message"], [class*="Message"]'
        )

    def toast_text(self) -> str:
        try:
            return self.get_toast().first.inner_text(timeout=3000)
        except PWTimeout:
            return ""

    def has_toast(self) -> bool:
        return self.get_toast().count() > 0


    def click_bottom_tab(self, tab_name: str) -> None:
        tab = self.page.get_by_text(tab_name, exact=True)
        tab.click()
        self.wait_for_idle()
