# api/member/cart_api.py
import allure
from typing import Dict, List, Optional


class CartApi:

    def __init__(self, client):
        self.client = client

    @allure.step("Get cart list")
    def list(self) -> Dict:
        return self.client.get("/cart/list")

    @allure.step("Get cart list with promotion info")
    def list_promotion(self, cart_ids: Optional[List[int]] = None) -> Dict:
        params = {}
        if cart_ids:
            params["cartIds"] = cart_ids
        return self.client.get("/cart/list/promotion", params=params)

    @allure.step("Add product to cart")
    def add(self, data: Dict) -> Dict:
        return self.client.post("/cart/add", json=data)

    @allure.step("Update cart item quantity")
    def update_quantity(self, cart_id: int, quantity: int) -> Dict:
        return self.client.get("/cart/update/quantity", params={
            "id": cart_id,
            "quantity": quantity
        })

    @allure.step("Update cart item attributes")
    def update_attr(self, data: Dict) -> Dict:
        return self.client.post("/cart/update/attr", json=data)

    @allure.step("Delete specified cart items")
    def delete(self, ids: List[int]) -> Dict:
        return self.client.post("/cart/delete", params={"ids": ids})

    @allure.step("Clear cart")
    def clear(self) -> Dict:
        return self.client.post("/cart/clear")

    @allure.step("Get cart item attributes by product")
    def get_cart_product(self, product_id: int) -> Dict:
        return self.client.get(f"/cart/getProduct/{product_id}")
