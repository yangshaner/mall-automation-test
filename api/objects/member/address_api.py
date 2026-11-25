# api/member/address_api.py
import allure
from typing import Dict

class AddressApi:

    def __init__(self, client):
        self.client = client

    @allure.step("Get all shipping addresses")
    def list(self) -> Dict:
        return self.client.get("/member/address/list")

    @allure.step("Get shipping address detail")
    def detail(self, address_id: int) -> Dict:
        return self.client.get(f"/member/address/{address_id}")

    @allure.step("Add shipping address")
    def add(self, data: str) -> Dict:
        return self.client.post("/member/address", json=data)

    @allure.step("Update shipping address")
    def update(self, address_id: int, data: Dict) -> Dict:
        return self.client.post(f"/member/address/update/{address_id}", json=data)

    @allure.step("Delete shipping address")
    def delete(self, address_id: int) -> Dict:
        return self.client.post(f"/member/address/delete/{address_id}")
