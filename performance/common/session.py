# common/session.py
import os
import sys


from locust import events
import requests

from performance.config import Config
from performance.common.data_loader import get_pool


def _fail(environment, msg):
    print(f"[PRECHECK FAIL] {msg}", file=sys.stderr)
    environment.process_exit_code = 1
    try:
        environment.runner.quit()
    except Exception:
        os._exit(1)


def _warn(msg):
    print(f"[PRECHECK WARN] {msg}", file=sys.stderr)


@events.test_start.add_listener
def precheck(environment, **kwargs):
    try:
        pool = get_pool()
    except Exception as e:
        _fail(environment, f"data pool not ready: {e}")
        return

    print(f"[PRECHECK] data ok: users={len(pool.users)} products={len(pool.products)} brands={len(pool.brands)}")

    if not pool.brands:
        _warn(f"{Config.BRANDS_CSV} missing; brand product/detail tasks will fall back to "
              f"/brand/recommendList.")

    try:
        from performance.orchestration.shape import InstrumentStepShape
        max_users = max(s["users"] for s in InstrumentStepShape.stages)
        if len(pool.users) < max_users:
            _warn(f"users.csv has {len(pool.users)} accounts but peak stage needs {max_users}; "
                  f"accounts will be reused and their tokens will overwrite each other "
                  f"(expect 401 / token expired).")
    except Exception:
        pass

    seen = set()
    dup = set()
    for u in pool.users:
        if u["username"] in seen:
            dup.add(u["username"])
        else:
            seen.add(u["username"])
    if dup:
        _warn(f"duplicated usernames in users.csv ({len(dup)}): {sorted(dup)[:5]}... "
              f"each duplicate makes its token fight the others.")


    account = pool.users[0]

    try:
        r = requests.post(
            Config.HOST + Config.LOGIN_ENDPOINT,
            data={"username": account["username"], "password": account["password"]},
            timeout=Config.REQUEST_TIMEOUT,
        )
    except Exception as e:
        _fail(environment, f"login request threw for {account['username']}: {e}")
        return

    if r.status_code != 200:
        _fail(environment, f"login {account['username']} HTTP {r.status_code}: {r.text[:200]}")
        return
    try:
        body = r.json()
    except Exception:
        _fail(environment, f"login {account['username']} response is not JSON: {r.text[:200]}")
        return
    if body.get("code") != Config.SUCCESS_CODE:
        _fail(environment, f"login {account['username']} biz_code={body.get('code')} msg={body.get('message')}")
        return

    data = body.get("data") or {}
    token = (data.get("token") or "").replace("Bearer ", "").strip()
    if not token:
        _fail(environment, f"login ok but no token field, data={data}")
        return
    print(f"[PRECHECK] login ok for {account['username']}")


    try:
        r = requests.get(
            Config.HOST + "/member/address/list",
            headers={"Authorization": f"Bearer {token}"},
            timeout=Config.REQUEST_TIMEOUT,
        )
    except Exception as e:
        _warn(f"address list request threw: {e}")
        return

    if r.status_code != 200:
        _warn(f"address list HTTP {r.status_code}; trade flows will fail with biz_code=500 "
              f"until addresses are seeded in DB.")

        return
    try:
        addresses = r.json().get("data") or []
    except Exception:
        _warn("address list response is not JSON; trade flows may fail with biz_code=500.")
        return
    if not addresses:
        _warn("member has no delivery address; trade flows will fail with biz_code=500 "
              "until addresses are seeded in ums_member_receive_address.")

        return

    default = next((a for a in addresses if a.get("defaultStatus") == 1), addresses[0])
    print(f"[PRECHECK] address ok, default id={default.get('id')}")
