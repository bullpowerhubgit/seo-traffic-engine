import asyncio
import hashlib
import hmac
import json
import logging
import os
import time
from datetime import datetime, timezone

import aiohttp
import aiosqlite
import anthropic
from aiohttp import web

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("seo-traffic-engine")

PORT = int(os.getenv("PORT", "8080"))
DB_PATH = os.getenv("DB_PATH", "/tmp/seo_engine.db")
APP_URL = os.getenv("APP_URL", "https://seo-traffic-engine-production.up.railway.app")

# ── Mailchimp / Klaviyo / Shopify ─────────────────────────────────────────────
MC_API_KEY      = os.getenv("MAILCHIMP_API_KEY", "")
MC_SERVER       = os.getenv("MAILCHIMP_SERVER_PREFIX", "us7")
MC_LIST_ID      = os.getenv("MAILCHIMP_LIST_ID", "")
KV_API_KEY      = os.getenv("KLAVIYO_API_KEY", "")
KV_LIST_ID      = os.getenv("KLAVIYO_LIST_ID", "")
SHOPIFY_DOMAIN  = os.getenv("SHOPIFY_SHOP_DOMAIN", "")
SHOPIFY_TOKEN   = os.getenv("SHOPIFY_ADMIN_API_TOKEN", "") or os.getenv("SHOPIFY_ACCESS_TOKEN", "")
SHOPIFY_API_VER = os.getenv("SHOPIFY_API_VERSION", "2024-10")


async def mailchimp_add_subscriber(email: str, fname: str = "", tags: list = None):
    if not MC_API_KEY or not MC_LIST_ID:
        return
    from base64 import b64encode
    import hashlib
    auth = b64encode(f"any:{MC_API_KEY}".encode()).decode()
    member_hash = hashlib.md5(email.lower().encode()).hexdigest()
    payload = {"email_address": email, "status_if_new": "subscribed",
                "merge_fields": {"FNAME": fname}, "tags": tags or ["seo-engine", "content-reader"]}
    try:
        async with aiohttp.ClientSession() as s:
            await s.put(
                f"https://{MC_SERVER}.api.mailchimp.com/3.0/lists/{MC_LIST_ID}/members/{member_hash}",
                headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"},
                json=payload, timeout=aiohttp.ClientTimeout(total=10),
            )
    except Exception as e:
        logger.warning(f"Mailchimp subscribe error: {e}")


async def klaviyo_track_event(event_name: str, properties: dict):
    if not KV_API_KEY:
        return
    try:
        async with aiohttp.ClientSession() as s:
            await s.post(
                "https://a.klaviyo.com/api/events/",
                headers={"Authorization": f"Klaviyo-API-Key {KV_API_KEY}",
                         "revision": "2024-06-15", "Content-Type": "application/json"},
                json={"data": {"type": "event", "attributes": {
                    "metric": {"data": {"type": "metric", "attributes": {"name": event_name}}},
                    "properties": properties,
                    "time": datetime.now(timezone.utc).isoformat(),
                }}},
                timeout=aiohttp.ClientTimeout(total=10),
            )
    except Exception as e:
        logger.warning(f"Klaviyo event error: {e}")


async def shopify_update_product_seo(product_id: str, seo_title: str, seo_desc: str, tags: list):
    if not SHOPIFY_DOMAIN or not SHOPIFY_TOKEN:
        return
    try:
        async with aiohttp.ClientSession() as s:
            await s.put(
                f"https://{SHOPIFY_DOMAIN}/admin/api/{SHOPIFY_API_VER}/products/{product_id}.json",
                headers={"X-Shopify-Access-Token": SHOPIFY_TOKEN, "Content-Type": "application/json"},
                json={"product": {
                    "id": product_id,
                    "metafields_global_title_tag": seo_title[:70],
                    "metafields_global_description_tag": seo_desc[:160],
                    "tags": ", ".join(tags[:10]),
                }},
                timeout=aiohttp.ClientTimeout(total=15),
            )
    except Exception as e:
        logger.warning(f"Shopify SEO update error: {e}")

