# tasks/product.py
import random

from locust import TaskSet, task, between

from config import Config
from common.data_loader import get_pool
from common.assertion_policy import AssertionPolicy

NAME_PRODUCT_SEARCH = "BROWSE_productSearch"
NAME_PRODUCT_DETAIL = "BROWSE_productDetail"
NAME_CATEGORY_TREE = "BROWSE_categoryTreeList"


class ProductTaskSet(TaskSet):
    wait_time = between(*Config.WAIT_BROWSE)

    def on_start(self):
        self.pool = get_pool()

    @task(Config.RATIO_PRODUCT_LIST)
    def product_search(self):
        brand_id = self.pool.random_brand_id() if self.pool.brands else None
        params = {
            "keyword": "",
            "brandId": brand_id,
            "pageNum": random.randint(1, 5),
            "pageSize": 10,
            "sort": random.choice(["default", "newest", "priceAsc", "priceDesc", "saleDesc"]),
        }
        params = {k: v for k, v in params.items() if v is not None}
        with self.client.get(
                "/product/search",
                params=params,
                name=NAME_PRODUCT_SEARCH,
                catch_response=True,
                timeout=Config.REQUEST_TIMEOUT,
        ) as resp:
            ok, reason = AssertionPolicy.check(NAME_PRODUCT_SEARCH, resp)
            if ok:
                resp.success()
            else:
                resp.failure(reason)

    @task(Config.RATIO_PRODUCT_DETAIL)
    def product_detail(self):
        p = self.pool.random_product()
        with self.client.get(
                f"/product/detail/{p['product_id']}",
                name=NAME_PRODUCT_DETAIL,
                catch_response=True,
                timeout=Config.REQUEST_TIMEOUT,
        ) as resp:
            ok, reason = AssertionPolicy.check(NAME_PRODUCT_DETAIL, resp)
            if ok:
                resp.success()
            else:
                resp.failure(reason)
