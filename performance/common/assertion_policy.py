# common/assertion_policy.py
from performance.config import Config


class AssertionPolicy:

    POLICIES = {
        "AUTH_login": "STRICT",
        "TRADE_addShoppingCart": "STRICT",
        "TRADE_shoppingCartList": "STRICT",
        "TRADE_addressList": "STRICT",
        "TRADE_generateOrder": "STRICT",
        "BROWSE_productSearch": "LENIENT",
        "BROWSE_productDetail": "LENIENT",
        "BROWSE_brandProductList": "LENIENT",
        "BROWSE_recommendBrand": "LENIENT",
        "BROWSE_brandDetail": "LENIENT",
    }

    @classmethod
    def check(cls, api_name, resp):
        level = cls.POLICIES.get(api_name, "LENIENT")
        if level == "NONE":
            return True, ""
        if resp.status_code == 0:
            err = getattr(resp, "error", None)
            if err is None:
                return False, "HTTP_0"
            return False, f"{type(err).__name__}: {err}"
        if resp.status_code != 200:
            return False, f"HTTP_{resp.status_code}"
        if level == "LENIENT":
            return True, ""
        try:
            body = resp.json()
        except Exception:
            return False, f"Non-JSON"
        code = body.get("code")
        if code != Config.SUCCESS_CODE:
            return False, f"BIZ_{code}"
        return True, ""
