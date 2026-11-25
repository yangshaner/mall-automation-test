# api/member/login_api.py

import allure
from typing import Dict

class MemberLoginApi:

    def __init__(self, client):
        self.client = client

    @allure.step("Member login")
    def login(self, username: str, password: str) -> Dict:
        return self.client.post("/sso/login", params={
            "username": username,
            "password": password
        })

    @allure.step("Member registration")
    def register(self, username: str, password: str, telephone: str, auth_code: str) -> Dict:
        return self.client.post("/sso/register", params={
            "username": username,
            "password": password,
            "telephone": telephone,
            "authCode": auth_code
        })

    @allure.step("Get auth code")
    def get_auth_code(self, telephone: str) -> Dict:
        return self.client.get("/sso/getAuthCode", params={"telephone": telephone})

    @allure.step("Update password")
    def update_password(self, telephone: str, password: str, auth_code: str) -> Dict:
        return self.client.post("/sso/updatePassword", params={
            "telephone": telephone,
            "password": password,
            "authCode": auth_code
        })

    @allure.step("Refresh token")
    def refresh_token(self) -> Dict:
        return self.client.get("/sso/refreshToken")

    @allure.step("Get member info")
    def get_info(self) -> Dict:
        return self.client.get("/sso/info")
