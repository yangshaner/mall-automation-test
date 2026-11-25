from typing import Callable, Optional, Any, Dict, List
import time
import allure
import logging

logger = logging.getLogger(__name__)

class ModuleFieldConfig:
    CONFIGS = {
        'brand': {
            'name_field': 'name',
            'id_field': 'id',
            'keyword_field': 'keyword',
            'list_method_name': 'list',
            'description': 'Brand management',
            'support_pagination': True
        },
        'category': {
            'name_field': 'name',
            'id_field': 'id',
            'keyword_field': None,
            'list_method_name': 'list',
            'requires_parent_id': True,
            'description': 'Product category',
            'support_pagination': True,
            'max_page_size': 100
        },
        'product': {
            'name_field': 'name',
            'id_field': 'id',
            'keyword_field': 'keyword',
            'list_method_name': 'simple_list',
            'description': 'Product management',
            'support_pagination': True
        },
        'coupon': {
            'name_field': 'name',
            'id_field': 'id',
            'keyword_field': 'name',
            'list_method_name': 'list',
            'description': 'Coupon management',
            'support_pagination': True
        },
        'admin': {
            'name_field': 'username',
            'id_field': 'id',
            'keyword_field': 'keyword',
            'list_method_name': 'list',
            'description': 'Admin user management',
            'support_pagination': True
        },
        'order': {
            'name_field': 'orderSn',
            'id_field': 'id',
            'keyword_field': 'orderSn',
            'list_method_name': 'list',
            'description': 'Order management',
            'support_pagination': True
        },
        'flash': {
            'name_field': 'title',
            'id_field': 'id',
            'keyword_field': 'keyword',
            'list_method_name': 'list',
            'description': 'Flash promotion',
            'support_pagination': True
        },
        'flash_session': {
            'name_field': 'name',
            'id_field': 'id',
            'keyword_field': None,
            'list_method_name': 'list',
            'description': 'Flash promotion session',
            'support_pagination': True
        }
    }

    @classmethod
    def get_config(cls, module: str) -> Dict:
        return cls.CONFIGS.get(module, {
            'name_field': 'name',
            'id_field': 'id',
            'keyword_field': 'keyword',
            'list_method_name': 'list',
            'description': 'Unknown module',
            'support_pagination': True
        })

    @classmethod
    def list_module(cls) -> List[str]:
        return list(cls.CONFIGS.keys())


