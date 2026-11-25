# api/admin/product_api.py

import allure
from typing import Optional, Dict, List

class ProductApi:

    def __init__(self, client):
        self.client = client

    @allure.step("Get product list")
    def list(self,
             page_num: int = 1,
             page_size: int = 10,
             keyword: Optional[str] = None,
             product_sn: Optional[str] = None,
             publish_status: Optional[int] = None,
             verify_status: Optional[int] = None,
             product_category_id: Optional[int] = None,
             brand_id: Optional[int] = None
             ):
        params = {
            "pageNum": page_num,
            "pageSize": page_size
        }
        if keyword:
            params["keyword"] = keyword
        if product_sn:
            params["productSn"] = product_sn
        if publish_status is not None:
            params["publishStatus"] = publish_status
        if verify_status is not None:
            params["verifyStatus"] = verify_status
        if product_category_id:
            params["productCategoryId"] = product_category_id
        if brand_id:
            params["brandId"] = brand_id

        return self.client.get('/product/list', params=params)

    @allure.step("Create product")
    def create(self, data: Dict):
        return self.client.post('/product/create', json=data)

    @allure.step("Update product")
    def update(self, product_id: int, data: Dict):
        return self.client.post(f'/product/update/{product_id}', json=data)

    @allure.step("Get product edit info")
    def get_update_info(self, product_id: int):
        return self.client.get(f'/product/updateInfo/{product_id}')

    @allure.step("Fuzzy search products")
    def simple_list(self, keyword: str):
        return self.client.get('/product/simpleList', params={"keyword": keyword})

    @allure.step("Batch update verify status")
    def update_verify_status(self, ids: List[int], verify_status: int, detail: str = ""):
        return self.client.post(
            "/product/update/verifyStatus",
            params={"ids": ids, "verifyStatus": verify_status, "detail": detail}
        )

    @allure.step("Batch publish/unpublish products")
    def update_publish_status(self, ids: List[int], publish_status: int):
        return self.client.post(
            "/product/update/publishStatus",
            params={"ids": ids, "publishStatus": publish_status}
        )

    @allure.step("Batch recommend products")
    def update_recommend_status(self, ids: List[int], recommend_status: int):
        return self.client.post(
            "/product/update/recommendStatus",
            params={"ids": ids, "recommendStatus": recommend_status}
        )

    @allure.step("Batch mark as new")
    def update_new_status(self, ids: List[int], new_status: int):
        return self.client.post(
            "/product/update/newStatus",
            params={"ids": ids, "newStatus": new_status}
        )

    @allure.step("Batch update delete status")
    def update_delete_statue(self, ids: List[int], delete_status: int):
        return self.client.post(
            "/product/update/deleteStatus",
            params={"ids": ids, "deleteStatus": delete_status}
        )
