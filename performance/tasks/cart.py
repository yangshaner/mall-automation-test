# tasks/cart.py
import random
import logging


from locust import SequentialTaskSet, task, between

from performance.config import Config
from performance.common.auth import TokenCache
from performance.common.data_loader import get_pool
from performance.common.assertion_policy import AssertionPolicy

logger = logging.getLogger(__name__)

NAME_ADD_CART = "TRADE_addShoppingCart"
NAME_CART_LIST = "TRADE_shoppingCartList"


def add_to_cart(client, headers, product_id, sku_id=None, quantity=None):
    if quantity is None:
        quantity = random.randint(1, 3)
    payload = {"productId": product_id, "quantity": quantity}
    if sku_id:
        payload["productSkuId"] = sku_id
    with client.post(
            "/cart/add",
            json=payload,
            headers=headers,
            name=NAME_ADD_CART,
            catch_response=True,
            timeout=Config.REQUEST_TIMEOUT,
    ) as resp:
        ok, reason = AssertionPolicy.check(NAME_ADD_CART, resp)
        if ok:
            resp.success()
        else:
            resp.failure(reason)
        return ok, reason


def fetch_cart_items(client, headers):
    with client.get(
            "/cart/list",
            headers=headers,
            name=NAME_CART_LIST,
            catch_response=True,
            timeout=Config.REQUEST_TIMEOUT,
    ) as resp:
        ok, reason = AssertionPolicy.check(NAME_CART_LIST, resp)
        if not ok:
            resp.failure(reason)
            return False, [], reason
        resp.success()
        body = None
        try:
            body = resp.json()
            items = body.get("data") or []
        except Exception as e:
            logger.warning(
                f"[cart] /cart/list json parse failed: {type(e).__name__}: {e} | "
                f"content-type={resp.headers.get('Content-Type')} | "
                f"body head={resp.text[:300]}"
            )
            items = []
        if not items:
            data_type = type(body.get("data")).__name__ if isinstance(body, dict) else "n/a"
            logger.warning(
                f"[cart] /cart/list returned empty data. "
                f"type(data)={data_type} | raw body head={resp.text[:500]}"
            )
        return True, items, ""


def cart_ids_of(items):
    return [i["id"] for i in items if i.get("id")]


class CartTaskSet(SequentialTaskSet):

    wait_time = between(*Config.WAIT_TRADE)

    def on_start(self):
        self.pool = get_pool()

    @task
    def add_and_view(self):
        try:
            self._add_and_view()
        finally:
            self.interrupt(reschedule=False)

    def _add_and_view(self):
        headers = TokenCache.auth_header(self.user)
        if not headers:
            return

        p = self.pool.random_product()
        ok, _ = add_to_cart(self.client, headers, p["product_id"], sku_id=p["sku_id"])
        if not ok:
            return

        fetch_cart_items(self.client, headers)