class IdFetcher:

    @staticmethod
    def _extract_items(data: Any) -> List[Dict]:
        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            for field in ['list', 'records', 'items', 'data', 'rows', 'content']:
                if field in data and isinstance(data[field], list):
                    return data[field]
            if data.get('id') is not None:
                return [data]

        return []

    @staticmethod
    def _find_in_tree(items: List[Dict], name: str, name_filed: str = 'name') -> Optional[Dict]:
        for item in items:
            if str(item.get(name_filed)) == str(name):
                return item
            if 'children' in item and isinstance(item['children'], list):
                found = IdFetcher._find_in_tree(item['children'], name, name_filed)
                if found:
                    return found

        return None

    @staticmethod
    def _get_total_from_response(data: Dict) -> int:
        for field in ['total', 'total', 'totalRecords', 'count']:
            if field in data:
                return int(data[field])
        return 0


    @staticmethod
    def _traverse_all_pages(
        list_method: Callable,
        name: str,
        name_field: str,
        id_field: str,
        page_size: int = 10,
        extra_match: bool = True,
        max_pages: int = 100,
        extra_params: Dict = None
    ) -> Optional[int]:
        page_num = 1
        total_checked = 0

        while page_num <= max_pages:
            try:
                params = {"page_num": page_num, "page_size": page_size}
                if extra_params:
                    params.update(extra_params)

                response = list_method(**params)

                if response.status_code != 200:
                    logger.warning(f"Failed to traverse page {page_num}: {response.status_code}")
                    break

                data = response.json().get('data', {})
                items = IdFetcher._extract_items(data)

                if not items:
                    break

                total_checked += len(items)
                print(f"total_checked: {total_checked}")
                logger.debug(f"Traversing page {page_num}, {len(items)} items, {total_checked} checked in total")

                for item in items:
                    item_name = str(item.get(name_field, ''))
                    search_name = str(name)

                    if extra_match:
                        if item_name == search_name:
                            logger.info(f"Found record on page {page_num}: {item_name}, ID:{item.get(id_field)}")
                            return item.get(id_field)
                    else:
                        if search_name in item_name:
                            logger.info(f"Found record on page {page_num}: {item_name}, ID: {item.get(id_field)}")
                            return item.get(id_field)

                total = IdFetcher._get_total_from_response(data)
                if total > 0 and page_num * page_size >= total:
                    print("All data traversed")
                    logger.debug(f"All data traversed, {total} records in total")
                    break

                if len(items) < page_size:
                    print("This is already the last page")
                    break

                page_num += 1

            except Exception as e:
                logger.error(f"Failed to traverse page {page_num}: {e}")
                break

        return None


    @staticmethod
    def get_id_by_name(
            list_method: Callable,
            name: str,
            name_field: str = 'name',
            id_field: str = 'id',
            keyword_field: str = 'keyword',
            page_size: int = 10,
            max_retries: int = 3,
            retry_delay: float = 0.5,
            extra_match: bool = True,
            max_pages: int = 100,
            **kwargs
    ) -> Optional[int]:
        for attempt in range(max_retries):
            try:
                params = {}

                if keyword_field:
                    params[keyword_field] = name

                    params['page_num'] = 1
                    params['page_size'] = page_size


                    params.update(kwargs)
                    logger.debug(f"Query params: {params}")
                    print(f"Query params: {params}")

                    response = list_method(**params)

                    if response.status_code != 200:
                        logger.warning(f"List query failed: {response.status_code}, attempt {attempt + 1}/{max_retries}")

                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            continue
                        return None

                    data = response.json().get('data', {})

                    items = IdFetcher._extract_items(data)

                    for item in items:
                        item_name = str(item.get(name_field, ''))
                        search_name = str(name)

                        if extra_match:
                            if item_name == search_name:
                                return item.get(id_field)
                        else:
                            if search_name in item_name:
                                return item.get(id_field)

                result = IdFetcher._traverse_all_pages(
                    list_method=list_method,
                    name=name,
                    name_field=name_field,
                    id_field=id_field,
                    page_size=page_size,
                    extra_match=extra_match,
                    max_pages=max_pages
                )

                if result is not None:
                    return result

                if attempt < max_retries - 1:
                    logger.debug(f"Record not found: '{name}', retrying {attempt + 1}/{max_retries}")
                    time.sleep(retry_delay)

            except TypeError as e:
                if 'unexpected keyword argument' or 'page_num' or 'page_size' in str(e):
                    logger.warning(f"Parameter error: {e}, trying without pagination parameters")
                    try:
                        params = {}
                        if keyword_field:
                            params[keyword_field] = name
                        params.update(kwargs)
                        response = list_method(**kwargs)

                        if response.status_code == 200:
                            data = response.json().get('data', {})
                            items = IdFetcher._extract_items(data)
                            for item in items:
                                if str(item.get(name_field, '')) == str(name):
                                    return item.get(id_field)
                    except Exception as e2:
                        logger.error(f"Also failed without pagination parameters: {e2}")

                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                raise e

            except Exception as e:
                logger.error(f"Failed to get ID: {e}, attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                raise e

        return None

    @staticmethod
    def get_id_by_field(
            api_instance: Any,
            list_method: Callable,
            field_value: Any,
            field_name: str,
            id_field: str = 'id',
            page_size: int = 50,
            max_retries: int = 3,
            retry_delay: float = 0.5,
    ) -> Optional[int]:
        for attempt in range(max_retries):
            try:
                params = {field_name: field_value, "pageSize": page_size, "pageNum": 1}
                params.update(params)

                response = list_method(**params)

                if response.status_code == 200:
                    data = response.json().get('data', {})
                    items = IdFetcher._extract_items(data)

                    for item in items:
                        if str(item.get(field_name)) == str(field_value):
                            return item.get(id_field)

                result = IdFetcher._traverse_all_pages(
                    list_method=list_method,
                    name=str(field_value),
                    name_field=field_name,
                    id_field=id_field,
                    page_size=page_size,
                    extra_match=True
                )

                if result is not None:
                    return result

                if attempt < max_retries - 1:
                    time.sleep(retry_delay)

            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                raise e

        return None

    @staticmethod
    def get_latest_id(
            list_method: Callable,
            id_field: str = 'id',
            page_size: int = 1,
            **kwargs
    ) -> Optional[int]:
        params = {'pageSize': page_size, 'pageNum': 1}
        params.update(kwargs)

        try:
            response = list_method(**params)
        except TypeError:
            response = list_method(**kwargs)

        if response.status_code != 200:
            return None

        data = response.json().get('data', {})
        items = IdFetcher._extract_items(data)

        if items:
            sorted_items = sorted(items, key=lambda x: x.get(id_field, 0), reverse=True)
            return sorted_items[0].get(id_field)

        return None


    @staticmethod
    def get_category_id_by_name(category_api, name: str, parent_id: int = 0) -> Optional[int]:
        try:
            response = category_api.list(parent_id=parent_id, page_num=1, page_size=100)
            if response.status_code != 200:
                logger.warning(f"Failed to get category list: {response.status_code}")
                return None

            data = response.json().get('data', {})
            items = IdFetcher._extract_items(data)
            print(f"data-itemsxxx:{items}")

            for category in items:
                print(f"{category['name']} xxxxxxx {name}")
                if category.get('name') == name:
                    print(f"find {name} {category.get('name')} id: {category.get('id')}")
                    return category.get('id')

            for category in items:
                if 'children' in category and isinstance(category['children'], list):
                    result = IdFetcher._find_in_tree(category['children'], name)
                    if result:
                        return result.get('id')

            return None
        except Exception as e:
            logger.error(f"Failed to get category ID: {e}")
            return None


    @staticmethod
    def get_id_by_module(
            api_instance: Any,
            module: str,
            search_value: str,
            **kwargs
    ) -> Optional[int]:
        config = ModuleFieldConfig.get_config(module)

        list_method_name = kwargs.get('list_method_name', config.get('list_method_name', 'list'))
        list_method = getattr(api_instance, list_method_name, None)

        if list_method is None:
            raise ValueError(f"API instance has no '{list_method_name}' method")

        name_field = kwargs.get('name_field', config.get('name_field', 'name'))
        id_field = kwargs.get('id_field', config.get('id_field', 'id'))
        keyword_field = kwargs.get('keyword_field', config.get('keyword_field', 'keyword'))

        extra_params = kwargs.get('extra_params', {})

        if keyword_field is None:
            return IdFetcher._traverse_all_pages(
                list_method=list_method,
                name=search_value,
                name_field=name_field,
                id_field=id_field,
                page_size=kwargs.get('page_size',  10),
                extra_match=kwargs.get('extra_match', True),
                max_pages=kwargs.get('max_pages', 100),
                extra_params=extra_params
            )

        return IdFetcher.get_id_by_name(
            api_instance=api_instance,
            list_method=list_method,
            name=search_value,
            name_field=name_field,
            id_field=id_field,
            keyword_field=keyword_field,
            page_size=kwargs.get('page_size', 10),
            max_retries=kwargs.get('max_retries', 3),
            retry_delay=kwargs.get('retry_delay', 5),
            extra_match=kwargs.get('extra_match', True),
            max_pages=kwargs.get('max_pages', 100)
        )


    @staticmethod
    def _get_category_id_by_name(category_api, name: str, **kwargs) -> Optional[int]:
        try:
            parent_id = kwargs.get('parent_id', 0)
            response = category_api.list(parent_id=parent_id, page_num=1, page_size=100)
            if response.status_code != 200:
                return None

            data = response.json().get('data', {})
            items = IdFetcher._extract_items(data)

            for category in items:
                if category.get('name') == name:
                    return category.get('id')

                if 'children' in category:
                    for child in category['children']:
                        if child.get('name') == name:
                            return child.get('id')

            return None
        except Exception as e:
            logger.error(f"Failed to get category ID: {e}")
            return None

    @staticmethod
    def _get_flash_session_id_by_name(flash_session_api, name: str) -> Optional[int]:
        try:
            response = flash_session_api.list()
            if response.status_code != 200:
                return None

            data = response.json().get('data', [])
            items = IdFetcher._extract_items(data)

            for session in items:
                if session.get('name') == name:
                    return session.get('id')

            return None
        except Exception as e:
            logger.error(f"Failed to get session ID: {e}")
            return None

    @staticmethod
    def _get_id_by_traverse(
            api_instance: Any,
            list_method: Callable,
            search_value: str,
            name_field: str,
            id_field: str,
            page_size: int = 100,
            **kwargs
    ) -> Optional[int]:
        page_num = 1
        while True:
            try:
                params = {}

                params.update(kwargs)

                try:
                    response = list_method(**params)
                except TypeError:
                    response = list_method(**kwargs)
                    if response.status_code == 200:
                        data = response.json().get('data', {})
                        itmes = IdFetcher._extract_items(data)
                        for item in itmes:
                            if str(item.get(name_field)) == str(search_value):
                                return item.get(id_field)
                    break

                if response.status_code != 200:
                    break

                data = response.json().get('data', {})
                items = IdFetcher._extract_items(data)

                for item in items:
                    if str(item.get(name_field)) == str(search_value):
                        return item.get(id_field)

                total = data.get('total', 0)
                if page_num * page_size >= total:
                    break

                page_num += 1

            except Exception as e:
                logger.error(f"Failed to get ID by traversal: {e}")
                break

        return None


class IDFetcherWithAllure:

    @staticmethod
    @allure.step("Get record ID by name")
    def get_id_by_name(
            api_instance: Any,
            list_method: Callable,
            name: str,
            name_field: str = 'name',
            id_field: str = 'id',
            keyword_field: str = 'keyword',
            page_size: int = 50,
            max_retries: int = 3,
            retry_delay: float = 0.5,
            extra_match: bool = True,
            max_pages: int = 100
    ) -> Optional[int]:
        allure.attach(
            f"Search name: {name}\n"
            f"Name field: {name_field}\n"
            f"Keyword field: {keyword_field}\n"
            f"Exact match: {extra_match}"
            f"Max pages: {max_pages}",
            name="ID lookup parameters",
            attachment_type=allure.attachment_type.TEXT
        )

        result = IdFetcher.get_id_by_name(
            api_instance, list_method, name,
            name_field, id_field, keyword_field,
            page_size, max_retries, retry_delay, extra_match, max_pages
        )

        allure.attach(
            f"Found ID: {result}" if result else "Record not found",
            name="ID lookup result",
            attachment_type=allure.attachment_type.TEXT
        )

        return result

    @staticmethod
    @allure.step("Get ID automatically by module")
    def get_id_by_module(
            api_instance: Any,
            module: str,
            search_value: str,
            **kwargs
    ) -> Optional[int]:
        config = ModuleFieldConfig.get_config(module)
        allure.attach(
            f"Module: {module}\n"
            f"Description: {config.get('description', '')}\n"
            f"Search value: {search_value}",
            name="Module ID lookup parameters",
            attachment_type=allure.attachment_type.TEXT
        )

        result = IdFetcher.get_id_by_module(api_instance, module, search_value, **kwargs)


        allure.attach(
            f"Found ID: {result}" if result else "Record not found",
            name="Module ID lookup result",
            attachment_type=allure.attachment_type.TEXT
        )

        return result