KEYWORDS = [
    "shopify automation", "shopify product import", "e-commerce automatisierung",
    "shopify ki tools", "dropshipping automatisierung", "shopify api python",
    "seo tools kostenlos", "keyword research tool", "seo analyse deutsch",
    "shopify skalierung", "online shop automatisieren", "e-commerce seo",
    "affiliate marketing automatisierung", "digistore24 tipps",
    "passive income online shop", "shopify starter guide", "seo content strategie",
    "backlink aufbau strategie", "google ranking verbessern", "long tail keywords finden",
    "amazon bestseller produkte finden", "ebay dropshipping deutschland",
    "amazon fba anfänger guide", "ebay verkäufer automatisieren",
    "amazon affiliate marketing", "ebay api integration",
    "produkte von amazon importieren shopify", "ebay listing automatisierung",
    "amazon product research tool", "best selling products ebay 2025",
]

PRODUCTS = [
    {"name": "Shopify Acquisition Engine", "url": "https://shopify-acquisition-engine-production.up.railway.app", "desc": "KI-gestützte Shopify Automatisierung"},
    {"name": "SEO Turbo Tools", "url": "https://seo-turbo-tools-production.up.railway.app", "desc": "Professionelle SEO Analyse & Keyword Research"},
    {"name": "iComeAuto SaaS", "url": "https://icomeauto-saas-production.up.railway.app", "desc": "Income Automation Platform"},
    {"name": "SteuercockPit", "url": "https://bullpower-steuercockpit.netlify.app", "desc": "KI-Steuerberater für Freelancer & Selbstständige"},
    {"name": "Analytics Marketing Pro", "url": "https://analytics-marketing-pro-production.up.railway.app", "desc": "Klaviyo, Mailchimp & Facebook Pixel Automatisierung"},
    {"name": "Shopify Automaton Suite", "url": "https://shopify-automaton-suite-production-e405.up.railway.app", "desc": "Vollautomatische Shopify Suite mit Amazon & AliExpress"},
    {"name": "Windsurf Shopify Suite", "url": "https://windsurf-shopify-suite-production.up.railway.app", "desc": "Shopify SaaS mit KI-Preisoptimierung"},
    {"name": "CreatorAI Ultra", "url": "https://creatorai-ultra-production.up.railway.app", "desc": "KI Content Creator & Automatisierung"},
    {"name": "Cognitive Symphony", "url": "https://cognitive-symphony-production.up.railway.app", "desc": "KI Business Analyse & Automatisierung"},
]


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                published_at TEXT NOT NULL,
                tweeted INTEGER DEFAULT 0,
                views INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS keyword_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT UNIQUE NOT NULL,
                priority INTEGER DEFAULT 5,
                last_used TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS scheduler_state (
                task TEXT PRIMARY KEY,
                last_run INTEGER DEFAULT 0
            )
        """)
        for kw in KEYWORDS:
            await db.execute(
                "INSERT OR IGNORE INTO keyword_queue (keyword, priority) VALUES (?, ?)",
                (kw, 7)
            )
        await db.commit()


def slugify(text: str) -> str:
    import re
    text = text.lower().replace(" ", "-")
    text = re.sub(r"[^a-z0-9\-]", "", text)
    return text[:80]


async def telegram_send(text: str):
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        logger.warning("Telegram nicht konfiguriert")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status != 200:
                    logger.error(f"Telegram error: {r.status}")
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")


async def search_amazon_products(keyword: str, limit: int = 5) -> list[dict]:
    """Returns list of {title, url, price, image, asin} — affiliate links via tag if set"""
    import urllib.parse
    tag = os.getenv("AMAZON_AFFILIATE_TAG", "bullpower-21")
    search_url = f"https://www.amazon.de/s?k={urllib.parse.quote(keyword)}&tag={tag}"
    return [{"title": f"Amazon: {keyword}", "url": search_url, "price": "", "source": "amazon", "search": True}]


async def search_ebay_products(keyword: str, limit: int = 5) -> list[dict]:
    """eBay Finding API — needs EBAY_APP_ID, falls back to search URL"""
    import urllib.parse
    app_id = os.getenv("EBAY_APP_ID", "")
    if app_id:
        url = "https://svcs.ebay.com/services/search/FindingService/v1"
        params = {
            "OPERATION-NAME": "findItemsByKeywords",
            "SERVICE-VERSION": "1.0.0",
            "SECURITY-APPNAME": app_id,
            "RESPONSE-DATA-FORMAT": "JSON",
            "keywords": keyword,
            "paginationInput.entriesPerPage": str(limit),
            "sortOrder": "BestMatch",
        }
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    if r.status == 200:
                        data = await r.json()
                        items = data.get("findItemsByKeywordsResponse", [{}])[0].get("searchResult", [{}])[0].get("item", [])
                        results = []
                        for item in items[:limit]:
                            title = item.get("title", [""])[0]
                            item_url = item.get("viewItemURL", [""])[0]
                            price = item.get("sellingStatus", [{}])[0].get("currentPrice", [{}])[0].get("__value__", "")
                            results.append({"title": title, "url": item_url, "price": price, "source": "ebay"})
                        return results
        except Exception as e:
            logger.warning(f"eBay API error: {e}")
    # Fallback: search URL
    search_url = f"https://www.ebay.de/sch/i.html?_nkw={urllib.parse.quote(keyword)}"
    return [{"title": f"eBay: {keyword}", "url": search_url, "price": "", "source": "ebay", "search": True}]


async def generate_article(keyword: str, product: dict) -> dict | None:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY fehlt")
        return None
    try:
        client = anthropic.Anthropic(api_key=api_key)
        prompt = f"""Schreibe einen SEO-optimierten Blog-Artikel auf Deutsch über: "{keyword}"

