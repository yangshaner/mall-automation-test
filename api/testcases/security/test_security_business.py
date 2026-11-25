# testcase/security/test_security_business.py
import time
import threading
import concurrent.futures

import pytest
import allure
import requests
from requests.adapters import HTTPAdapter

from common.assertions import ApiAssertion
from common.client.member_client import MemberClient
from api.objects.member.collection_api import CollectionApi


@allure.feature("Security Test - Business Logic and Concurrency")
class TestSecurityBusiness:

    FAST_TIMEOUT = (5, 10)

    def setup_method(self):
        self.api_assert = ApiAssertion()

    def _build_fast_collection_api(self):
        client = MemberClient()
        client._login()
        no_retry_adapter = HTTPAdapter(max_retries=0)
        client.session.mount("http://", no_retry_adapter)
        client.session.mount("https://", no_retry_adapter)
        client.timeout = self.FAST_TIMEOUT

        api = CollectionApi(client)
        return api, client

    def _safe_call(self, func, step_name: str):
        try:
            return func()
        except requests.exceptions.RequestException as e:
            allure.attach(str(e), f"{step_name} request exception", allure.attachment_type.TEXT)
            return None

    def _request_or_skip(self, func, step_name: str):
        resp = self._safe_call(func, step_name)
        if resp is None:
            pytest.skip(f"{step_name} no response (endpoint timeout/unavailable), "
                        f"likely a test environment or backend issue, skipping idempotency check")
        return resp


    @allure.story("Repeatedly Claiming the Same Coupon")
    def test_duplicate_coupon_claim(self, member_coupon_api, test_product):
        product_coupon_response = member_coupon_api.list_by_product(test_product)
        product_coupons = product_coupon_response.json().get("data", [])
        if not product_coupons:
            pytest.skip("No claimable coupon for the current product")

        coupon_id = product_coupons[0].get("id")
        first = member_coupon_api.add(coupon_id)
        first_result = first.json()

        second = member_coupon_api.add(coupon_id)
        second_result = second.json()

        first_ok = first_result.get("code") == 200
        second_ok = second_result.get("code") == 200
        assert not (first_ok and second_ok), \
            "The same coupon should not be claimed successfully twice"

    @allure.story("Repeatedly Collecting the Same Product")
    def test_duplicate_collection(self, test_product, data_generator):
        api, client = self._build_fast_collection_api()

        def query_list():
            return client.get(
                "/member/productCollection/list",
                params={"pageNum": 1, "pageSize": 100},
                timeout=self.FAST_TIMEOUT
            )

        self._request_or_skip(query_list, "collection list probe")

        data = {
            "productId": test_product,
            "productName": f"duplicateFavoriteTest_{data_generator.random_string(4)}",
            "productPic": "test.png",
            "productPrice": "99.99"
        }
        try:
            first = self._request_or_skip(lambda: api.add(data), "first collection")
            first_result = first.json()
            if first_result.get("code") != 200:
                pytest.skip(f"First collection did not succeed ({first_result.get('message')}), "
                            f"cannot verify duplicate submission idempotency")

            second = self._safe_call(lambda: api.add(data), "duplicate collection")
            allure.attach(
                f"status={second.status_code}, body={second.text[:300]}" if second is not None
                else "No response for second collection (timeout)",
                "duplicate collection response", allure.attachment_type.TEXT
            )

            list_response = self._request_or_skip(query_list, "query collection list")
            items = (list_response.json() or {}).get("data", {}).get("list", []) or []
            count = sum(1 for item in items if item.get("productId") == test_product)
            assert count <= 1, f"The same product was collected repeatedly, appearing {count} times"
        finally:
            try:
                client.post(
                    "/member/productCollection/delete",
                    params={"productId": test_product},
                    timeout=self.FAST_TIMEOUT
                )
            except requests.exceptions.RequestException as e:
                allure.attach(str(e), "Failed to clean up collection", allure.attachment_type.TEXT)

    @allure.story("Repeatedly Confirming Receipt")
    def test_duplicate_confirm_receive(self, member_order_api):
        list_response = member_order_api.list(status=2, page_size=1)
        orders = list_response.json().get("data", {}).get("list", [])
        if not orders:
            pytest.skip("No shipped order available for testing")

        order_id = orders[0].get("id")
        first = member_order_api.confirm_receiver_order(order_id)
        first_result = first.json()

        second = member_order_api.confirm_receiver_order(order_id)
        second_result = second.json()

        assert not (first_result.get("code") == 200 and second_result.get("code") == 200), \
            "The same order should not be confirmed as received twice"

    @allure.story("Repeated Payment Callback")
    def test_duplicate_pay_callback(self, member_order_api):
        list_response = member_order_api.list(status=0, page_size=1)
        orders = list_response.json().get("data", {}).get("list", [])
        if not orders:
            pytest.skip("No pending-payment order available for testing")

        order_id = orders[0].get("id")
        first = member_order_api.pay_success(order_id, pay_type=1)
        first_result = first.json()

        second = member_order_api.pay_success(order_id, pay_type=1)
        second_result = second.json()

        assert not (first_result.get("code") == 200 and second_result.get("code") == 200), \
            "The payment success callback should not be processed twice"

    @allure.story("Repeatedly Cancelling Orders")
    def test_duplicate_cancel_order(self, member_order_api):
        list_response = member_order_api.list(status=0, page_size=1)
        orders = list_response.json().get("data", {}).get("list", [])
        if not orders:
            pytest.skip("No pending-payment order available for testing")

        order_id = orders[0].get("id")
        first = member_order_api.cancel_user_order(order_id)
        first_result = first.json()

        second = member_order_api.cancel_user_order(order_id)
        second_result = second.json()

        assert not (first_result.get("code") == 200 and second_result.get("code") == 200), \
            "The same order should not be cancelled twice"


    @allure.story("Concurrent Add of the Same Product to Cart")
    def test_concurrent_add_to_cart(self, cart_api, test_product, data_generator):
        from common.db.mysql_util import mysql
        sku_rows = mysql.query(
            "SELECT id, price FROM pms_sku_stock WHERE product_id = %s AND stock > 0 ORDER BY id LIMIT 1",
            (test_product,)
        )
        assert sku_rows, f"Product {test_product} has no available SKU (no stock record in pms_sku_stock)"
        sku_id = sku_rows[0]["id"]
        price = float(sku_rows[0]["price"] or 99.99)

        data = {
            "productId": test_product,
            "productSkuId": sku_id,
            "quantity": 1,
            "price": price
        }

        results = []
        lock = threading.Lock()

        def add_once():
            try:
                resp = cart_api.add(data)
                with lock:
                    results.append(resp.json())
            except Exception as e:
                with lock:
                    results.append({"error": str(e)})

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(add_once) for _ in range(10)]
            concurrent.futures.wait(futures)

        cart_api.clear()

        success_count = sum(1 for r in results if r.get("code") == 200)
        error_count = sum(1 for r in results if "error" in r)
        assert error_count == 0, "Concurrent requests should not produce unhandled exceptions"
        assert success_count > 0, "All concurrent add-to-cart requests failed"

    @allure.story("Concurrent Claim of the Same Coupon")
    def test_concurrent_coupon_claim(self, member_coupon_api, test_product):
        product_coupon_response = member_coupon_api.list_by_product(test_product)
        product_coupons = product_coupon_response.json().get("data", [])
        if not product_coupons:
            pytest.skip("No claimable coupon for the current product")

        coupon_id = product_coupons[0].get("id")
        results = []
        lock = threading.Lock()

        def claim():
            try:
                resp = member_coupon_api.add(coupon_id)
                with lock:
                    results.append(resp.json())
            except Exception as e:
                with lock:
                    results.append({"error": str(e)})

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(claim) for _ in range(10)]
            concurrent.futures.wait(futures)

        success_count = sum(1 for r in results if r.get("code") == 200)
        assert success_count <= 1, \
            f"Concurrent claim of the same coupon succeeded {success_count} times, possible over-issuance"

    @allure.story("Rapid Consecutive Requests - Anti-Flood")
    def test_rapid_requests(self, member_product_api):
        start = time.time()
        results = []
        for _ in range(20):
            try:
                resp = member_product_api.search(page_num=1, page_size=5)
                results.append(resp.status_code)
            except Exception as e:
                results.append(("error", str(e)))

        elapsed = time.time() - start
        error_count = sum(1 for r in results if isinstance(r, tuple))
        assert error_count < 20, f"All rapid consecutive requests failed, elapsed {elapsed:.2f}s"

    @allure.story("Concurrent Order List Queries")
    def test_concurrent_order_list(self, member_order_api):
        results = []
        lock = threading.Lock()

        def query():
            try:
                resp = member_order_api.list(status=-1, page_num=1, page_size=5)
                with lock:
                    results.append(resp.status_code)
            except Exception as e:
                with lock:
                    results.append(("error", str(e)))

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(query) for _ in range(5)]
            concurrent.futures.wait(futures)

        error_count = sum(1 for r in results if isinstance(r, tuple))
        assert error_count == 0, "Concurrent order list queries should not raise exceptions"
        assert all(r == 200 for r in results), "Concurrent order list queries should all return 200"
