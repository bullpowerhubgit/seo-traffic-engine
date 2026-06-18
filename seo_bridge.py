"""
SEO Bridge — connect any service to the SEO Traffic Engine.
Usage:
    from seo_bridge import SEOBridge
    bridge = SEOBridge(project_name="my-project", keywords=["shopify", "seo"])
    asyncio.create_task(bridge.start_background_sync())
"""
import asyncio
import logging
import os

import aiohttp

log = logging.getLogger("seo_bridge")
SEO_ENGINE_URL = os.getenv("SEO_ENGINE_URL", "https://seo-traffic-engine-production.up.railway.app")


class SEOBridge:
    def __init__(self, project_name: str, keywords: list[str], interval_hours: int = 6):
        self.project_name = project_name
        self.keywords = keywords
        self.interval = interval_hours * 3600
        self._last_sync = 0

    async def push_keywords(self, keywords: list[str] | None = None) -> bool:
        kws = keywords or self.keywords
        try:
            async with aiohttp.ClientSession() as s:
                for kw in kws:
                    payload = {
                        "title": kw,
                        "url": os.getenv("APP_URL", ""),
                        "keyword": kw,
                        "excerpt": f"Article about {kw} for {self.project_name}",
                    }
                    async with s.post(
                        f"{SEO_ENGINE_URL}/api/trigger/articles",
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=8),
                    ) as r:
                        if r.status == 200:
                            log.info(f"SEO: triggered article for '{kw}'")
            return True
        except Exception as e:
            log.warning(f"SEO push failed: {e}")
            return False

    async def get_products(self, keyword: str, source: str = "all") -> list[dict]:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(
                    f"{SEO_ENGINE_URL}/api/products",
                    params={"keyword": keyword, "source": source},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as r:
                    if r.status == 200:
                        d = await r.json()
                        return d.get("products", [])
        except Exception as e:
            log.warning(f"SEO products failed: {e}")
        return []

    async def get_recommendations(self, topic: str) -> dict:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.post(
                    f"{SEO_ENGINE_URL}/api/recommend",
                    json={"topic": topic, "limit": 5},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as r:
                    if r.status == 200:
                        return await r.json()
        except Exception as e:
            log.warning(f"SEO recommend failed: {e}")
        return {"topic": topic, "amazon": [], "ebay": [], "total": 0}

    async def get_articles(self) -> list[dict]:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(
                    f"{SEO_ENGINE_URL}/stats",
                    timeout=aiohttp.ClientTimeout(total=8),
                ) as r:
                    if r.status == 200:
                        d = await r.json()
                        return d.get("articles", [])
        except Exception as e:
            log.warning(f"SEO stats failed: {e}")
        return []

    async def start_background_sync(self):
        import time

        await asyncio.sleep(60)
        while True:
            try:
                now = time.time()
                if now - self._last_sync >= self.interval:
                    await self.push_keywords()
                    self._last_sync = now
                    log.info(f"SEO sync done for {self.project_name}")
            except Exception as e:
                log.warning(f"SEO sync error: {e}")
            await asyncio.sleep(3600)


def add_seo_routes(router, bridge: "SEOBridge"):
    """Add /api/seo and /api/seo/products routes to an aiohttp router."""
    from aiohttp import web

    async def handle_seo(request):
        articles = await bridge.get_articles()
        return web.json_response(
            {
                "project": bridge.project_name,
                "seo_engine": SEO_ENGINE_URL,
                "articles_tracked": len(articles),
                "keywords": bridge.keywords[:10],
                "top_articles": articles[:5],
            }
        )

    async def handle_seo_products(request):
        keyword = request.rel_url.query.get(
            "keyword", bridge.keywords[0] if bridge.keywords else "shopify"
        )
        products = await bridge.get_products(keyword)
        return web.json_response({"keyword": keyword, "products": products})

    router.add_get("/api/seo", handle_seo)
    router.add_get("/api/seo/products", handle_seo_products)
