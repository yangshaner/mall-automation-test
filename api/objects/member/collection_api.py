# api/member/collection_api.py
import allure
from typing import Dict

class CollectionApi:

    def __init__(self, client):
        self.client = client

    @allure.step("Get product collection list")
    def list(self, page_num: int = 1, page_size: int = 5) -> Dict:
        return self.client.get("/member/productCollection/list", params={
            "pageNum": page_num,
            "pageSize": page_size
        })

    @allure.step("Get product collection detail")
    def detail(self, product_id: int) -> Dict:
        return self.client.get(f"/member/productCollection/detail/{product_id}")

    @allure.step("Add product collection")
    def add(self, data: Dict) -> Dict:
        return self.client.post("/member/productCollection/add", json=data)

    @allure.step("Delete product collection")
    def delete(self, product_id: int) -> Dict:
        return self.client.post("/member/productCollection/delete", params={
            "productId": product_id
        })

    @allure.step("Clear product collections")
    def clear(self) -> Dict:
        return self.client.post("/member/productCollection/clear")
