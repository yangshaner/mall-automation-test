# common/assertions.py
from performance.config import Config


def assert_business_ok(resp, action_name):
    if resp.status_code != 200:
        return False, f"HTTP {resp.status_code}"

    if not Config.STRICT_ASSERT:
        return True, ""

    try:
        body = resp.json()
    except Exception:
        return False, "Non-JSON response"

    code = body.get("code")
    if code != Config.SUCCESS_CODE:
        return False, f"code={code} msg={body.get('message')}"

    return True, ""
