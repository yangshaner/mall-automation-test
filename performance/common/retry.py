# common/retry.py

import time

def retry_once(func, max_attempts=2, delay=0.1):
    last_exc = None
    for attempt in range(max_attempts):
        try:
            return func(), attempt + 1
        except Exception as e:
            last_exc = e
            if attempt < max_attempts - 1:
                time.sleep(delay)
    raise last_exc
