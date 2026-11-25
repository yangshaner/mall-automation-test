# api/amdin/coupon_api.py
import allure
from typing import Optional, Dict

class CouponApi:

    def __init__(self, client):
        self.client = client

    @allure.step("Get coupon list")
    def list(
            self,
            page_num: int = 1,
            page_size: int = 10,
            name: Optional[str] = None,
            type: Optional[int] = None
    ):
        params = {"pageNum": page_num, "pageSize": page_size}
        if name:
            params["name"] = name
        if type is not None:
            params["type"] = type
        return self.client.get("/coupon/list", params=params)

    @allure.step("Get coupon detail")
    def detail(self, coupon_id: int):
        return self.client.get(f"/coupon/{coupon_id}")

    @allure.step("Create coupon")
    def create(self, data: Dict):
        return self.client.post("/coupon/create", json=data)

    @allure.step("Update coupon")
    def update(self, coupon_id: int, data: Dict):
        return self.client.post(f"/coupon/update/{coupon_id}", json=data)

    @allure.step("Delete coupon")
    def delete(self, coupon_id: int):
        return self.client.post(f"/coupon/update/{coupon_id}")
