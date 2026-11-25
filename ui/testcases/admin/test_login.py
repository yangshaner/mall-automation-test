# ui/testcases/admin/test_login.py
from __future__ import annotations

import pytest

from ui import config as ui_cfg
from ui.pages.admin_login import AdminLoginPage


@pytest.mark.admin
@pytest.mark.ui
class TestAdminLogin:

    def test_login_success(self, page) -> None:
        login = AdminLoginPage(page)
        login.open(ui_cfg.ADMIN_BASE_URL)
        ok = login.login(ui_cfg.ADMIN_USERNAME, ui_cfg.ADMIN_PASSWORD)
        assert ok, "URL should no longer contain /login after a successful login"
        assert login.sidebar.count() > 0 or "首页" in login.text_by_text("首页").inner_text(), \
            "Admin home elements should be visible after login"

    def test_login_wrong_password(self, page) -> None:
        login = AdminLoginPage(page)
        login.open(ui_cfg.ADMIN_BASE_URL)
        err = login.login_expect_error(ui_cfg.ADMIN_USERNAME, "wrong_password")
        assert "/login" in page.url, "Wrong password should stay on the login page"
        assert err, f"An error message should appear, got: {err}"

    def test_login_empty_username(self, page) -> None:
        login = AdminLoginPage(page)
        login.open(ui_cfg.ADMIN_BASE_URL)
        err = login.login_expect_error("", ui_cfg.ADMIN_PASSWORD)
        assert err, f"Empty username should be blocked, got: {err}"
        assert "/login" in page.url, "Empty username should stay on the login page"
