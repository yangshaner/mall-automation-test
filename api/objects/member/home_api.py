# api/member/home_api.py
import allure
from typing import Dict, Optional

class HomeApi:

    def __init__(self, client):
        self.client = client

    @allure.step("Get home content")
    def content(self) -> Dict:
        return self.client.get("/home/content")

    @allure.step("Get recommended products")
    def recommend_product_list(self, page_num: int = 1, page_size: int = 4) -> Dict:
        return self.client.get("/home/recommandProductList", params={
            "pageNum": page_num,
            "pageSize": page_size
        })

    @allure.step("Get new products")
    def new_product_list(self, page_num: int = 1, page_size: int = 6) -> Dict:
        return self.client.get("/home/newProductList", params={
            "pageNum": page_num,
            "pageSize": page_size
        })

    @allure.step("Get hot products")
    def hot_product_list(self, page_num: int = 1, page_size: int = 6) -> Dict:
        return self.client.get("/home/hotProductList", params={
            "pageNum": page_num,
            "pageSize": page_size
        })

    @allure.step("Get product categories")
    def product_cate_list(self, parent_id: int) -> Dict:
        return self.client.get(f"/home/productCateList/{parent_id}")

    @allure.step("Get subject list")
    def subject_list(self, cate_id: Optional[int] = None, page_num: int = 1, page_size: int = 4) -> Dict:
        params = {"pageNum": page_num, "pageSize": page_size}
        if cate_id:
            params["cateId"] = cate_id
        return self.client.get("/home/subjectList", params=params)
