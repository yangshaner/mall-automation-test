# ui/conftest.py
from __future__ import annotations

import logging
import sys
import tempfile
from pathlib import Path
from typing import Tuple

import pytest
import requests
from playwright.sync_api import BrowserContext, Page, Playwright, TimeoutError as PWTimeout

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ui import config as ui_cfg

logger = logging.getLogger(__name__)

_fail_context: dict = {}



@pytest.fixture(scope="session")
def playwright_instance():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        yield pw


@pytest.fixture(scope="session")
def chromium(playwright_instance: Playwright):
    try:
        browser = playwright_instance.chromium.launch(
            headless=ui_cfg.HEADLESS,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        yield browser
        browser.close()
    except Exception as exc:
        logger.warning("Browser launch failed: %s", exc)
        pytest.skip(f"Browser unavailable: {exc}")



@pytest.fixture()
def context(chromium, request) -> BrowserContext:
    safe_name = request.node.nodeid.replace("::", "__").replace("/", "_").replace("\\", "_")
    reports_dir = Path(__file__).resolve().parent / ".." / "reports"
    reports_dir.mkdir(exist_ok=True)
    trace_path = str(reports_dir / f"trace_{safe_name}.zip")

    ctx = chromium.new_context(viewport=ui_cfg.VIEWPORT)
    ctx.set_default_timeout(ui_cfg.DEFAULT_TIMEOUT_MS)
    ctx.tracing.start(name="trace", screenshots=True, snapshots=True, sources=True)

    _fail_context["trace_path"] = trace_path
    _fail_context["request"] = request

    yield ctx

    try:
        ctx.tracing.stop(path=trace_path)
    except Exception:
        pass
    ctx.close()


@pytest.fixture()
def page(context: BrowserContext) -> Page:
    p = context.new_page()

    _fail_context["console_logs"] = []
    _fail_context["page"] = p

    def _on_console(msg):
        _fail_context.setdefault("console_logs", []).append(
            f"[{msg.type}] {msg.text}"
        )

    p.on("console", _on_console)
    p.on("pageerror", lambda exc: _fail_context.setdefault("page_errors", []).append(str(exc)))

    try:
        yield p
    finally:
        page_to_close = _fail_context.get("page")
        if page_to_close and not page_to_close.is_closed():
            try:
                page_to_close.close()
            except Exception:
                pass



def _api_login(api_url: str, username: str, password: str) -> bool:
    try:
        r = requests.post(
            f"{api_url}/sso/login",
            params={"username": username, "password": password},
            timeout=10,
        )
        if r.status_code != 200:
            return False
        body = r.json()
        return body.get("code") == 200 and isinstance((body.get("data") or {}).get("token"), str)
    except Exception:
        return False


def _api_token(api_url: str, username: str, password: str) -> str:
    try:
        r = requests.post(
            f"{api_url}/sso/login",
            params={"username": username, "password": password},
            timeout=10,
        )
        return (r.json().get("data") or {}).get("token", "")
    except Exception:
        return ""


def _frontend_reachable(base_url: str) -> bool:
    try:
        r = requests.get(f"{base_url}/", timeout=10)
        return r.status_code == 200 and "<!doctype html" in r.text.lower()[:500]
    except Exception:
        return False


def _domain_of(url: str) -> str:
    return url.split("/")[2].split(":")[0]



@pytest.fixture()
def admin_page(context: BrowserContext, page: Page) -> Tuple[Page, bool]:
    api_url = ui_cfg.ADMIN_API_URL
    spa_url = ui_cfg.ADMIN_BASE_URL

    api_ok = _api_login(api_url, ui_cfg.ADMIN_USERNAME, ui_cfg.ADMIN_PASSWORD)
    spa_ok = _frontend_reachable(spa_url)
    available = api_ok and spa_ok

    if available:
        token = _api_token(api_url, ui_cfg.ADMIN_USERNAME, ui_cfg.ADMIN_PASSWORD)
        if token:
            domain = _domain_of(spa_url)
            try:
                context.add_cookies([{
                    "name": "token", "value": token,
                    "domain": domain, "path": "/",
                }])
                page.add_init_script(f"localStorage.setItem('token', '{token}');")
            except Exception as exc:
                logger.debug("Skip admin token injection: %s", exc)

    try:
        page.goto(f"{spa_url}/#/", wait_until="networkidle", timeout=30000)
    except PWTimeout:
        available = False
    except Exception:
        available = False

    return page, available


@pytest.fixture()
def member_page(context: BrowserContext, page: Page) -> Tuple[Page, bool]:
    api_url = ui_cfg.MEMBER_API_URL
    spa_url = ui_cfg.MEMBER_BASE_URL

    api_ok = _api_login(api_url, ui_cfg.MEMBER_USERNAME, ui_cfg.MEMBER_PASSWORD)
    spa_ok = _frontend_reachable(spa_url)
    available = api_ok and spa_ok

    if available:
        token = _api_token(api_url, ui_cfg.MEMBER_USERNAME, ui_cfg.MEMBER_PASSWORD)
        if token:
            domain = _domain_of(spa_url)
            try:
                context.add_cookies([{
                    "name": "token", "value": token,
                    "domain": domain, "path": "/",
                }])
                page.add_init_script(f"localStorage.setItem('token', '{token}');")
            except Exception as exc:
                logger.debug("Skip member token injection: %s", exc)

    try:
        page.goto(f"{spa_url}/#/", wait_until="networkidle", timeout=30000)
    except PWTimeout:
        available = False
    except Exception:
        available = False

    return page, available



@pytest.fixture()
def admin_ready(admin_page):
    page, available = admin_page
    if not available:
        pytest.skip("Admin service unreachable, skipping UI test")
    return page


@pytest.fixture()
def member_ready(member_page):
    page, available = member_page
    if not available:
        pytest.skip("Member service unreachable, skipping UI test")
    return page


@pytest.fixture()
def member_page_blank(context: BrowserContext, page: Page) -> Page:
    api_url = ui_cfg.MEMBER_API_URL
    spa_url = ui_cfg.MEMBER_BASE_URL

    api_ok = _api_login(api_url, ui_cfg.MEMBER_USERNAME, ui_cfg.MEMBER_PASSWORD)
    spa_ok = _frontend_reachable(spa_url)

    if not api_ok:
        pytest.skip("Member backend API unreachable, skipping login UI test")
    if not spa_ok:
        pytest.skip("Member frontend SPA unreachable, skipping login UI test")
    return page



@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        _attach_failure_artifacts()
    elif report.when == "setup" and report.failed:
        _attach_failure_artifacts()


def _attach_failure_artifacts() -> None:
    try:
        import allure
    except ImportError:
        return

    page = _fail_context.get("page")
    trace_path = _fail_context.get("trace_path", "")
    console_logs = _fail_context.get("console_logs", [])
    page_errors = _fail_context.get("page_errors", [])

    if page and not page.is_closed():
        try:
            shot = page.screenshot(full_page=True)
            allure.attach(
                shot, name="Failure screenshot (Full Page)",
                attachment_type=allure.attachment_type.PNG,
            )
            try:
                url_info = f"URL: {page.url}\nTitle: {page.title()}"
                allure.attach(
                    url_info, name="Page info at failure",
                    attachment_type=allure.attachment_type.TEXT,
                )
            except Exception:
                pass
        except Exception as exc:
            allure.attach(
                f"Screenshot failed: {exc}", name="Screenshot error",
                attachment_type=allure.attachment_type.TEXT,
            )

    if trace_path and Path(trace_path).exists():
        try:
            allure.attach.file(
                trace_path, name="Playwright Trace (open -> select Playwright format)",
                attachment_type=allure.attachment_type.ZIP,
            )
        except Exception as exc:
            logger.debug("Skip trace attach: %s", exc)

    if console_logs:
        try:
            allure.attach(
                "\n".join(console_logs), name="Browser Console logs",
                attachment_type=allure.attachment_type.TEXT,
            )
        except Exception:
            pass

    if page_errors:
        try:
            allure.attach(
                "\n".join(page_errors), name="Page JS Errors",
                attachment_type=allure.attachment_type.TEXT,
            )
        except Exception:
            pass
