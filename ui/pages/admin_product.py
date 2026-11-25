# ui/pages/admin_product.py
from __future__ import annotations

from playwright.sync_api import Locator, Page, TimeoutError as PWTimeout

from ui.pages.base_page import BasePage


class AdminProductPage(BasePage):

    def __init__(self, page: Page):
        super().__init__(page)
        self.search_name_input: Locator = self.page.get_by_placeholder("请输入商品名称关键字")
        self.search_btn: Locator = self.page.get_by_role("button", name="搜索")
        self.reset_btn: Locator = self.page.get_by_role("button", name="重置")
        self.add_btn: Locator = self.page.get_by_role("button", name="添加商品")
        self.export_btn: Locator = self.page.get_by_role("button", name="导出数据")
        self.table: Locator = self.page.locator(".el-table__body-wrapper .el-table")


    def search(self, keyword: str) -> None:
        self.fill(self.search_name_input, keyword)
        self.click(self.search_btn)
        self.wait_for_loading()

    def reset(self) -> None:
        self.click(self.reset_btn)
        self.wait_for_loading()


    def product_names(self) -> list:
        try:
            return self.page.locator(".el-table__body .cell").all_inner_texts()
        except PWTimeout:
            return []

    def row_count(self) -> int:
        return self.page.locator(".el-table__body .el-table__row").count()

    def has_product(self, name: str) -> bool:
        return self.el_table_row(name).count() > 0

    def delete_product(self, name: str) -> bool:
        row = self.el_table_row(name)
        if row.count() == 0:
            return False
        row.get_by_role("button", name="删除").click()
        self.page.get_by_role("button", name="确 定").click()
        self.wait_for_loading()
        return True
