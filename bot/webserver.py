"""Small HTTP health server for Render Web Services."""

import os
from aiohttp import web


class HealthServer:
    def __init__(self):
        self.host = os.getenv("WEB_HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "10000"))
        self.runner = None
        self.site = None
        self.bot_ready = False
        self.assistant_ready = False

    async def _root(self, _request):
        return web.json_response({
            "ok": True,
            "service": "chikoo-music-bot",
            "bot_ready": self.bot_ready,
            "assistant_ready": self.assistant_ready,
        })

    async def _health(self, _request):
        return web.json_response({
            "ok": self.bot_ready,
            "bot_ready": self.bot_ready,
            "assistant_ready": self.assistant_ready,
        }, status=200 if self.bot_ready else 503)

    async def start(self):
        app = web.Application()
        app.router.add_get("/", self._root)
        app.router.add_get("/health", self._health)
        app.router.add_get("/healthz", self._health)

        self.runner = web.AppRunner(app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        print(f"HTTP health server listening on {self.host}:{self.port}")

    async def stop(self):
        if self.runner is not None:
            await self.runner.cleanup()
            self.runner = None
            self.site = None


health_server = HealthServer()
