import time
from collections import defaultdict, deque
MAX_REQUESTS = 10
WINDOW_SECONDS = 60

_requests: dict[str, deque] = defaultdict(deque)

def allow(key: str) -> bool:
    now = time.monotonic()
    timestamps = _requests[key]
    while(timestamps and now-timestamps[0]>WINDOW_SECONDS):
        timestamps.popleft()
    if len(timestamps)>=MAX_REQUESTS:
        return False
    timestamps.append(now)
    return True
