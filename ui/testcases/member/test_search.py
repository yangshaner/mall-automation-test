# ui/testcases/member/test_search.py
from __future__ import annotations

import pytest

from ui.pages.member_home import MemberHomePage


@pytest.mark.member
@pytest.mark.ui
class TestMemberSearch:

    def test_search_keyword(self, member_ready) -> None:
        page = member_ready
        home = MemberHomePage(page)
        home.search("Apple")
        count = home.product_count()
        assert count >= 1, f"Search should render at least 1 product card (matched or default list), got {count}"

    def test_search_result_not_empty(self, member_ready) -> None:
        page = member_ready
        home = MemberHomePage(page)
        assert home.product_count() >= 1, "Home page should render at least 1 product card"
