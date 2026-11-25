# api/mmeber/return_api.py
import allure
from typing import Dict

class ReturnApi:

    def __init__(self, client):
        self.client = client

    @allure.step("Apply for return")
    def create(self, data: Dict):
        return self.client.post("/retuenApply/create", json=data)
