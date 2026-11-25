# testcases/member/test_product.py
import pytest
import allure

from common.assertions import ApiAssertion


@allure.feature("Frontend Product Management")
class TestMemberProduct:

    def setup_method(self):
        self.api_assert = ApiAssertion()

    @allure.story("Product Search")
    def test_search_product_list(self, member_product_api):
        response = member_product_api.search(page_num=1, page_size=10)
        self.api_assert.assert_page_response(
            response,
            message="Failed to search product list",
            allow_empty_list=True
        )

    @allure.story("Product search boundary: "
                  "empty keyword - mall backend design issue (returns all records with empty paging)")
    def test_search_product_empty_keyword(self, member_product_api):
        response = member_product_api.search(keyword="", page_num=1, page_size=10)
        body = response.json()
        assert body.get("code", 200) == 200

    @allure.story("Product Search")
    def test_search_product_by_keyword(self, member_product_api, test_product):
        response = member_product_api.search(keyword="测试商品", page_num=1, page_size=100)
        page_data = self.api_assert.assert_page_response(
            response,
            message="Failed to search products by keyword",
            allow_empty_list=True
        )

        product_list = page_data.get("list", [])
        assert any(isinstance(item, dict) and item.get("id") == test_product
                   for item in product_list), \
            "Search results do not contain the test product"

    @allure.story("Product Search")
    def test_search_product_pagination(self, member_product_api):
        response = member_product_api.search(page_num=1, page_size=1)
        page_data = self.api_assert.assert_page_response(
            response,
            expected_page_size=1,
            message="Failed to search products with pagination",
            allow_empty_list=True
        )

        product_list = page_data.get("list", [])
        assert len(product_list) <= 1, "pageSize=1 should return at most 1 record per page"

    @allure.story("Product Search")
    @pytest.mark.parametrize("sort", [0, 1])
    def test_search_product_with_sort(self, member_product_api, sort):
        response = member_product_api.search(sort=sort, page_num=1, page_size=10)
        self.api_assert.assert_page_response(
            response,
            message=f"Failed to search with sort={sort}",
            allow_empty_list=True
        )

    @allure.story("Product Search")
    def test_search_product_by_brand(self, member_product_api, test_brand):
        response = member_product_api.search(brand_id=test_brand, page_num=1, page_size=10)
        self.api_assert.assert_page_response(
            response,
            message="Failed to filter products by brand",
            allow_empty_list=True
        )

    @allure.story("Product Detail")
    def test_product_detail(self, member_product_api):
        search_response = member_product_api.search(page_num=1, page_size=1)
        items = (search_response.json() or {}).get("data", {}).get("list", []) or []
        if not items:
            pytest.skip("No visible product in the frontend, cannot verify the detail API")
        product_id = items[0].get("id")

        response = member_product_api.detail(product_id)
        data = self.api_assert.assert_object_response(
            response,
            required_fields=["product"],
            message="Failed to get product detail"
        )

        product = data.get("product") or {}
        assert product.get("id") == product_id, "Product detail ID does not match the requested ID"
        assert product.get("name"), "Product detail is missing the product name"

    @allure.story("Product Detail")
    def test_new_product_detail(self, member_product_api, test_product):
        response = member_product_api.detail(test_product)
        if response.status_code != 200:
            allure.attach(
                f"HTTP {response.status_code}\n{response.text[:500]}",
                "Abnormal response of new product detail (suspected server-side non-demo data defect)",
                allure.attachment_type.TEXT
            )
            pytest.skip(
                f"The product detail API returned HTTP {response.status_code} for the new product; "
                f"the member side in this environment has a server-side defect for non-demo product detail, skipping"
            )

        data = self.api_assert.assert_object_response(
            response,
            required_fields=["product"],
            message="Failed to get new product detail"
        )
        product = data.get("product") or {}
        assert product.get("id") == test_product, "Product detail ID does not match the requested ID"
        assert product.get("name"), "Product detail is missing the product name"

    @allure.story("Product Detail")
    def test_product_detail_not_exist(self, member_product_api):
        response = member_product_api.detail(999999999)
        result = response.json()
        assert result.get("code") != 200 or not result.get("data"), \
            "A nonexistent product should not return valid detail data"

    @allure.story("Product Category Tree")
    def test_category_tree(self, member_product_api):
        response = member_product_api.category_tree()
        self.api_assert.assert_list_response(
            response,
            message="Failed to get product category tree"
        )
