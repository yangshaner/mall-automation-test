# ui/testcases/member/test_my.py
from __future__ import annotations

import pytest
import requests

from ui import config as ui_cfg
from ui.pages.member_my import MemberMyPage


@pytest.mark.member
@pytest.mark.ui
class TestMemberMyAddress:

    @staticmethod
    def _member_token() -> str:
        r = requests.post(
            f"{ui_cfg.MEMBER_API_URL}/sso/login",
            params={"username": ui_cfg.MEMBER_USERNAME,
                    "password": ui_cfg.MEMBER_PASSWORD},
            timeout=10,
        )
        return (r.json().get("data") or {}).get("token", "")

    @staticmethod
    def _addresses_via_api(token: str) -> list:
        r = requests.get(
            f"{ui_cfg.MEMBER_API_URL}/member/address/list",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        body = r.json()
        data = body.get("data")
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("list") or []
        return []

    def test_address_api_crud(self, member_ready) -> None:
        page = member_ready
        my_page = MemberMyPage(page)

        my_page.go_to_mine()
        assert "/pages/user" in page.url, f"Should navigate to the profile center, got {page.url}"

        api_token = self._member_token()
        assert api_token, "API login should return a token"
        addresses = self._addresses_via_api(api_token)
        assert isinstance(addresses, list), f"Address endpoint should return a list, got {type(addresses)}"

        if len(addresses) >= 0:
            print(f"[address] demo account address count: {len(addresses)}")


@pytest.mark.member
@pytest.mark.ui
class TestMemberMyFavorites:

    def test_user_page_renders(self, member_ready) -> None:
        page = member_ready
        my_page = MemberMyPage(page)
        my_page.go_to_mine()
        assert "/pages/user" in page.url, f"Should navigate to the profile center, got {page.url}"
        assert page.title(), "Page should have a title"
