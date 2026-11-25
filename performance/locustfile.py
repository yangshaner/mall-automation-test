# locustfile.py
import logging
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from locust import HttpUser, events, between

from performance.config import Config
from performance.common.session import precheck
from performance.common.auth import AutoAuthSession

from performance.tasks.browse import BrowseTaskSet
from performance.tasks.cart import CartTaskSet
from performance.tasks.trade import TradeTaskSet
import performance.metrics.collector
from performance.orchestration.collectors import start_middleware_collector, stop_middleware_collector

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s -%(name)s %(message)s")


class MallUser(HttpUser):
    host = Config.HOST

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = AutoAuthSession(
            base_url=self.host,
            request_event=self.environment.events.request,
            user=self,
            pool_manager=self.pool_manager,
        )
        self.client.trust_env = False

    wait_time = between(*Config.WAIT_BROWSE)

    tasks = {
        BrowseTaskSet: Config.RATIO_BROWSE,
        CartTaskSet: Config.RATIO_ADD_CART,
        TradeTaskSet: Config.RATIO_TRADE,
    }


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    if Config.ENABLE_MIDDLEWARE_COLLECTOR:
        logging.info("[LIFECYCLE] pressure test starting, middleware collector on.")
        start_middleware_collector()
    else:
        logging.info("[LIFECYCLE] pressure test starting, middleware collector disabled.")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    logging.info("[LIFECYCLE] pressure test stopping, middleware collector off.")
    stop_middleware_collector()

    from performance.metrics.collector import get_collector
    get_collector().flush()

    try:
        from performance.analysis.align import build_aligned_report
        build_aligned_report()
    except Exception as e:
        logging.warning(f"auto-alignment report failed (run `python -m performance.analysis.align` manually): {e}")
