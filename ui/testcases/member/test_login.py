# ui/testcases/member/test_login.py
from __future__ import annotations

import pytest
import requests

from ui import config as ui_cfg
from ui.pages.member_login import MemberLoginPage


@pytest.mark.member
@pytest.mark.ui
class TestMemberLogin:

    def test_login_success(self, member_page_blank) -> None:
        page = member_page_blank
        login = MemberLoginPage(page)
        page.add_init_script(
            "localStorage.removeItem('token'); localStorage.removeItem('member_token');"
        )
        login.open(ui_cfg.MEMBER_BASE_URL)
        ok = login.login_with_password(ui_cfg.MEMBER_USERNAME, ui_cfg.MEMBER_PASSWORD)
        assert ok, "Page should leave the login URL after a successful login"
        token = page.evaluate("() => localStorage.getItem('token') || localStorage.getItem('member_token')")
        assert token, f"localStorage should hold a token after login, got: {page.evaluate('() => Object.keys(localStorage)')}"

    def test_login_wrong_password(self, member_page_blank) -> None:
        page = member_page_blank
        login = MemberLoginPage(page)
        import requests as req
        r = req.post(
            f"{ui_cfg.MEMBER_API_URL}/sso/login",
            params={"username": ui_cfg.MEMBER_USERNAME, "password": "wrong123"},
            timeout=10,
        )
        body = r.json()
        token = (body.get("data") or {}).get("token", "") if isinstance(body.get("data"), dict) else ""
        assert r.status_code != 200 or body.get("code") != 200 or not token, \
            f"Wrong password must not return a valid token, got: HTTP={r.status_code} body={body}"

    def test_login_empty_username(self, member_page_blank) -> None:
        page = member_page_blank
        login = MemberLoginPage(page)
        import requests as req
        r = req.post(
            f"{ui_cfg.MEMBER_API_URL}/sso/login",
            params={"username": "", "password": ui_cfg.MEMBER_PASSWORD},
            timeout=10,
        )
        body = r.json()
        token = (body.get("data") or {}).get("token", "") if isinstance(body.get("data"), dict) else ""
        assert not token, f"Empty username must not return a valid token, got body={body}"
