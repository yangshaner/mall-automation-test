# fixtures/member_fixtures.py
import pytest
import allure
import requests
from requests.adapters import HTTPAdapter

from api.objects.member.return_api import ReturnApi
from api.objects.member.login_api import MemberLoginApi
from api.objects.member.product_api import MemberProductApi
from api.objects.member.cart_api import CartApi
from api.objects.member.order_api import MemberOrderApi
from api.objects.member.coupon_api import MemberCouponApi
from api.objects.member.address_api import AddressApi
from api.objects.member.collection_api import CollectionApi
from api.objects.member.attention_api import AttentionApi
from api.objects.member.read_history_api import ReadHistoryApi
from api.objects.member.home_api import HomeApi
from api.objects.member.brand_api import MemberBrandApi
from common.assertions import ApiAssertion, DBAssertion
from common.db.mysql_util import mysql
from common.client.member_client import MemberClient
from common.config.config_loader import config
from common.utils.data_generator import DataGenerator
from api.fixtures.product_fixtures import test_product, test_brand


@pytest.fixture(scope="session")
def member_client():
    client = MemberClient()
    client._login()
    return client


@pytest.fixture(scope="session")
def member_client_unauthenticated():
    return MemberClient()


@pytest.fixture(scope="session")
def member_credentials():
    account = config.get("member", {})
    return {
        "username": account["username"],
        "password": account["password"]
    }


@pytest.fixture(scope="session")
def member_login_api(member_client):
    return MemberLoginApi(member_client)


@pytest.fixture(scope="session")
def member_login_api_unauthenticated(member_client_unauthenticated):
    return MemberLoginApi(member_client_unauthenticated)


@pytest.fixture(scope="session")
def member_product_api(member_client):
    return MemberProductApi(member_client)


@pytest.fixture(scope="session")
def member_brand_api(member_client):
    return MemberBrandApi(member_client)


@pytest.fixture(scope="session")
def cart_api(member_client):
    return CartApi(member_client)


@pytest.fixture(scope="session")
def member_order_api(member_client):
    return MemberOrderApi(member_client)


@pytest.fixture(scope="session")
def member_coupon_api(member_client):
    return MemberCouponApi(member_client)


@pytest.fixture(scope="session")
def address_api(member_client):
    return AddressApi(member_client)


@pytest.fixture(scope="session")
def collection_api(member_client):
    return CollectionApi(member_client)


@pytest.fixture(scope="session")
def collection_available(member_client):
    probe = requests.Session()
    probe.mount("http://", HTTPAdapter(max_retries=0))
    probe.mount("https://", HTTPAdapter(max_retries=0))
    auth = member_client.session.headers.get("Authorization", "")
    if auth:
        probe.headers["Authorization"] = auth
    try:
        resp = probe.get(
            f"{member_client.base_url}/member/productCollection/list",
            params={"pageNum": 1, "pageSize": 1},
            timeout=(3, 6)
        )
        body = resp.json()
        return resp.status_code == 200 and body.get("code") == 200
    except requests.exceptions.RequestException:
        return False
    except ValueError:
        return False
    finally:
        probe.close()


@pytest.fixture(scope="session")
def attention_api(member_client):
    return AttentionApi(member_client)


@pytest.fixture(scope="session")
def read_history_api(member_client):
    return ReadHistoryApi(member_client)


@pytest.fixture(scope="session")
def home_api(member_client):
    return HomeApi(member_client)


@pytest.fixture(scope="session")
def retune_api(member_client):
    return ReturnApi(member_client)


@pytest.fixture(scope="session")
def data_generator():
    return DataGenerator()


@pytest.fixture(scope="session")
def api_assert():
    return ApiAssertion()


@pytest.fixture(scope="session")
def db_assert():
    return DBAssertion()


