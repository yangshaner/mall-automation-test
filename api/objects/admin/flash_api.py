# api/admin/flash_api.py
import allure
from typing import Optional, Dict, List

class FlashApi:

    def __init__(self, client):
        self.client = client


    @allure.step("Get flash sale campaign list")
    def list(self, page_num: int = 1, page_size: int = 10, keyword: Optional[str] = None):
        params = {"pageNum": page_num, "pageSize": page_size}
        if keyword:
            params["keyword"] = keyword
        return self.client.get("/flash/list", params=params)

    @allure.step("Get campaign detail")
    def detail(self, flash_id: int):
        return self.client.get(f"/flash/{flash_id}")

    @allure.step("Create flash sale campaign")
    def create(self, data: Dict):
        return self.client.post("/flash/create", json=data)

    @allure.step("Edit campaign")
    def update(self, flash_id: int, data: Dict):
        return self.client.post(f"/flash/update/{flash_id}", json=data)

    @allure.step("Update online/offline status")
    def update_status(self, flash_id: int, status: int):
        return self.client.post(
            f"/flash/update/status/{flash_id}",
            params={"status": status},
        )

    @allure.step("Delete campaign")
    def delete(self, flash_id: int):
        return self.client.post(f"/flash/delete/{flash_id}")


    @allure.step("Get all sessions")
    def session_list(self):
        return self.client.get("/flashSession/list")

    @allure.step("Get session detail")
    def session_detail(self, session_id: int):
        return self.client.get(f"/flashSession/{session_id}")

    @allure.step("Create session")
    def session_create(self, data: Dict):
        return self.client.post("/flashSession/create", json=data)

    @allure.step("Update session")
    def session_update(self, session_id: int, data: Dict):
        return self.client.post(f"/flashSession/update/{session_id}", json=data)

    @allure.step("Update session enabled status")
    def session_update_status(self, session_id: int, status: int):
        return self.client.post(
            f"/flashSession/update/status/{session_id}",
            params={"status": status}
        )

    @allure.step("Delete session")
    def session_delete(self, session_id: int):
        return self.client.post(f"/flashSession/delete/{session_id}")


    @allure.step("Get flash sale product relation list")
    def relation_list(
            self,
            flash_promotion_id: int,
            flash_promotion_session_id: int,
            page_num: int = 1,
            page_size: int = 10
    ):
        return self.client.get(
            "/flashProductRelation/list",
            params={
                "flashPromotionId": flash_promotion_id,
                "flashPromotionSessionId": flash_promotion_session_id,
                "pageNum": page_num,
                "pageSize": page_size
            }
        )

    @allure.step("Get promotion info of a related product")
    def relation_detail(self, relation_id: int):
        return self.client.get(f"/flashProductRelation/{relation_id}")

    @allure.step("Batch select products and add relations")
    def relation_create(self, data: List[Dict]):
        return self.client.post("/flashProductRelation/create", json=data)

    @allure.step("Update relation info")
    def relation_update(self, relation_id: int, data: Dict):
        return self.client.post(f"/flashProductRelation/update/{relation_id}", json=data)

    @allure.step("Delete relation")
    def relation_delete(self, relation_id: int):
        return self.client.post(f"/flashProductRelation/delete/{relation_id}")
