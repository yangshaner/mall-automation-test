# ui/testcases/admin/test_product.py
from __future__ import annotations

import pytest

from ui.pages.admin_dashboard import AdminDashboardPage
from ui.pages.admin_product import AdminProductPage


@pytest.mark.admin
@pytest.mark.ui
class TestAdminProduct:

    def test_navigate_to_product(self, admin_ready) -> None:
        page = admin_ready
        dashboard = AdminDashboardPage(page)
        dashboard.navigate_to("商品管理")
        dashboard.navigate_to("商品列表")
        assert "product" in page.url.lower() or "product" in page.url, \
            f"Should navigate to a product-related route, got {page.url}"

    def test_search_product(self, admin_ready) -> None:
        page = admin_ready
        product = AdminProductPage(page)
        dashboard = AdminDashboardPage(page)
        dashboard.navigate_to("商品管理")
        dashboard.navigate_to("商品列表")
        product.search("Apple")
        names = product.product_names()
        assert any("Apple" in n or "iPhone" in n or "iPad" in n for n in names), \
            f"Searching Apple should hit demo products, got first rows: {names[:5]}"
