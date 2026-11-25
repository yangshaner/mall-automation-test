# tasks/browse.py
import random

from locust import TaskSet, task


from performance.config import Config
from performance.common.data_loader import get_pool
from performance.common.assertion_policy import AssertionPolicy


class BrowseTaskSet(TaskSet):

    def on_start(self):
        self.pool = get_pool()

    @task(Config.RATIO_BROWSE_BRAND_PRODUCT_LIST)
    def brand_product_list(self):
        if not self.pool.brands:
            return self.brand_recommend_list()

        brand_id = self.pool.random_brand_id()
        page = random.randint(1, 5)
        with self.client.get(
                f"/brand/productList?brandId={brand_id}&pageNum={page}&pageSize=10",
                name="BROWSE_brandProductList",
                catch_response=True,
                timeout=Config.REQUEST_TIMEOUT,
        ) as resp:
            ok, reason = AssertionPolicy.check("BROWSE_brandProductList", resp)
            if ok:
                resp.success()
            else:
                resp.failure(reason)
        self.interrupt(reschedule=False)

    @task(Config.RATIO_BROWSE_BRAND_RECOMMEND_LIST)
    def brand_recommend_list(self):
        page = random.randint(1, 3)
        with self.client.get(
                f"/brand/recommendList?pageNum={page}&pageSize=6",
                name="BROWSE_recommendBrand",
                catch_response=True,
                timeout=Config.REQUEST_TIMEOUT,
        ) as resp:
            ok, reason = AssertionPolicy.check("BROWSE_recommendBrand", resp)
            if ok:
                resp.success()
            else:
                resp.failure(reason)
        self.interrupt(reschedule=False)

    @task(Config.RATIO_BROWSE_BRAND_DETAIL)
    def brand_detail(self):
        if not self.pool.brands:
            return self.brand_recommend_list()

        brand_id = self.pool.random_brand_id()
        with self.client.get(
                f"/brand/detail/{brand_id}",
                name="BROWSE_brandDetail",
                catch_response=True,
                timeout=Config.REQUEST_TIMEOUT,
        ) as resp:
            ok, reason = AssertionPolicy.check("BROWSE_brandDetail", resp)
            if ok:
                resp.success()
            else:
                resp.failure(reason)
        self.interrupt(reschedule=False)
