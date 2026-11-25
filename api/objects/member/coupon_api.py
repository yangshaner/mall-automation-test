# api/member/coupon_api.py
import allure
from typing import Dict, Optional

class MemberCouponApi:

    def __init__(self, client):
        self.client = client

    @allure.step("Get member coupon list")
    def list(self, use_status: Optional[int] = None) -> Dict:
        params = {}
        if use_status is not None:
            params["useStatus"] = use_status
        return self.client.get("/member/coupon/list", params=params)

    @allure.step("Get member coupon history list")
    def list_history(self, use_status: Optional[int] = None) -> Dict:
        params = {}
        if use_status is not None:
            params["useStatus"] = use_status
        return self.client.get("/member/coupon/listHistory", params=params)

    @allure.step("Receive coupon")
    def add(self, coupon_id: int) -> Dict:
        return self.client.post(f"/member/coupon/add/{coupon_id}")

    @allure.step("Get coupons related to a product")
    def list_by_product(self, product_id: int) -> Dict:
        return self.client.get(f"/member/coupon/listByProduct/{product_id}")

    @allure.step("Get coupons related to the cart")
    def list_cart(self, type: int) -> Dict:
        return self.client.get(f"/member/coupon/list/cart/{type}")
