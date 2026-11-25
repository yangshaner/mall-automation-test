# metrics/collector.py
import csv
import time
import threading
import os
from locust import events

from performance.config import Config


class MetricsCollector:

    def __init__(self, output_dir="metrics_output"):
        os.makedirs(output_dir, exist_ok=True)
        self.path = os.path.join(output_dir, f"req_metrics_{int(time.time())}.csv")
        self._lock = threading.Lock()
        self._file = open(self.path, "w", newline="", encoding="utf-8")
        self._writer = csv.writer(self._file)
        self._writer.writerow(
            ["ts", "api_name", "response_time_ms", "status_code",
             "business_code", "success", "failure_reason", "response_bytes"
             ])
        self._buffer = []
        self._buffer_size = 500
        self._last_flush = time.time()

    def record(self, api_name, response_time_ms, status_code,
               business_code, success, failure_reason, response_bytes,
               ts_ms=None):
        row = [
            ts_ms if ts_ms is not None else int(time.time() * 1000),
            api_name,
            round(response_time_ms, 2),
            status_code,
            business_code,
            success,
            failure_reason,
            response_bytes,
        ]
        with self._lock:
            self._buffer.append(row)
            if len(self._buffer) >= self._buffer_size or time.time() - self._last_flush >= 2:
                self._flush_locked()

    def _flush_locked(self):
        self._writer.writerows(self._buffer)
        self._file.flush()
        self._buffer.clear()
        self._last_flush = time.time()

    def flush(self):
        with self._lock:
            if self._buffer:
                self._flush_locked()

    def close(self):
        with self._lock:
            self._flush_locked()
            self._file.close()

_collector = None

def get_collector():
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector

@events.request.add_listener
def on_request(request_type, name, response_time, response_length,
               response, context, exception, start_time, url, **kwargs):
    collector = get_collector()
    status_code = getattr(response, "status_code", 0) if response is not None else 0
    business_code = ""
    reason = ""
    success = exception is None

    if exception:
        reason = f"{type(exception).__name__}: {str(exception)[:100]}"
    elif response is not None:
        if status_code >= 400:
            success = False
            reason = f"HTTP_{status_code}"
        else:
            try:
                body = response.json()
                business_code = body.get("code", "")
                business_code = str(business_code) if business_code != "" else ""
                if business_code != str(Config.SUCCESS_CODE):
                    success = False
                    reason = f"biz_code={business_code}"
            except Exception:
                pass

    collector.record(
        api_name=name,
        response_time_ms=response_time,
        status_code=status_code,
        business_code=business_code,
        success=success,
        failure_reason=reason,
        response_bytes=response_length,
        ts_ms=int(start_time * 1000) if start_time else None,
    )

@events.quitting.add_listener
def on_quit(environment, **kwargs):
    get_collector().close()
