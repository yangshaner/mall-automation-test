# common/auth.py
import logging
from locust.clients import HttpSession
from performance.config import Config
from performance.common.data_loader import get_pool

logger = logging.getLogger(__name__)


class TokenCache:

    @staticmethod
    def invalidate(user):
        user.token = None

    @staticmethod
    def ensure_token(user):
        if getattr(user, "token", None):
            return user.token

        pool = get_pool()
        if getattr(user, "username", None) and getattr(user, "_password", None):
            account = {"username": user.username, "password": user._password}
        else:
            account = pool.next_user()

        user.username = account["username"]
        user._password = account["password"]

        with user.client.post(
                Config.LOGIN_ENDPOINT,
                data={"username": account["username"], "password": account["password"]},
                name="AUTH_login",
                catch_response=True,
                timeout=Config.REQUEST_TIMEOUT,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"HTTP {resp.status_code}")
                return None
            try:
                body = resp.json()
            except Exception:
                resp.failure("Login response is not JSON.")
                return None

            if body.get("code") != Config.SUCCESS_CODE:
                resp.failure(f"Business failure code={body.get('code')} msg={body.get('message')}")
                return None

            data = body.get("data") or {}
            token = data.get("token")
            if not token:
                token = data.get("tokenHead", "") + (data.get("token") or "")
                token = token.replace("Bearer ", "").strip()

            if not token:
                resp.failure("Login succeeded but token was not obtained.")
                return None

            user.token = token
            user.member_id = data.get("memberId")
            resp.success()

        return user.token

    @staticmethod
    def auth_header(user):
        token = TokenCache.ensure_token(user)
        if not token:
            return None
        return {"Authorization": f"Bearer {token}"}


class AutoAuthSession(HttpSession):

    def _is_unauthorized(self, resp):
        if resp.status_code == 401:
            return True
        if resp.status_code in (500, 403):
            try:
                return resp.json().get("code") == 401
            except Exception:
                return False
        return False

    def request(self, method, url, name=None, catch_response=False, context=None, **kwargs):
        is_login = str(url).endswith(Config.LOGIN_ENDPOINT) or "sso/login" in str(url)

        if not is_login and getattr(self, "user", None) and getattr(self.user, "token", None):
            headers = dict(kwargs.get("headers") or {})
            headers["Authorization"] = f"Bearer {self.user.token}"
            kwargs["headers"] = headers

        rcm = super().request(
            method, url, name=name, catch_response=True, context=context or {}, **kwargs
        )

        if self._is_unauthorized(rcm) and not is_login and getattr(self, "user", None):
            rcm.__enter__()
            rcm.failure("token expired (auto-retry)")
            rcm.__exit__(None, None, None)

            TokenCache.invalidate(self.user)
            if not TokenCache.ensure_token(self.user):
                logger.warning("[auth] re-login failed, keep 401 response")
            else:
                rcm = super().request(
                    method, url, name=name, catch_response=True, context=context or {}, **kwargs
                )
                if self._is_unauthorized(rcm):
                    sent = (kwargs.get("headers") or {}).get("Authorization", "<none>")
                    logger.warning(
                        f"[auth] still 401 after re-login user={getattr(self.user, 'username', '?')} "
                        f"user.token={getattr(self.user, 'token', '')[:10]}… "
                        f"sent={str(sent)[:20]}…: {method} {url} — "
                        f"check mall-portal log / gateway rule for this path"
                    )

        if not catch_response:
            rcm.__exit__(None, None, None)
        return rcm
