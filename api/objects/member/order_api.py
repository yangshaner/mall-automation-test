# api/member/order_api.py
import allure
from typing import Dict, List

class MemberOrderApi:

    def __init__(self, client):
        self.client = client

    @allure.step("Get order list")
    def list(self, status: int = 1, page_num: int = 1, page_size: int = 10) -> Dict:
        return self.client.get("/order/list", params={
            "status": status,
            "pageNum": page_num,
            "pageSize": page_size
        })

    @allure.step("Get order detail")
    def detail(self, order_id: int) -> Dict:
        return self.client.get(f"/order/detail/{order_id}")

    @allure.step("Generate confirm order")
    def generate_confirm_order(self, cart_ids: List[int]) -> Dict:
        return self.client.post("/order/generateConfirmOrder", json=cart_ids)

    @allure.step("Generate order")
    def generate_order(self, data: Dict) -> Dict:
        return self.client.post("/order/generateOrder", json=data)

    @allure.step("Cancel user order")
    def cancel_user_order(self, order_id: int) -> Dict:
        return self.client.post("/order/cancelUserOrder", params={"orderId": order_id})

    @allure.step("Confirm receipt")
    def confirm_receiver_order(self, order_id: int) -> Dict:
        return self.client.post("/order/confirmReceiveOrder", params={"orderId": order_id})

    @allure.step("Delete user order")
    def delete_order(self, order_id: int) -> Dict:
        return self.client.post("/order/deleteOrder", params={"orderId": order_id})

    @allure.step("Payment success callback")
    def pay_success(self, order_id: int, pay_type: int) -> Dict:
        return self.client.post("/order/paySuccess", params={
            "orderId": order_id,
            "payType": pay_type
        })

    @allure.step("Apply for return")
    def return_apply(self, data: Dict) -> Dict:
        return self.client.post("/returnApply/create", json=data)
