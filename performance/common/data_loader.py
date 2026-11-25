# common/data_loader.py
import csv
import logging
import os
import random
import threading
from performance.config import Config


logger = logging.getLogger(__name__)


class DataPool:

    def __init__(self):
        self.users = self._load_users()
        self.products = self._load_products()
        self.brands = self._load_brands()

        if not self.users:
            raise RuntimeError(
                f"{Config.USERS_CSV} has no data rows (expected header: username,password). "
                f"Export accounts from ums_member before running the test."
            )
        if not self.products:
            raise RuntimeError(
                f"{Config.PRODUCTS_CSV} has no data rows (expected header: product_id,sku_id). "
                f"Export products from pms_product before running the test."
            )


        self._user_lock = threading.Lock()
        self._user_cursor = 0

    def _load_users(self):
        rows = []
        with open(Config.USERS_CSV, newline='', encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                rows.append({"username": r["username"], "password": r["password"]})
            return rows

    def _load_products(self):
        rows = []
        with open(Config.PRODUCTS_CSV, newline='', encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                rows.append({
                     "product_id": int(r["product_id"]),
                     "sku_id": int(r.get("sku_id", 0)),
                })
            return rows

    def _load_brands(self):
        if not os.path.exists(Config.BRANDS_CSV):
            logger.warning(f"[data] {Config.BRANDS_CSV} not found; brand product/detail tasks "
                           f"will fall back to /brand/recommendList. Export brand ids to enable them.")

            return []
        rows = []
        with open(Config.BRANDS_CSV, newline='', encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                rows.append(int(r["brand_id"]))
        return rows

    def random_user(self):
        return random.choice(self.users)

    def random_product(self):
        return random.choice(self.products)

    def random_products(self, n=2):
        return random.sample(self.products, min(n, len(self.products)))

    def next_user(self):
        with self._user_lock:
            u = self.users[self._user_cursor % len(self.users)]
            self._user_cursor += 1
            return u

    def random_brand_id(self):
        return random.choice(self.brands)


_pool = None

def get_pool():
    global _pool
    if _pool is None:
        _pool = DataPool()
    return _pool
