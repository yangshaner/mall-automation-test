# tasks/order.py
import logging
import time

from locust.exception import CatchResponseError

from performance.config import Config
from performance.common.assertion_policy import AssertionPolicy

logger = logging.getLogger(__name__)

NAME_ADDRESS_LIST = "TRADE_addressList"
NAME_GENERATE_ORDER = "TRADE_generateOrder"
NAME_PROBE_ORDER_AUTH = "PROBE_generateOrder_auth"


def _biz_code(resp):
    try:
        return resp.json().get("code")
    except Exception:
        return None


def _fire_probe(client, resp, reason):
    try:
        elapsed_ms = resp.elapsed.total_seconds() * 1000
    except Exception:
        elapsed_ms = 0
    client.request_event.fire(
        request_type="PROBE",
        name=NAME_PROBE_ORDER_AUTH,
        response_time=elapsed_ms,
        response_length=len(resp.content or b""),
        exception=CatchResponseError(reason),
        context={},
        response=resp,
        start_time=time.time(),
        url=resp.url,
    )


def fetch_default_address(client, headers):
    with client.get(
            "/member/address/list",
            headers=headers,
            name=NAME_ADDRESS_LIST,
            catch_response=True,
            timeout=Config.REQUEST_TIMEOUT,
    ) as resp:
        ok, reason = AssertionPolicy.check(NAME_ADDRESS_LIST, resp)
        if not ok:
            resp.failure(reason)
            return False, None, reason
        resp.success()
        try:
            addresses = resp.json().get("data") or []
        except Exception:
            addresses = []

    addr = next(
        (a for a in addresses if a.get("defaultStatus") == 1),
        addresses[0] if addresses else None,
    )
    return True, addr, ""


def generate_order(client, headers, cart_ids, receiver_id):
    payload = {
        "memberReceiveAddressId": receiver_id,
        "couponId": int(Config.COUPON_ID) if Config.COUPON_ID.strip() else None,
        "useIntegration": Config.USE_INTEGRATION,
        "payType": 1,
        "cartIds": cart_ids,
        "note": "locust-perf-test",
    }
    with client.post(
            "/order/generateOrder",
            json=payload,
            headers=headers,
            name=NAME_GENERATE_ORDER,
            catch_response=True,
            timeout=Config.REQUEST_TIMEOUT,
    ) as resp:
        ok, reason = AssertionPolicy.check(NAME_GENERATE_ORDER, resp)
        if not ok:
            if Config.ISOLATE_ORDER and _biz_code(resp) == 401:
                _fire_probe(client, resp, f"auth-blocked: {reason}")
                resp.success()
                logger.warning(
                    f"[order] generateOrder blocked by server auth (isolated as {NAME_PROBE_ORDER_AUTH}): "
                    f"{reason} | body={resp.text[:200]}"
                )
                return False, None, "generateOrder blocked by server auth (isolated)"

            detail = (
                f"{reason} | url={resp.url} | "
                f"history={[r.status_code for r in resp.history]} | "
                f"body={resp.text[:300]} | payload={payload}"
            )
            logger.warning(f"[order] generateOrder failed: {detail}")
            resp.failure(detail)
            return False, None, detail
        resp.success()
        try:
            order_id = resp.json().get("data")
        except Exception:
            order_id = None
        return True, order_id, ""
