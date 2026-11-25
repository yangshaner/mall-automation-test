import os

_ROOT = os.path.dirname(os.path.abspath(__file__))


class Config:
    HOST = os.getenv("HOST", "http://127.0.0.1:8085")

    LOGIN_ENDPOINT = os.getenv("LOGIN_ENDPOINT", "/sso/login")

    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASS = os.getenv("MYSQL_PASS", "")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    REDIS_ADDR = os.getenv("REDIS_ADDR", "127.0.0.1:6379")

    ENABLE_MIDDLEWARE_COLLECTOR = os.getenv("ENABLE_MIDDLEWARE_COLLECTOR", "1") == "1"

    RATIO_BROWSE = int(os.getenv("RATIO_BROWSE", "70"))
    RATIO_ADD_CART = int(os.getenv("RATIO_ADD_CART", "15"))
    RATIO_TRADE = int(os.getenv("RATIO_TRADE", "15"))

    RATIO_PRODUCT = int(os.getenv("RATIO_PRODUCT", "0"))

    RATIO_BROWSE_BRAND_PRODUCT_LIST = 50
    RATIO_BROWSE_BRAND_RECOMMEND_LIST = 20
    RATIO_BROWSE_BRAND_DETAIL = 30

    RATIO_PRODUCT_LIST = 50
    RATIO_PRODUCT_DETAIL = 50

    WAIT_BROWSE = (1, 3)
    WAIT_TRADE = (2, 5)

    USERS_CSV = os.path.join(_ROOT, "data", "users.csv")
    PRODUCTS_CSV = os.path.join(_ROOT, "data", "products.csv")
    BRANDS_CSV = os.path.join(_ROOT, "data", "brands.csv")

    SUCCESS_CODE = 200
    REQUEST_TIMEOUT = 10

    COUPON_ID = os.getenv("COUPON_ID", "")
    USE_INTEGRATION = int(os.getenv("USE_INTEGRATION", "0"))

    ISOLATE_ORDER = os.getenv("ISOLATE_ORDER", "1") == "1"
