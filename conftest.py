# confest.py

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

pytest_plugins = [
    'api.fixtures.product_fixtures',
    'api.fixtures.admin_fixtures',
    'api.fixtures.member_fixtures',
    'api.fixtures.data_fixtures'
]


def pytest_configure(config):

    report_dir = Path(__file__).parent / "reports"
    report_dir.mkdir(exist_ok=True)
    (report_dir / "allure-results").mkdir(exist_ok=True)

    config.addinivalue_line("markers", "smoke: Smoke testing")
    config.addinivalue_line("markers", "regression: Regression testing")
    config.addinivalue_line("markers", "admin: Backend management test")
    config.addinivalue_line("markers", "member: Front-end user testing")
    config.addinivalue_line("markers", "product: Product management testing")
    config.addinivalue_line("markers", "order: Order management testing")

    @pytest.fixture(scope="session", autouse=True)
    def test_session_setup():
        print("\n" + "=" * 30)
        print("Mall API Test Framework Started")
        print("=" * 30)
        yield
        print("\n" + "=" * 30)
        print("Mall API Test Framework Finished")
        print("=" * 30)
