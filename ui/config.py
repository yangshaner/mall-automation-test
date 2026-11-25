# ui/config.py
from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _env_or_yaml(env: str, section: str, key: str, default: str) -> str:
    v = os.getenv(env)
    if v and v.strip():
        return v.strip()
    try:
        import yaml
        cfg = PROJECT_ROOT / "common" / "config" / "config.yml"
        if cfg.exists():
            data = yaml.safe_load(cfg.open(encoding="utf-8")) or {}
            return (data.get("dev", {}) or {}).get(section, {}).get(key) or default
    except Exception:
        pass
    return default



ADMIN_BASE_URL: str = _env_or_yaml(
    "MALL_ADMIN_URL", "admin", "ui_base_url", "http://127.0.0.1:5173"
)
MEMBER_BASE_URL: str = _env_or_yaml(
    "MALL_MEMBER_URL", "member", "ui_base_url", "http://127.0.0.1:5174"
)


ADMIN_API_URL: str = _env_or_yaml(
    "MALL_ADMIN_API_URL", "admin", "base_url", "http://127.0.0.1:8080"
)
MEMBER_API_URL: str = _env_or_yaml(
    "MALL_MEMBER_API_URL", "member", "base_url", "http://127.0.0.1:8085"
)


ADMIN_USERNAME: str = _env_or_yaml("MALL_ADMIN_USER", "admin", "username", "admin")
ADMIN_PASSWORD: str = _env_or_yaml("MALL_ADMIN_PASSWORD", "admin", "password", "macro123")
MEMBER_USERNAME: str = _env_or_yaml("MALL_MEMBER_USER", "member", "username", "demo")
MEMBER_PASSWORD: str = _env_or_yaml("MALL_MEMBER_PASSWORD", "member", "password", "demo1234")


HEADLESS: bool = os.getenv("MALL_UI_HEADLESS", "false").lower() in ("1", "true", "yes")
DEFAULT_TIMEOUT_MS: int = int(os.getenv("MALL_UI_TIMEOUT", "15000"))
VIEWPORT = {"width": 1440, "height": 900}