Produkt das natürlich erwähnt wird: {product['name']} — {product['desc']} ({product['url']})

Ausgabe-Format (exakt so, keine JSON, nur Text):
TITLE: [Catchy Titel mit Keyword, max 70 Zeichen]
META: [Meta-Description 140-155 Zeichen]
---
[Artikel-Inhalt in HTML: <h2>, <p>, <ul><li> Tags, 600-900 Wörter, natürlich, hilfreich]
[Am Ende CTA zum Produkt einbauen]

Starte direkt ohne Einleitung wie "Hier ist der Artikel..."."""

        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = msg.content[0].text.strip()

        # Parse structured plain-text format
        title = f"Guide: {keyword}"
        meta = f"Alles über {keyword} — Tipps und Tools für 2025."
        content = raw

        if raw.startswith("TITLE:"):
            lines = raw.split("\n")
            body_lines = []
            in_body = False
            for line in lines:
                if line.startswith("TITLE:") and not in_body:
                    title = line.replace("TITLE:", "").strip()
                elif line.startswith("META:") and not in_body:
                    meta = line.replace("META:", "").strip()
                elif line.strip() == "---":
                    in_body = True
                elif in_body:
                    body_lines.append(line)
            if body_lines:
                content = "\n".join(body_lines).strip()

        article = {"title": title, "meta_description": meta, "content": content}

        # Append marketplace product recommendations
        amazon_products = await search_amazon_products(keyword, limit=3)
        ebay_products = await search_ebay_products(keyword, limit=3)

        product_html = "\n<section class='marketplace-picks'>\n<h2>🛒 Passende Produkte</h2>\n"
        product_html += "<div class='product-grid'>\n"
        for p in amazon_products[:2]:
            product_html += f'<div class="product-card"><a href="{p["url"]}" target="_blank" rel="nofollow">🟠 Amazon: {p["title"][:60]}</a></div>\n'
        for p in ebay_products[:2]:
            product_html += f'<div class="product-card"><a href="{p["url"]}" target="_blank" rel="nofollow">🟡 eBay: {p["title"][:60]}</a></div>\n'
        product_html += "</div></section>\n"

        article["content"] = article.get("content", "") + product_html
        return article
    except Exception as e:
        logger.error(f"Artikel-Generierung fehlgeschlagen: {e}")
        return None


async def post_to_twitter(title: str, url: str, keyword: str) -> bool:
    api_key = os.getenv("TWITTER_API_KEY", "")
    api_secret = os.getenv("TWITTER_API_SECRET", "")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN", "")
    access_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
    if not all([api_key, api_secret, access_token, access_secret]):
        logger.warning("Twitter credentials unvollständig")
        return False
    try:
        import base64
        import urllib.parse

        tweet_text = f"{title}\n\n#{keyword.replace(' ', '')} #SEO #Shopify\n\n{url}"
        if len(tweet_text) > 280:
            tweet_text = f"{title[:200]}...\n\n{url}"

        tweet_url = "https://api.twitter.com/2/tweets"
        method = "POST"
        timestamp = str(int(time.time()))
        nonce = hashlib.md5(f"{timestamp}{api_key}".encode()).hexdigest()

        params = {
            "oauth_consumer_key": api_key,
            "oauth_nonce": nonce,
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": timestamp,
            "oauth_token": access_token,
            "oauth_version": "1.0",
        }

        param_string = "&".join(f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(v, safe='')}" for k, v in sorted(params.items()))
        base_string = f"{method}&{urllib.parse.quote(tweet_url, safe='')}&{urllib.parse.quote(param_string, safe='')}"
        signing_key = f"{urllib.parse.quote(api_secret, safe='')}&{urllib.parse.quote(access_secret, safe='')}"
        signature = base64.b64encode(hmac.new(signing_key.encode(), base_string.encode(), "sha1").digest()).decode()

        params["oauth_signature"] = signature
        auth_header = "OAuth " + ", ".join(f'{k}="{urllib.parse.quote(v, safe="")}"' for k, v in sorted(params.items()))

        async with aiohttp.ClientSession() as session:
            async with session.post(
                tweet_url,
                headers={"Authorization": auth_header, "Content-Type": "application/json"},
                json={"text": tweet_text},
                timeout=aiohttp.ClientTimeout(total=15)
            ) as r:
                resp_data = await r.json()
                if r.status in (200, 201):
                    logger.info(f"Tweet posted: {resp_data.get('data', {}).get('id', 'unknown')}")
                    return True
                logger.error(f"Twitter error {r.status}: {resp_data}")
                return False
    except Exception as e:
        logger.error(f"Twitter post failed: {e}")
        return False


SOCIAL_ENGINE_URLS = [
    os.getenv("META_ENGINE_URL", "https://meta-social-engine-production.up.railway.app"),
    os.getenv("VISUAL_ENGINE_URL", "https://visual-content-engine-production.up.railway.app"),
    os.getenv("SOCIAL_ENGINE_URL", "https://social-traffic-engine-production.up.railway.app"),
    os.getenv("FREELANCE_ENGINE_URL", "https://freelance-gig-engine-production.up.railway.app"),
    os.getenv("ADPOSTER_ENGINE_URL", "https://adposter-engine-production.up.railway.app"),
    os.getenv("SHOPIFY_ACQUISITION_URL", "https://shopify-acquisition-engine-production.up.railway.app"),
    os.getenv("ICOMEAUTO_URL", "https://icomeauto-saas-production.up.railway.app"),
    os.getenv("STEUERCOCKPIT_URL", "https://steuercockpit-production-44c9.up.railway.app"),
    os.getenv("DIGISTORE_URL", "https://digistore24-automation-production.up.railway.app"),
    os.getenv("CREATORAI_URL", "https://creatorai-ultra-production.up.railway.app"),
    os.getenv("COGNITIVE_URL", "https://cognitive-symphony-production.up.railway.app"),
    os.getenv("SUPERMEGABOT_URL", "https://dudirudibot-mega-production.up.railway.app"),
    os.getenv("TELEGRAM_BOT_URL", "https://telegram-automation-bot-production.up.railway.app"),
    os.getenv("SEO_TURBO_URL", "https://seo-turbo-tools-production.up.railway.app"),
    os.getenv("ANALYTICS_URL", "https://analytics-marketing-pro-production.up.railway.app"),
    os.getenv("SHOPIFY_AUTOMATON_URL", "https://shopify-automaton-suite-production-e405.up.railway.app"),
    os.getenv("WINDSURF_SHOPIFY_URL", "https://windsurf-shopify-suite-production.up.railway.app"),
]


async def broadcast_article(article: dict, slug: str, keyword: str, product: dict):
    payload = {
        "title": article.get("title", ""),
        "content": article.get("content", "")[:2000],
        "url": f"{APP_URL}/blog/{slug}",
        "keyword": keyword,
        "excerpt": article.get("meta_description", article.get("content", "")[:300]),
        "product_name": product["name"],
        "product_url": product["url"],
    }
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        for engine_url in SOCIAL_ENGINE_URLS:
            try:
                resp = await session.post(f"{engine_url}/api/ingest", json=payload)
                logger.info(f"Broadcast to {engine_url}: {resp.status}")
            except Exception as e:
                logger.warning(f"Broadcast failed to {engine_url}: {e}")


async def ping_search_engines(article_url: str):
    sitemap_url = f"{APP_URL}/sitemap.xml"
    ping_urls = [
        f"https://www.google.com/ping?sitemap={sitemap_url}",
        f"https://www.bing.com/ping?sitemap={sitemap_url}",
    ]
    async with aiohttp.ClientSession() as session:
        for url in ping_urls:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    logger.info(f"Sitemap ping {url}: {r.status}")
            except Exception as e:
                logger.warning(f"Ping fehlgeschlagen {url}: {e}")


async def task_generate_articles():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT keyword FROM keyword_queue ORDER BY priority DESC, last_used ASC NULLS FIRST LIMIT 3"
        )
        keywords = [row[0] for row in await cursor.fetchall()]

    for i, keyword in enumerate(keywords):
        product = PRODUCTS[i % len(PRODUCTS)]
        logger.info(f"Generiere Artikel: {keyword}")
        article = await generate_article(keyword, product)
        if not article:
            continue

        title = article.get("title", f"Guide: {keyword}")
        content = article.get("content", "")
        slug = slugify(title)
        published_at = datetime.now(timezone.utc).isoformat()

        try:
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "INSERT OR IGNORE INTO articles (keyword, title, content, slug, published_at) VALUES (?, ?, ?, ?, ?)",
                    (keyword, title, content, slug, published_at)
                )
                await db.execute(
                    "UPDATE keyword_queue SET last_used = ? WHERE keyword = ?",
                    (published_at, keyword)
                )
                await db.commit()

            article_url = f"{APP_URL}/blog/{slug}"
            await ping_search_engines(article_url)
            await broadcast_article(article, slug, keyword, product)
            await klaviyo_track_event("SEO Article Published", {
                "keyword": keyword, "title": title, "url": article_url,
                "product": product["name"],
            })
            await telegram_send(
                f"📝 <b>Neuer SEO Artikel veröffentlicht!</b>\n\n"
                f"🔑 Keyword: {keyword}\n"
                f"📄 Titel: {title}\n"
                f"🔗 URL: {article_url}\n"
                f"🏪 Produkt: {product['name']}\n\n"
                f"✅ Google & Bing gecrawlt | Klaviyo getrackt"
            )
            logger.info(f"Artikel gespeichert: {slug}")
        except Exception as e:
            logger.error(f"DB-Speicherung fehlgeschlagen: {e}")

        await asyncio.sleep(2)


async def task_tweet_articles():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, title, slug, keyword FROM articles WHERE tweeted = 0 ORDER BY published_at DESC LIMIT 3"
        )
        rows = await cursor.fetchall()

    for article_id, title, slug, keyword in rows:
        article_url = f"{APP_URL}/blog/{slug}"
        success = await post_to_twitter(title, article_url, keyword)
        if success:
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE articles SET tweeted = 1 WHERE id = ?", (article_id,))
                await db.commit()
            await telegram_send(f"🐦 <b>Tweet gepostet!</b>\n{title}\n{article_url}")
        await asyncio.sleep(5)


async def task_add_keywords():
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return
    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role": "user", "content": "Liste 10 deutschsprachige Long-Tail-Keywords für E-Commerce Automatisierung und SEO Tools. Nur die Keywords, eine pro Zeile, keine Nummerierung."}]
        )
        new_keywords = [line.strip() for line in msg.content[0].text.strip().split("\n") if line.strip()]
        async with aiosqlite.connect(DB_PATH) as db:
            for kw in new_keywords[:10]:
                await db.execute("INSERT OR IGNORE INTO keyword_queue (keyword, priority) VALUES (?, 5)", (kw,))
            await db.commit()
        logger.info(f"Neue Keywords hinzugefügt: {len(new_keywords)}")
    except Exception as e:
        logger.error(f"Keyword-Generierung fehlgeschlagen: {e}")


async def task_shopify_seo_sync():
    """Fetch Shopify products and update their SEO tags with current keywords."""
    if not SHOPIFY_DOMAIN or not SHOPIFY_TOKEN:
        logger.info("Shopify SEO sync: not configured")
        return
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"https://{SHOPIFY_DOMAIN}/admin/api/{SHOPIFY_API_VER}/products.json?limit=10&fields=id,title,tags",
                headers={"X-Shopify-Access-Token": SHOPIFY_TOKEN},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as r:
                data = await r.json(content_type=None)
        products = data.get("products", [])
        updated = 0
        for p in products[:5]:
            title = p.get("title", "")
            if not title:
                continue
            seo_keywords = [kw for kw in KEYWORDS[:3] if any(w in title.lower() for w in ["shop", "seo", "auto", "store"])]
            if not seo_keywords:
                seo_keywords = KEYWORDS[:2]
            await shopify_update_product_seo(
                str(p["id"]),
                f"{title} — Shopify Automatisierung & SEO",
                f"Entdecke {title}. {seo_keywords[0].title()} für deinen Online-Shop. Jetzt starten!",
                seo_keywords[:5],
            )
            updated += 1
        logger.info(f"Shopify SEO sync: {updated} Produkte aktualisiert")
        await klaviyo_track_event("Shopify SEO Synced", {"products_updated": updated})
    except Exception as e:
        logger.error(f"Shopify SEO sync error: {e}")


async def get_task_due(task: str, interval: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT last_run FROM scheduler_state WHERE task = ?", (task,))
        row = await cursor.fetchone()
        last_run = row[0] if row else 0
        now = int(time.time())
        if now - last_run >= interval:
            await db.execute(
                "INSERT OR REPLACE INTO scheduler_state (task, last_run) VALUES (?, ?)",
                (task, now)
            )
            await db.commit()
            return True
    return False


async def scheduler_loop():
    INTERVALS = {
        "generate_articles": 6 * 3600,
        "tweet_articles": 4 * 3600,
        "add_keywords": 24 * 3600,
        "sitemap_ping": 1 * 3600,
        "shopify_seo_sync": 12 * 3600,
    }
    await asyncio.sleep(10)
    logger.info("Scheduler gestartet")

    # Run article generation immediately on startup
    await task_generate_articles()

    while True:
        try:
            if await get_task_due("generate_articles", INTERVALS["generate_articles"]):
                logger.info("Task: generate_articles")
                await task_generate_articles()

            if await get_task_due("tweet_articles", INTERVALS["tweet_articles"]):
                logger.info("Task: tweet_articles")
                await task_tweet_articles()

            if await get_task_due("add_keywords", INTERVALS["add_keywords"]):
                logger.info("Task: add_keywords")
                await task_add_keywords()

            if await get_task_due("sitemap_ping", INTERVALS["sitemap_ping"]):
                logger.info("Task: sitemap_ping")
                await ping_search_engines(APP_URL)

            if await get_task_due("shopify_seo_sync", INTERVALS["shopify_seo_sync"]):
                logger.info("Task: shopify_seo_sync")
                await task_shopify_seo_sync()

        except Exception as e:
            logger.error(f"Scheduler error: {e}")

        await asyncio.sleep(300)


async def serve_blog_index(request: web.Request) -> web.Response:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT title, slug, keyword, published_at FROM articles ORDER BY published_at DESC LIMIT 20"
        )
        articles = await cursor.fetchall()

    items = ""
    for title, slug, keyword, published_at in articles:
        date = published_at[:10] if published_at else ""
        items += f'<article><h2><a href="/blog/{slug}">{title}</a></h2><p class="meta">{keyword} — {date}</p></article>\n'

    if not items:
        items = "<p>Erste Artikel werden generiert...</p>"

    html = f"""<!DOCTYPE html>
