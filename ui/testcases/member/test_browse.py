# ui/testcases/member/test_browse.py
from __future__ import annotations

import pytest

from ui.pages.member_home import MemberHomePage


@pytest.mark.member
@pytest.mark.ui
class TestMemberBrowse:

    def test_home_loads(self, member_ready) -> None:
        page = member_ready
        home = MemberHomePage(page)
        total = home.product_count()
        assert total >= 1, f"Home page should show >= 1 product card, actual floor={home.floor_count()} guess={home.guess_count()}"

    def test_browse_to_product_detail(self, member_ready) -> None:
        page = member_ready
        home = MemberHomePage(page)
        home.click_product(index=0)
        assert "/pages/product/product" in page.url, f"Should navigate to the product detail page, got URL: {page.url}"

    def test_category_navigation(self, member_ready) -> None:
        page = member_ready
        home = MemberHomePage(page)
        home.go_to_category()
        assert page.url, "Page should still have a URL after clicking category"
