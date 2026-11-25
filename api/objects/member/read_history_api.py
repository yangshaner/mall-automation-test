# api/member/read_history_api.py
import allure
from typing import Dict, List

class ReadHistoryApi:

    def __init__(self, client):
        self.client = client

    @allure.step("Get browse history")
    def list(self, page_num: int = 1, page_size: int = 5) -> Dict:
        return self.client.get("/member/readHistory/list", params={
            "pageNum": page_num,
            "pageSize": page_size
        })

    @allure.step("Create browse history")
    def create(self, data: Dict) -> Dict:
        return self.client.post("/member/readHistory/create", json=data)

    @allure.step("Delete browse history")
    def delete(self, ids: List[str]) -> Dict:
        return self.client.post("/member/readHistory/delete", params={"ids": ids})

    @allure.step("Clear browse history")
    def clear(self) -> Dict:
        return self.client.post("/member/readHistory/clear")
