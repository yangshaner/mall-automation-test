# tasks/trade.py
import logging
import random

from locust import SequentialTaskSet, task, between
from locust_plugins.transaction_manager import TransactionManager

from performance.config import Config
from performance.common.auth import TokenCache
from performance.common.data_loader import get_pool
from performance.tasks.cart import add_to_cart, fetch_cart_items, cart_ids_of
from performance.tasks.order import fetch_default_address, generate_order

logger = logging.getLogger(__name__)


class TradeTaskSet(SequentialTaskSet):
    wait_time = between(*Config.WAIT_TRADE)

    def on_start(self):
        self.pool = get_pool()
        self.tm = TransactionManager()
        self.failed = False
        self._default_addr = None

        headers = TokenCache.auth_header(self.user)
        if headers and not getattr(self.user, "default_addr", None):
            ok, addr, _ = fetch_default_address(self.client, headers)
            if ok:
                self.user.default_addr = addr

    @task
    def full_trade_flow(self):
        try:
            self._full_trade_flow()
        finally:
            self.interrupt(reschedule=False)

    def _full_trade_flow(self):
        self.failed = False
        self._fail_reason = ""
        self.tm.start_transaction("TRADE_completeShoppingLink")

        def _abort(reason):
            self.failed = True
            self._fail_reason = reason

        try:
            headers = TokenCache.auth_header(self.user)
            if not headers:
                return _abort("login failed")

            p = self.pool.random_product()
            ok, _ = add_to_cart(self.client, headers, p["product_id"], sku_id=p["sku_id"])
            if not ok:
                return _abort("add to cart failed")

            ok, items, _ = fetch_cart_items(self.client, headers)
            if not ok:
                return _abort("fetch cart failed")
            cart_ids = cart_ids_of(items)
            if not cart_ids:
                return _abort(f"cart has no selectable items (got {len(items)} rows)")

            cart_ids = random.sample(cart_ids, k=min(len(cart_ids), random.randint(1, 3)))

            addr = getattr(self.user, "default_addr", None)
            if not addr:
                ok, addr, _ = fetch_default_address(self.client, headers)
                if not ok:
                    return _abort("fetch address failed")
                self.user.default_addr = addr
            if not addr:
                return _abort("no receive address for this member")

            ok, _, reason = generate_order(self.client, headers, cart_ids, addr["id"])
            if not ok:
                return _abort(f"generate order failed: {reason[:60]}")

        finally:
            self.tm.end_transaction(
                "TRADE_completeShoppingLink",
                success=not self.failed,
            )
            if self.failed:
                logger.warning(f"[trade] aborted: {self._fail_reason}")
