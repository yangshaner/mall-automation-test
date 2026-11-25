# common/failure_taxonomy.py

class FailureTaxonomy:

    @staticmethod
    def classify(reason: str) -> str:
        if not reason:
            return "OK"
        r = reason.lower()
        if "timeout" in r or "time out" in r:
            return "TIMEOUT"
        if "connection" in r and ("refused" in r or "reset" in r):
            return "CONNECTION_ERROR"
        if r.startswith("http_5"):
            return "SERVER_5XX"
        if r.startswith("http_4"):
            return "CLIENT_4XX"
        if r.startswith("biz_"):
            code = r.replace("biz_", "")
            if code == "500":
                return "BIZ_INTERNAL_ERROR"
            if code == "401":
                return "BIZ_UNAUTHORIZED"
            if code == "404":
                return "BIZ_NOT_FOUND"
            return f"BIZ_OTHER_{code}"
        if "non_json" in r:
            return "NON_JSON_RESPONSE"
        return "OTHER"
