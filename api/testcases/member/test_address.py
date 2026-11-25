# testcases/member/test_address.py
import allure


@allure.feature("Frontend Address Management")
class TestAddress:

    @allure.story("Address CRUD")
    def test_address_crud(self, address_api, data_generator, api_assert):
        suffix = data_generator.random_string(6)
        address_data = {
            "name": data_generator.random_name(),
            "phoneNumber": data_generator.random_phone(),
            "province": "guangdongsheng",
            "city": "shenzhenshi",
            "region": "nanshanqu",
            "detailAddress": f"testAddress_{suffix}",
            "defaultStatus": 0
        }
        address_id = None

        try:
            with allure.step("Create shipping address"):
                response = address_api.add(address_data)
                address_id = api_assert.assert_create_success(
                    response, message="Failed to create shipping address"
                )

            with allure.step("Get shipping address detail"):
                response = address_api.detail(address_id)
                detail = api_assert.assert_object_response(
                    response,
                    required_fields=["id", "name", "phoneNumber", "detailAddress"],
                    message="Failed to get shipping address detail"
                )
                assert detail["id"] == address_id
                assert detail["name"] == address_data["name"]
                assert detail["phoneNumber"] == address_data["phoneNumber"]
                assert detail["detailAddress"] == address_data["detailAddress"]

            with allure.step("Update shipping address"):
                updated_detail = f"updatedAddress_{suffix}"
                updated_data = {**address_data, "detailAddress": updated_detail}
                response = address_api.update(address_id, updated_data)
                api_assert.assert_success(response, "Failed to update shipping address")

                response = address_api.detail(address_id)
                detail = api_assert.assert_object_response(
                    response, message="Failed to get updated shipping address"
                )
                assert detail["detailAddress"] == updated_detail

            with allure.step("Delete shipping address"):
                response = address_api.delete(address_id)
                api_assert.assert_success(response, "Failed to delete shipping address")

            with allure.step("Verify shipping address deletion"):
                response = address_api.list()
                addresses = api_assert.assert_list_response(
                    response, message="Failed to get shipping address list"
                )
                assert all(item.get("id") != address_id for item in addresses), \
                    "Deleted shipping address still exists in the address list"
                address_id = None
        finally:
            if address_id is not None:
                address_api.delete(address_id)