@pytest.fixture(scope="session")
def test_member_address(address_api, data_generator, db_assert):
    with allure.step("Create test shipping address"):
        data = {
            "name": data_generator.random_name(),
            "phoneNumber": data_generator.random_phone(),
            "province": "guangdongsheng",
            "city": "shenzhenshi",
            "region": "nanshanqu",
            "detailAddress": f"testAddress_{data_generator.random_string(4)}",
            "defaultStatus": 1
        }
        response = address_api.add(data)
        assert response.status_code == 200
        result = response.json()
        address_id = result.get('data', {}).get('id')
        assert address_id, "Failed to create shipping address"

        allure.attach(str(address_id), "Address ID", allure.attachment_type.TEXT)
        yield address_id

    with allure.step("Clean up test shipping address"):
        try:
            address_id.delete(address_id)
        except Exception as e:
            allure.attach(str(e), "Cleanup failed", allure.attachment_type.TEXT)


@pytest.fixture
def test_cart_item(cart_api, test_product):
    with allure.step("Add product to cart"):
        sku_rows = mysql.query(
            "SELECT id, price FROM pms_sku_stock WHERE product_id = %s AND stock > 0 ORDER BY id LIMIT 1",
            (test_product,)
        )
        assert sku_rows, f"Product {test_product} has no available SKU (no stock record in pms_sku_stock)"
        sku_id = sku_rows[0]["id"]
        price = float(sku_rows[0]["price"] or 99.99)

        data = {
            "productId": test_product,
            "productSkuId": sku_id,
            "quantity": 1,
            "price": price
        }
        response = cart_api.add(data)
        assert response.status_code == 200, f"Failed to add to cart (HTTP level): {response.text}"
        add_result = response.json()
        assert add_result.get("code") == 200, f"Failed to add to cart (business layer): {add_result.get('message')}"


        list_response = cart_api.list()
        assert list_response.status_code == 200
        list_result = list_response.json()
        assert list_result.get('code') == 200, f"Failed to get cart list: {list_result.get('message')}"

        list_data = list_result.get('data')
        if not isinstance(list_data, list):
            raise TypeError(f"Cart list data should be a list, got {type(list_data)}: {list_data})")

        cart_item = next((item for item in list_data if item.get("productId") == test_product), None)
        assert cart_item, "Cart item was not added successfully"

        cart_id = cart_item.get('id')
        allure.attach(str(cart_id), "Cart Item ID", allure.attachment_type.TEXT)

        yield cart_id

    with allure.step("Clean up cart"):
        try:
            cart_api.clear()
        except Exception as e:
            allure.attach(str(e), "Cleanup failed", allure.attachment_type.TEXT)


SEED_PRODUCT_ID = 26


@pytest.fixture
def seed_cart_item(cart_api):
    sku_rows = mysql.query(
        "SELECT id, price FROM pms_sku_stock WHERE product_id = %s AND stock > 0 ORDER BY id LIMIT 1",
        (SEED_PRODUCT_ID,)
    )
    if not sku_rows:
        pytest.skip(f"Seed product {SEED_PRODUCT_ID} has no available SKU, skipping promotion-related flows")

    sku_id = sku_rows[0]["id"]
    price = float(sku_rows[0]["price"] or 0)
    response = cart_api.add({
        "productId": SEED_PRODUCT_ID,
        "productSkuId": sku_id,
        "quantity": 1,
        "price": price
    })
    result = response.json()
    assert response.status_code == 200 and result.get("code") == 200, \
        f"Failed to add seed product to cart: {result.get('message')}"

    list_result = cart_api.list().json()
    list_data = list_result.get("data") or []
    cart_item = next(
        (it for it in list_data if isinstance(it, dict) and it.get("productId") == SEED_PRODUCT_ID),
        None
    )
    assert cart_item, "Seed product cart item not found"
    yield cart_item["id"]

    try:
        cart_api.clear()
    except Exception:
        pass


