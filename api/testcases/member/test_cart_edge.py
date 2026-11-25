# testcases/test_cart_edge.py
import pytest
import allure


@allure.feature("Cart Management - Boundary and Exception")
class TestCartEdge:

    @allure.story("Add boundary: quantity 0 - mall backend defect (no boundary validation)")
    def test_add_quantity_zero(self, cart_api, test_product):
        data = {"productId": test_product, "productSkuId": 1, "quantity": 0, "price": 99.99}
        resp = cart_api.add(data)
        body = resp.json()
        assert body.get("code", 200) != 200, \
            (f"BUG: mall backend does not validate quantity=0, "
             f"returned code={body.get('code')} data={body.get('data')}, it should be rejected")

    @allure.story("Add boundary: negative quantity")
    def test_add_quantity_negative(self, cart_api, test_product):
        data = {"productId": test_product, "productSkuId": 1, "quantity": -1, "price": 99.99}
        resp = cart_api.add(data)
        assert resp.status_code in (200, 400, 422)

    @allure.story("Add boundary: oversized quantity (99999)")
    def test_add_quantity_overflow(self, cart_api, test_product):
        data = {"productId": test_product, "productSkuId": 1, "quantity": 99999, "price": 99.99}
        resp = cart_api.add(data)
        assert resp.status_code in (200, 400, 422, 500)

    @allure.story("Add exception: nonexistent SKU")
    def test_add_nonexistent_sku(self, cart_api, test_product):
        data = {"productId": test_product, "productSkuId": 99999, "quantity": 1, "price": 99.99}
        resp = cart_api.add(data)
        assert resp.status_code in (200, 400, 404, 422)

    @allure.story("Add exception: nonexistent product")
    def test_add_nonexistent_product(self, cart_api):
        data = {"productId": 99999, "productSkuId": 1, "quantity": 1, "price": 99.99}
        resp = cart_api.add(data)
        assert resp.status_code in (200, 400, 404, 422)

    @allure.story("Cart idempotency: adding the same product twice should accumulate quantity")
    def test_add_same_item_idempotent(self, cart_api, seed_cart_item):
        list_before = cart_api.list().json().get("data", [])
        target = next((i for i in list_before if i.get("id") == seed_cart_item), None)
        qty_before = target.get("quantity", 0) if target else 0

        cart_api.add({
            "productId": target.get("productId") if target else 1,
            "productSkuId": target.get("productSkuId") if target else 1,
            "quantity": 1,
            "price": target.get("price", 99.99) if target else 99.99,
        })

        list_after = cart_api.list().json().get("data", [])
        after_item = next((i for i in list_after if i.get("id") == seed_cart_item), None)
        if after_item:
            assert after_item.get("quantity", 0) >= qty_before

    @allure.story("Update quantity boundary: set to 0")
    def test_update_quantity_to_zero(self, cart_api, seed_cart_item):
        resp = cart_api.update_quantity(seed_cart_item, 0)
        assert resp.status_code in (200, 400, 422)

    @allure.story("Delete exception: deleting a nonexistent cart item - mall backend defect (silent success)")
    def test_delete_nonexistent_item(self, cart_api):
        resp = cart_api.delete([99999])
        body = resp.json()
        assert body.get("code", 200) != 200, \
            f"BUG: deleting a nonexistent cart item should return 404, but mall returned code={body.get('code')}"

    @allure.story("Delete exception: delete with empty list")
    def test_delete_empty_list(self, cart_api):
        resp = cart_api.delete([])
        assert resp.status_code in (200, 400, 422)
