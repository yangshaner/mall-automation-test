# api/admin/brand_api.py

import allure
from typing import Optional, Dict, List

class BrandApi():

    def __init__(self, client):
        self.client = client

    @allure.step("Get brand list")
    def list(
        self,
        page_num: int = 1,
        page_size: int = 10,
        keyword: Optional[str] = None,
        show_status: Optional[int] = None
    ):
        params = {"pageNum": page_num, page_size: page_size}
        if keyword:
            params["keyword"] = keyword
        if show_status is not None:
            params["showStatus"] = show_status
        return self.client.get('/brand/list', params=params)

    @allure.step("Get all brands")
    def list_all(self):
        return self.client.get('/brand/listAll')

    @allure.step("Get brand detail")
    def detail(self, brand_id: int):
        return self.client.get(f'/brand/{brand_id}')

    @allure.step("Create brand")
    def create(self, data: Dict):
        return self.client.post('/brand/create', json=data)

    @allure.step("Update brand")
    def update(self, brand_id: int, data: Dict):
        return self.client.post(f'/brand/update/{brand_id}', json=data)

    @allure.step("Delete brand")
    def delete(self, brand_id: int):
        return self.client.get(f'/brand/delete/{brand_id}')

    @allure.step("Batch delete brands")
    def delete_batch(self, ids: List[int]):
        return self.client.post('/brand/delete/batch', params={"ids": ids})

    @allure.step("Batch update show status")
    def update_show_status(self, ids: List[int], show_status: int):
        return self.client.post(
            '/brand/update/showStatus',
            params={"ids": ids, "showStatus": show_status}
        )

    @allure.step("Batch update factory status")
    def update_factory_status(self, ids: List[int], factory_status: int):
        return self.client.post(
            '/brand/update/factoryStatus',
            params={"ids": ids, "factoryStatus": factory_status}
        )
