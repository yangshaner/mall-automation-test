# api/admin/category_api.py
import allure
from typing import List, Dict

class CategoryApi:

    def __init__(self, client):
        self.client = client

    @allure.step("Get product category list")
    def list(self, parent_id: int = 0, page_num: int = 1, page_size: int = 10):
        return self.client.get(
            f"/productCategory/list/{parent_id}",
            params={"pageNum": page_num, "pageSize": page_size},
        )

    @allure.step("Get product category detail")
    def detail(self, category_id: int):
        return self.client.get(f"/productCategory/{category_id}")

    @allure.step("Get all top-level categories and their children")
    def list_with_children(self):
        return self.client.get("/productCategory/list/withChildren")

    @allure.step("Create product category")
    def create(self, data: Dict):
        return self.client.post("/productCategory/create", json=data)

    @allure.step("Update product category")
    def update(self, category_id: int, data: Dict):
        return self.client.post(f"/productCategory/update/{category_id}", json=data)

    @allure.step("Update show status")
    def update_show_status(self, ids: List[int], show_status: int):
        return self.client.post(
            "/productCategory/update/showStatus",
            params={"ids": ids, "showStatus": show_status}
        )

    @allure.step("Update navigation bar show status")
    def update_nav_status(self, ids: List[int], nav_status: int):
        return self.client.post(
            "/productCategory/update/navStatus",
            params={"ids": ids, "navStatus": nav_status}
        )

    @allure.step("Delete product category")
    def delete(self, category_id: int):
        return self.client.post(f"/productCategory/delete/{category_id}")
