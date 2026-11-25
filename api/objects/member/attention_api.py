# api/member/attention_api.py
import allure
from typing import Dict

class AttentionApi:

    def __init__(self, client):
        self.client = client

    @allure.step("Get brand attention list")
    def list(self, page_num: int = 1, page_size: int = 5) -> Dict:
        return self.client.get("/member/attention/list", params={
            "page_num": page_num,
            "page_size": page_size
        })

    @allure.step("Get brand attention detail")
    def detail(self, brand_id: int) -> Dict:
        return self.client.get("/member/attention/detail", params={
            "brandId": brand_id
        })

    @allure.step("Add brand attention")
    def add(self, data: Dict) -> Dict:
        return self.client.post("/member/attention/add", json=data)

    @allure.step("Remove brand attention")
    def delete(self, brand_id: int) -> Dict:
        return self.client.post("/member/attention/delete", params={
            "brandId": brand_id
        })

    @allure.step("Clear brand attentions")
    def clear(self) -> Dict:
        return self.client.post("/member/attention/clear")