@pytest.fixture
def test_member_order(member_order_api, seed_cart_item, test_member_address):
    with allure.step("Generate test order"):
        conforms_response = member_order_api.generate_confirm_order([seed_cart_item])
        confirm_result = conforms_response.json()
        assert conforms_response.status_code == 200 and confirm_result.get("code") == 200, \
            f"Failed to generate confirm order: HTTP {conforms_response.status_code}, {str(confirm_result)[:200]}"

        order_data = {
            "memberReceiverAddressId": test_member_address,
            "couponId": None,
            "useIntegration": 0,
            "payType": 1,
            "cartIds": [seed_cart_item]
        }
        response = member_order_api.generate_order(order_data)
        assert response.status_code == 200
        result = response.json()
        assert result.get("code") == 200, \
            f"Failed to create order (business layer): {result.get('message')}, data={str(result.get('data'))[:200]}"
        order_data_resp = result.get("data")
        assert isinstance(order_data_resp, dict), f"Unexpected data type returned by order creation: {type(order_data_resp).__name__}"
        order_id = order_data_resp.get("id")
        assert order_id, "Failed to create order, no order ID returned"

        allure.attach(str(order_id), "Order ID", allure.attachment_type.TEXT)
        yield order_id

    with allure.step("Clean up test order"):
        try:
            member_order_api.delete_order(order_id)
        except Exception as e:
            allure.attach(str(e), "Cleanup failed", allure.attachment_type.TEXT)


@pytest.fixture
def test_read_history(read_history_api, test_product, data_generator):
    with allure.step("Create test browse history"):
        data = {
            "productId": test_product,
            "productName": f"testProduct_{data_generator.random_string(4)}",
            "productPic": "test.png",
            "productPrice": "99.99"
        }
        response = read_history_api.create(data)
        assert response.status_code == 200
        result = response.json()
        assert result.get("code") == 200, f"Failed to create browse history: {result.get('message')}"
        history_data = result.get("data")
        history_id = history_data.get("id") if isinstance(history_data, dict) else None

        allure.attach(str(history_id), "History ID", allure.attachment_type.TEXT)
        yield history_id

    with allure.step("Clean up test browse history"):
        try:
            if history_id:
                read_history_api.delete([history_id])
        except Exception as e:
            allure.attach(str(e), "Cleanup failed", allure.attachment_type.TEXT)


@pytest.fixture
def test_collection(collection_api, collection_available, test_product, data_generator):
    if not collection_available:
        pytest.skip("Collection API unavailable (server timeout / missing collection table), skipping collection write operations")

    with allure.step("Create test collection"):
        data = {
            "productId": test_product,
            "productName": f"testProduct_{data_generator.random_string(4)}",
            "productPic": "test.png",
            "productPrice": "99.99"
        }
        response = collection_api.add(data)
        assert response.status_code == 200
        allure.attach(str(test_product), "Collection Product ID", allure.attachment_type.TEXT)
        yield test_product

    with allure.step("Clean up test collection"):
        try:
            collection_api.delete(test_product)
        except Exception as e:
            allure.attach(str(e), "Cleanup failed", allure.attachment_type.TEXT)


@pytest.fixture
def test_attention(attention_api, test_brand, data_generator, member_client):
    with allure.step("Create test attention"):
        brand_api = MemberBrandApi(member_client)
        brand_response = brand_api.detail(test_brand)
        brand_result = brand_response.json()
        brand_data = brand_result.get("data", {})

        data = {
            "brandId": test_brand,
            "brandName": brand_data.get('name', f'testBrand_{data_generator.random_string(4)}'),
            "brandLogo": "logo.png",
        }
        response = attention_api.create(data)
        assert response.status_code == 200
        result = response.json()
        attention_id = result.get("data", {}).get("id")

        allure.attach(str(attention_id), "Attention ID", allure.attachment_type.TEXT)
        yield attention_id

    with allure.step("Clean up test attention"):
        try:
            attention_api.delete(test_brand)
        except Exception as e:
            allure.attach(str(e), "Cleanup failed", allure.attachment_type.TEXT)
