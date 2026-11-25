# api/admin/order_api.py

import allure
from typing import Optional, Dict, List

class OrderApi:

    def __init__(self, client):
        self.client = client

    @allure.step("Query order list")
    def list(
        self,
        page_num: int = 1,
        page_size: int = 10,
        order_sn: Optional[str] = None,
        status: Optional[int] = None,
        order_type: Optional[int] = None,
        source_type: Optional[int] = None,
        receiver_keyword: Optional[str] = None
    ):
        params = {"pageNum": page_num, "pageSize": page_size}
        if order_sn:
            params["orderSn"] = order_sn
        if status is not None:
            params["status"] = status
        if order_type is not None:
            params["orderType"] = order_type
        if source_type is not None:
            params["sourceType"] = source_type
        if receiver_keyword:
            params["receiverKeyword"] = receiver_keyword
        return self.client.get("/order/list", params=params)

    @allure.step("Get order detail")
    def detail(self, order_id: int):
        return self.client.get(f"/order/{order_id}")

    @allure.step("Add order note")
    def update_note(self, order_id: int, note: str, status: int):
        return self.client.post(
            "/order/update/note",
            params={"id": order_id, "note": note, "status": status},
        )

    @allure.step("Update receiver info")
    def update_receiver_info(self, data: Dict):
        return self.client.post(
            "/order/update/receiverInfo",
            json=data
        )

    @allure.step("Update order fee info")
    def update_money_info(self, data: Dict):
        return self.client.post("/order/update/moneyInfo", json=data)

    @allure.step("Batch delivery")
    def delivery(self, data: List[Dict]):
        return self.client.post("/order/update/delivery", json=data)

    @allure.step("Batch close orders")
    def close(self, ids: List[int], note: str = ""):
        return self.client.post("/order/update/close", params={"ids": ids, "note": note})

    @allure.step("Batch delete orders")
    def delete(self, ids: List[int]):
        return self.client.post("/order/delete", params={"ids": ids})
