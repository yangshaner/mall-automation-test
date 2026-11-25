# api/member/brand_api.py
import allure

class MemberBrandApi:

    def __init__(self, client):
        self.client = client

    @allure.step("Get recommended brand list")
    def recommend_list(self, page_num: int, page_size: int = 6):
        return self.client.get(
            "/brand/recommendList",
            params={"pageNum": page_num, "pageSize": page_size}
        )

    @allure.step("Get brand detail")
    def detail(self, brand_id: int):
        return self.client.get(f"/brand/detail/{brand_id}")

    @allure.step("Get products of a brand")
    def product_list(self, brand_id: int, page_num: int = 1, page_size: int = 6):
        return self.client.get(
            "/brand/productList",
            params={"brandId": brand_id, "pageNum": page_num, "pageSize": page_size}
        )