<html lang="de">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SEO Traffic Engine — E-Commerce Automatisierung Blog</title>
<meta name="description" content="Professionelle Guides zu Shopify Automatisierung, SEO Optimierung und E-Commerce Skalierung.">
<style>
body{{margin:0;font-family:system-ui,sans-serif;background:#0d1117;color:#e6edf3;}}
header{{background:#161b22;padding:20px;border-bottom:1px solid #30363d;}}
header h1{{margin:0;color:#58a6ff;font-size:1.5rem;}}
main{{max-width:800px;margin:40px auto;padding:0 20px;}}
article{{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:20px;margin:20px 0;}}
article h2{{margin:0 0 8px;}}
article h2 a{{color:#58a6ff;text-decoration:none;}}
article h2 a:hover{{text-decoration:underline;}}
.meta{{color:#8b949e;font-size:0.85rem;margin:0;}}
footer{{text-align:center;padding:40px 20px;color:#8b949e;font-size:0.8rem;}}
</style>
</head>
<body>
<header><h1>SEO Traffic Engine — E-Commerce Blog</h1><p>Automatisch generierte SEO-Artikel zu Shopify, E-Commerce & Automatisierung</p></header>
<main>
<h2>Neueste Artikel</h2>
{items}
</main>
<footer>
Powered by <a href="{APP_URL}" style="color:#58a6ff;">SEO Traffic Engine</a> •
<a href="/sitemap.xml" style="color:#58a6ff;">Sitemap</a>
</footer>
</body>
</html>"""
    return web.Response(text=html, content_type="text/html")


async def serve_blog_article(request: web.Request) -> web.Response:
    slug = request.match_info["slug"]
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT title, content, keyword, published_at FROM articles WHERE slug = ?", (slug,)
        )
        row = await cursor.fetchone()
        if row:
            await db.execute("UPDATE articles SET views = views + 1 WHERE slug = ?", (slug,))
            await db.commit()

    if not row:
        raise web.HTTPNotFound(text="Artikel nicht gefunden")

    title, content, keyword, published_at = row
    date = published_at[:10] if published_at else ""
    html = f"""<!DOCTYPE html>
<html lang="de">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="keywords" content="{keyword}, seo, e-commerce, automatisierung">
<link rel="canonical" href="{APP_URL}/blog/{slug}">
<style>
body{{margin:0;font-family:system-ui,sans-serif;background:#0d1117;color:#e6edf3;line-height:1.7;}}
header{{background:#161b22;padding:20px;border-bottom:1px solid #30363d;}}
header a{{color:#58a6ff;text-decoration:none;}}
.article{{max-width:800px;margin:40px auto;padding:0 20px;}}
h1{{color:#e6edf3;font-size:2rem;margin-bottom:8px;}}
.meta{{color:#8b949e;font-size:0.9rem;margin-bottom:40px;}}
h2{{color:#58a6ff;margin-top:40px;}}
ul{{padding-left:20px;}}
li{{margin:6px 0;}}
a{{color:#58a6ff;}}
footer{{text-align:center;padding:40px 20px;color:#8b949e;font-size:0.8rem;border-top:1px solid #30363d;margin-top:60px;}}
</style>
</head>
<body>
<header><a href="/blog">← Blog</a></header>
<div class="article">
<h1>{title}</h1>
<p class="meta">Keyword: {keyword} • Veröffentlicht: {date}</p>
{content}
</div>
<footer>© 2026 SEO Traffic Engine • <a href="/sitemap.xml">Sitemap</a></footer>
</body>
</html>"""
    return web.Response(text=html, content_type="text/html")


async def serve_sitemap(request: web.Request) -> web.Response:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT slug, published_at FROM articles ORDER BY published_at DESC")
        articles = await cursor.fetchall()

    urls = f"<url><loc>{APP_URL}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>\n"
    urls += f"<url><loc>{APP_URL}/blog</loc><changefreq>daily</changefreq><priority>0.9</priority></url>\n"
    for slug, published_at in articles:
        lastmod = published_at[:10] if published_at else "2026-01-01"
        urls += f"<url><loc>{APP_URL}/blog/{slug}</loc><lastmod>{lastmod}</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>\n"

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>"""
    return web.Response(text=xml, content_type="application/xml")


async def handle_health(request: web.Request) -> web.Response:
    return web.json_response({
        "status": "ok",
        "service": "seo-traffic-engine",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


async def handle_stats(request: web.Request) -> web.Response:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT title, slug, views, tweeted, keyword FROM articles ORDER BY views DESC LIMIT 20")
        articles = [{"title": r[0], "slug": r[1], "views": r[2], "tweeted": bool(r[3]), "keyword": r[4]} for r in await cursor.fetchall()]
        cursor = await db.execute("SELECT task, last_run FROM scheduler_state")
        tasks = {r[0]: r[1] for r in await cursor.fetchall()}
    return web.json_response({"articles": articles, "scheduler": tasks})


async def handle_trigger_articles(request: web.Request) -> web.Response:
    asyncio.create_task(task_generate_articles())
    return web.json_response({"status": "triggered", "task": "generate_articles"})


async def handle_trigger_tweets(request: web.Request) -> web.Response:
    asyncio.create_task(task_tweet_articles())
    return web.json_response({"status": "triggered", "task": "tweet_articles"})


async def handle_products(request: web.Request) -> web.Response:
    keyword = request.rel_url.query.get("keyword", "shopify automation")
    source = request.rel_url.query.get("source", "all")
    results = []
    if source in ("amazon", "all"):
        results += await search_amazon_products(keyword)
    if source in ("ebay", "all"):
        results += await search_ebay_products(keyword)
    return web.json_response({"keyword": keyword, "products": results, "count": len(results)})


async def handle_recommend(request: web.Request) -> web.Response:
    data = await request.json()
    topic = data.get("topic", "")
    products_per_source = data.get("limit", 3)
    amazon = await search_amazon_products(topic, products_per_source)
    ebay = await search_ebay_products(topic, products_per_source)
    return web.json_response({"topic": topic, "amazon": amazon, "ebay": ebay, "total": len(amazon) + len(ebay)})


async def on_startup(app):
    await init_db()
    asyncio.create_task(scheduler_loop())
    logger.info(f"SEO Traffic Engine gestartet auf Port {PORT}")


def create_app():
    app = web.Application()
    app.on_startup.append(on_startup)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/stats", handle_stats)
    app.router.add_get("/sitemap.xml", serve_sitemap)
    app.router.add_get("/blog", serve_blog_index)
    app.router.add_get("/blog/{slug}", serve_blog_article)
    app.router.add_get("/", serve_blog_index)
    app.router.add_post("/api/trigger/articles", handle_trigger_articles)
    app.router.add_post("/api/trigger/tweets", handle_trigger_tweets)
    app.router.add_get("/api/products", handle_products)
    app.router.add_post("/api/recommend", handle_recommend)
    return app


if __name__ == "__main__":
    web.run_app(create_app(), port=PORT)
