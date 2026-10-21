"""Small single-process admission limits for the public course deployment."""
import os
import time
from collections import deque
from starlette.responses import JSONResponse

class TrafficLimits:
    def __init__(self, app):
        self.app = app
        self.windows = {"analysis": deque(), "writes": deque()}
        self.active = 0

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or os.getenv("PUBLIC_TRAFFIC_LIMITS") != "true":
            return await self.app(scope, receive, send)
        analysis = scope["path"] == "/api/analyze" and scope["method"] == "POST"
        writing = scope["path"].startswith("/api/drafts") and scope["method"] in ("POST", "DELETE")
        if not (analysis or writing):
            return await self.app(scope, receive, send)
        now = time.monotonic()
        window = self.windows["analysis" if analysis else "writes"]
        while window and window[0] <= now - 60:
            window.popleft()
        if len(window) >= (20 if analysis else 30) or (analysis and self.active >= 4):
            return await JSONResponse({"detail":"The shared demo is busy. Please try again in a minute."}, status_code=429,
                headers={"Retry-After":"60"})(scope, receive, send)
        window.append(now)
        if analysis: self.active += 1
        try:
            await self.app(scope, receive, send)
        finally:
            if analysis: self.active -= 1
