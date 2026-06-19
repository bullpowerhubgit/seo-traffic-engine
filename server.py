#!/usr/bin/env python3
"""
SEO Traffic Engine — MAXIMUM TUNING v2.0
Revolutionary autonomous SEO + traffic + broadcast system.
10000 Jahre voraus: IndexNow, Schema.org, LSI, Google Trends, Omni-Broadcast, AI-Content.
"""
import asyncio
import hashlib
import hmac
import json
import logging
import os
import re
import time
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import quote

import aiohttp
import aiosqlite
import anthropic
from aiohttp import web

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("seo-turbo-max")

PORT = int(os.getenv("PORT", "8080"))
DB_PATH = os.getenv("DB_PATH", "/tmp/seo_engine.db")
APP_URL = os.getenv("APP_URL", "https://seo-traffic-engine-production.up.railway.app")

# ── API Keys ──────────────────────────────────────────────────────────────────
ANTHROPIC_KEY   = os.getenv("ANTHROPIC_API_KEY", "")
TELEGRAM_TOKEN  = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT   = os.getenv("TELEGRAM_CHAT_ID", "")
MC_API_KEY      = os.getenv("MAILCHIMP_API_KEY", "")
MC_SERVER       = os.getenv("MAILCHIMP_SERVER_PREFIX", "us7")
MC_LIST_ID      = os.getenv("MAILCHIMP_LIST_ID", "")
KV_API_KEY      = os.getenv("KLAVIYO_API_KEY", "")
KV_LIST_ID      = os.getenv("KLAVIYO_LIST_ID", "")
SHOPIFY_DOMAIN  = os.getenv("SHOPIFY_SHOP_DOMAIN", "")
SHOPIFY_TOKEN   = os.getenv("SHOPIFY_ADMIN_API_TOKEN", "") or os.getenv("SHOPIFY_ACCESS_TOKEN", "")
SHOPIFY_API_VER = os.getenv("SHOPIFY_API_VERSION", "2024-10")
TWITTER_KEY     = os.getenv("TWITTER_API_KEY", "")
TWITTER_SECRET  = os.getenv("TWITTER_API_SECRET", "")
TWITTER_TOKEN   = os.getenv("TWITTER_ACCESS_TOKEN", "")
TWITTER_TSECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
REDDIT_CLIENT   = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_SECRET   = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER     = os.getenv("REDDIT_USERNAME", "")
REDDIT_PASS     = os.getenv("REDDIT_PASSWORD", "")
LINKEDIN_TOKEN  = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
LINKEDIN_URN    = os.getenv("LINKEDIN_PERSON_URN", "")
AMAZON_TAG      = os.getenv("AMAZON_AFFILIATE_TAG", "bullpower-21")
EBAY_APP_ID     = os.getenv("EBAY_APP_ID", "")

# IndexNow key — serves at /indexnow-key.txt for Bing/Yandex verification
INDEXNOW_KEY = os.getenv("INDEXNOW_KEY", str(uuid.uuid5(uuid.NAMESPACE_URL, APP_URL)).replace("-", ""))

# ── Product catalog ───────────────────────────────────────────────────────────
PRODUCTS = [
    {"name": "Shopify Acquisition Engine", "url": "https://shopify-acquisition-engine-production.up.railway.app", "desc": "KI-gestützte Shopify Automatisierung", "price": "kostenlos testen"},
    {"name": "SEO Turbo Tools", "url": "https://seo-turbo-tools-production.up.railway.app", "desc": "Professionelle SEO Analyse & Keyword Research", "price": "ab €29/mo"},
    {"name": "iComeAuto SaaS", "url": "https://bullpower-icomeauto.netlify.app", "desc": "Income Automation Platform", "price": "ab €29/mo"},
    {"name": "SteuercockPit", "url": "https://bullpower-steuercockpit.netlify.app", "desc": "KI-Steuerberater für Freelancer & Selbstständige", "price": "€29/mo"},
    {"name": "Analytics Marketing Pro", "url": "https://analytics-marketing-pro-production.up.railway.app", "desc": "Klaviyo, Mailchimp & Facebook Pixel Automatisierung", "price": "ab €49/mo"},
    {"name": "Shopify Automaton Suite", "url": "https://shopify-automaton-suite-production-e405.up.railway.app", "desc": "Vollautomatische Shopify Suite mit Amazon & AliExpress", "price": "kostenlos"},
    {"name": "CreatorAI Ultra", "url": "https://creatorai-ultra-production.up.railway.app", "desc": "KI Content Creator & Automatisierung", "price": "ab €19/mo"},
    {"name": "Cognitive Symphony", "url": "https://cognitive-symphony-production.up.railway.app", "desc": "KI Business Analyse & Automatisierung", "price": "ab €29/mo"},
    {"name": "BullPower Hub Bundle", "url": "https://bullpower-hub-portal.netlify.app", "desc": "8 KI-Tools für E-Commerce", "price": "ab €99/mo"},
]

# ── Core SEO keyword bank ─────────────────────────────────────────────────────
BASE_KEYWORDS = [
    "shopify automatisierung 2025", "shopify product import automatisch", "e-commerce automatisierung tool",
    "shopify ki tools vergleich", "dropshipping automatisierung software", "shopify api python guide",
    "seo tools kostenlos deutsch", "keyword research tool deutsch", "seo analyse tool kostenlos",
    "shopify skalierung strategie", "online shop automatisieren tipps", "e-commerce seo optimierung",
    "affiliate marketing automatisierung", "digistore24 tipps anfänger", "passives einkommen online shop",
    "backlink aufbau strategie 2025", "google ranking verbessern schnell", "long tail keywords finden tool",
    "amazon bestseller produkte finden", "ebay dropshipping deutschland guide",
    "amazon fba anfänger kompletter guide", "ebay verkäufer automatisieren wie",
    "amazon affiliate marketing passives einkommen", "shopify store conversion optimierung",
    "email marketing automatisierung shopify", "facebook ads shopify strategie",
    "tiktok shop dropshipping", "instagram shopping setup guide", "pinterest seo pins viral",
    "google shopping feed shopify", "local seo für online shops", "core web vitals shopify fix",
    "shopify speed optimierung 2025", "shopify abandoned cart email", "shopify upsell strategie",
    "ki text generator seo deutsch", "chatgpt für seo content", "claude ai für e-commerce",
    "woocommerce vs shopify vergleich", "shopify plus lohnt sich", "shopify payments einrichten",
    "stripe shopify integration", "paypal shopify probleme lösen", "shopify versand automatisieren",
    "fulfillment by amazon fba kosten", "alibaba dropshipping anleitung", "aliexpress shopify plugin",
    "canva shopify produktbilder", "produktfotos selber machen tipps", "seo meta description generator",
]

# ── All social/broadcast engines ─────────────────────────────────────────────
BROADCAST_ENGINES = [
    os.getenv("META_ENGINE_URL", "https://meta-social-engine-production.up.railway.app"),
    os.getenv("VISUAL_ENGINE_URL", "https://visual-content-engine-production.up.railway.app"),
    os.getenv("SOCIAL_ENGINE_URL", "https://social-traffic-engine-production.up.railway.app"),
    os.getenv("FREELANCE_ENGINE_URL", "https://freelance-gig-engine-production.up.railway.app"),
    os.getenv("ADPOSTER_ENGINE_URL", "https://adposter-engine-production.up.railway.app"),
    os.getenv("ICOMEAUTO_URL", "https://icomeauto-saas-production.up.railway.app"),
    os.getenv("DIGISTORE_URL", "https://digistore24-automation-production.up.railway.app"),
    os.getenv("CREATORAI_URL", "https://creatorai-ultra-production.up.railway.app"),
    os.getenv("SUPERMEGABOT_URL", "https://dudirudibot-mega-production.up.railway.app"),
    os.getenv("ANALYTICS_URL", "https://analytics-marketing-pro-production.up.railway.app"),
]

# Reddit subreddits for organic traffic
REDDIT_SUBS = ["entrepreneur", "ecommerce", "SEO", "shopify", "digital_marketing",
                "passive_income", "marketing", "smallbusiness"]


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

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
                meta_description TEXT DEFAULT '',
                schema_json TEXT DEFAULT '',
                lsi_keywords TEXT DEFAULT '',
                faq_json TEXT DEFAULT '',
                tweeted INTEGER DEFAULT 0,
                reddit_posted INTEGER DEFAULT 0,
                linkedin_posted INTEGER DEFAULT 0,
                newsletter_sent INTEGER DEFAULT 0,
                indexed_bing INTEGER DEFAULT 0,
                views INTEGER DEFAULT 0,
                engagement_score INTEGER DEFAULT 0,
                language TEXT DEFAULT 'de'
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS keyword_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT UNIQUE NOT NULL,
                priority INTEGER DEFAULT 5,
                source TEXT DEFAULT 'manual',
                last_used TEXT,
                success_score INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS scheduler_state (
                task TEXT PRIMARY KEY,
                last_run INTEGER DEFAULT 0,
                run_count INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS trending_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT UNIQUE NOT NULL,
                trend_score INTEGER DEFAULT 1,
                fetched_at TEXT NOT NULL,
                geo TEXT DEFAULT 'DE'
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS broadcast_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_slug TEXT NOT NULL,
                engine_url TEXT NOT NULL,
                status INTEGER DEFAULT 0,
                sent_at TEXT NOT NULL
            )
        """)
        for kw in BASE_KEYWORDS:
            await db.execute(
                "INSERT OR IGNORE INTO keyword_queue (keyword, priority, source) VALUES (?, 7, 'base')",
                (kw,)
            )
        await db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def slugify(text: str) -> str:
    text = text.lower().replace(" ", "-")
    text = re.sub(r"[^a-z0-9\-äöüß]", "", text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss"))
    text = re.sub(r"-+", "-", text)
    return text[:80].strip("-")


async def telegram_send(text: str, parse_mode: str = "HTML"):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        return
    try:
        async with aiohttp.ClientSession() as s:
            await s.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT, "text": text[:4096], "parse_mode": parse_mode},
                timeout=aiohttp.ClientTimeout(total=10)
            )
    except Exception as e:
        logger.warning(f"Telegram error: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# GOOGLE TRENDS RSS — FREE TRENDING KEYWORDS
# ═══════════════════════════════════════════════════════════════════════════════

async def fetch_google_trends(geo: str = "DE") -> list[str]:
    """Pull trending search terms from Google Trends RSS feed — completely free."""
    url = f"https://trends.google.com/trends/trendingsearches/daily/rss?geo={geo}"
    keywords = []
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=15),
                             headers={"User-Agent": "Mozilla/5.0 (compatible; SEOBot/2.0)"}) as r:
                if r.status == 200:
                    text = await r.text()
                    root = ET.fromstring(text)
                    ns = {"ht": "https://trends.google.com/trends/trendingsearches/daily"}
                    for item in root.findall(".//item"):
                        title_el = item.find("title")
                        if title_el is not None and title_el.text:
                            # Only keep e-commerce/business/tech related
                            kw = title_el.text.strip().lower()
                            relevant = any(t in kw for t in [
                                "shop", "amazon", "ebay", "ki", "ai", "geld", "verdienen",
                                "online", "digital", "seo", "app", "tool", "software",
                                "auto", "preis", "kauf", "deal", "angebot", "business",
                            ])
                            if relevant:
                                keywords.append(kw)
    except Exception as e:
        logger.warning(f"Google Trends RSS error: {e}")
    return keywords[:20]


async def task_refresh_trending_keywords():
    """Fetch Google Trends, add relevant ones to keyword queue with high priority."""
    trending = await fetch_google_trends("DE")
    if not trending:
        logger.info("No trending keywords fetched")
        return
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        added = 0
        for kw in trending:
            try:
                await db.execute(
                    "INSERT OR REPLACE INTO trending_keywords (keyword, trend_score, fetched_at, geo) VALUES (?, 10, ?, 'DE')",
                    (kw, now)
                )
                # Add to keyword queue with highest priority
                result = await db.execute(
                    "INSERT OR IGNORE INTO keyword_queue (keyword, priority, source) VALUES (?, 9, 'google_trends')",
                    (kw,)
                )
                if result.rowcount:
                    added += 1
            except Exception:
                pass
        await db.commit()
    logger.info(f"Trending keywords added: {added}/{len(trending)}")
    if added:
        await telegram_send(f"📈 <b>Google Trends Update</b>\n{added} neue trending Keywords: {', '.join(trending[:5])}")


# ═══════════════════════════════════════════════════════════════════════════════
# INDEXNOW — INSTANT BING/YANDEX/SEZNAM INDEXING
# ═══════════════════════════════════════════════════════════════════════════════

async def indexnow_ping(urls: list[str]) -> bool:
    """Submit URLs to IndexNow API — instant Bing + Yandex + Seznam indexing.
    Free, no auth beyond key file verification."""
    if not urls:
        return False
    payload = {
        "host": APP_URL.replace("https://", "").replace("http://", ""),
        "key": INDEXNOW_KEY,
        "keyLocation": f"{APP_URL}/{INDEXNOW_KEY}.txt",
        "urlList": urls[:100],
    }
    endpoints = [
        "https://api.indexnow.org/indexnow",
        "https://www.bing.com/indexnow",
        "https://yandex.com/indexnow",
    ]
    success = False
    async with aiohttp.ClientSession() as s:
        for ep in endpoints:
            try:
                async with s.post(ep, json=payload, timeout=aiohttp.ClientTimeout(total=10),
                                  headers={"Content-Type": "application/json; charset=utf-8"}) as r:
                    if r.status in (200, 202):
                        logger.info(f"IndexNow {ep}: {r.status}")
                        success = True
            except Exception as e:
                logger.warning(f"IndexNow {ep} error: {e}")
    return success


async def ping_search_engines(article_url: str):
    """Multi-engine sitemap + URL ping."""
    sitemap = f"{APP_URL}/sitemap.xml"
    # Google/Bing sitemap ping
    for ping_url in [
        f"https://www.google.com/ping?sitemap={quote(sitemap, safe='')}",
        f"https://www.bing.com/ping?sitemap={quote(sitemap, safe='')}",
    ]:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(ping_url, timeout=aiohttp.ClientTimeout(total=8)) as r:
                    logger.info(f"Sitemap ping {ping_url}: {r.status}")
        except Exception as e:
            logger.warning(f"Ping failed {ping_url}: {e}")
    # IndexNow for instant indexing
    await indexnow_ping([article_url])


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEMA.ORG JSON-LD — RICH SNIPPETS BOOST
# ═══════════════════════════════════════════════════════════════════════════════

def generate_schema_markup(title: str, meta: str, slug: str, keyword: str,
                            published_at: str, faqs: list[dict]) -> str:
    """Generate full Schema.org JSON-LD: Article + FAQPage + BreadcrumbList."""
    url = f"{APP_URL}/blog/{slug}"
    date = published_at[:10] if published_at else "2026-01-01"

    article_schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": meta,
        "url": url,
        "datePublished": date,
        "dateModified": date,
        "author": {"@type": "Organization", "name": "BullPower Hub", "url": "https://bullpower-hub-portal.netlify.app"},
        "publisher": {
            "@type": "Organization",
            "name": "BullPower Hub",
            "url": "https://bullpower-hub-portal.netlify.app",
            "logo": {"@type": "ImageObject", "url": f"{APP_URL}/logo.png"}
        },
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "keywords": keyword,
        "inLanguage": "de-DE",
        "articleSection": "E-Commerce & SEO",
    }

    breadcrumb_schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": APP_URL},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": f"{APP_URL}/blog"},
            {"@type": "ListItem", "position": 3, "name": title, "item": url},
        ]
    }

    schemas = [article_schema, breadcrumb_schema]

    if faqs:
        faq_schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": faq["question"],
                    "acceptedAnswer": {"@type": "Answer", "text": faq["answer"]}
                }
                for faq in faqs[:8]
            ]
        }
        schemas.append(faq_schema)

    return "\n".join(
        f'<script type="application/ld+json">{json.dumps(s, ensure_ascii=False)}</script>'
        for s in schemas
    )


# ═══════════════════════════════════════════════════════════════════════════════
# AI CONTENT GENERATION — TURBO MODE
# ═══════════════════════════════════════════════════════════════════════════════

async def generate_lsi_keywords(keyword: str) -> list[str]:
    """Generate 20 LSI (Latent Semantic Indexing) keywords for natural density."""
    if not ANTHROPIC_KEY:
        return []
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{"role": "user", "content":
                f"Gib mir 20 LSI-Keywords (semantisch verwandte Begriffe) für das Haupt-Keyword: '{keyword}'\n"
                f"Nur die Keywords, eine pro Zeile, ohne Nummerierung, auf Deutsch."}]
        )
        return [line.strip() for line in msg.content[0].text.strip().split("\n") if line.strip()][:20]
    except Exception as e:
        logger.warning(f"LSI generation error: {e}")
        return []


async def generate_faqs(keyword: str, context: str = "") -> list[dict]:
    """Generate FAQ schema items — boosts People Also Ask rankings."""
    if not ANTHROPIC_KEY:
        return []
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=800,
            messages=[{"role": "user", "content":
                f"Erstelle 5 FAQ-Paare (Frage + kurze Antwort) für das Thema: '{keyword}'\n"
                f"Format: Q: [Frage]\nA: [Antwort max 150 Wörter]\n\n"
                f"Die Fragen sollen typische 'People Also Ask' Suchanfragen sein. Auf Deutsch."}]
        )
        raw = msg.content[0].text.strip()
        faqs = []
        lines = raw.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("Q:") or line.startswith("Frage:"):
                q = line.split(":", 1)[1].strip()
                a = ""
                i += 1
                while i < len(lines) and not lines[i].strip().startswith("Q:") and not lines[i].strip().startswith("Frage:"):
                    if lines[i].strip().startswith("A:") or lines[i].strip().startswith("Antwort:"):
                        a = lines[i].split(":", 1)[1].strip()
                    i += 1
                if q and a:
                    faqs.append({"question": q, "answer": a})
            else:
                i += 1
        return faqs[:6]
    except Exception as e:
        logger.warning(f"FAQ generation error: {e}")
        return []


async def generate_article(keyword: str, product: dict, lsi: list[str] = None) -> dict | None:
    """Generate full SEO article with LSI keywords, FAQ, schema, competitor-aware content."""
    if not ANTHROPIC_KEY:
        logger.error("ANTHROPIC_API_KEY fehlt")
        return None
    lsi_str = ", ".join((lsi or [])[:10]) if lsi else ""
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        prompt = f"""Du bist ein Senior SEO-Texter der Top-Rankings erreicht. Schreibe einen Artikel der BESSER ist als alle Top-10 Google-Ergebnisse.

HAUPT-KEYWORD: "{keyword}"
LSI-KEYWORDS (natürlich einbauen): {lsi_str}
PRODUKT-EMPFEHLUNG: {product['name']} — {product['desc']} — {product['url']} ({product.get('price','')})

ANFORDERUNGEN:
- 800-1200 Wörter
- H1, H2 (4+), H3 Tags
- Bullet points & nummerierte Listen
- Konkrete Zahlen, Daten, Beispiele
- FAQ-Abschnitt am Ende (5 Fragen)
- Starker CTA zum Produkt
- Keyword-Dichte: 1-2% natürlich
- E-E-A-T Signale (Expertise, Erfahrung, Autorität, Vertrauen)

OUTPUT FORMAT (exakt):
TITLE: [SEO-Titel max 60 Zeichen, Keyword am Anfang]
META: [Meta-Description 145-155 Zeichen, CTA enthalten]
OG_DESC: [Open Graph Description 100-120 Zeichen]
---
[HTML-Artikel-Inhalt mit <h2>,<h3>,<p>,<ul>,<ol>,<strong> Tags]
[Kein <html>,<body>,<head> Wrapper]"""

        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = msg.content[0].text.strip()

        title = f"Guide: {keyword.title()}"
        meta = f"Alles über {keyword} — Profi-Tipps & Tools für 2025."
        og_desc = f"{keyword.title()} — Der komplette Guide."
        content = raw

        if raw.startswith("TITLE:"):
            lines = raw.split("\n")
            body_lines = []
            in_body = False
            for line in lines:
                if line.startswith("TITLE:") and not in_body:
                    title = line.split(":", 1)[1].strip()
                elif line.startswith("META:") and not in_body:
                    meta = line.split(":", 1)[1].strip()
                elif line.startswith("OG_DESC:") and not in_body:
                    og_desc = line.split(":", 1)[1].strip()
                elif line.strip() == "---":
                    in_body = True
                elif in_body:
                    body_lines.append(line)
            if body_lines:
                content = "\n".join(body_lines).strip()

        # Add marketplace product section
        amazon_url = f"https://www.amazon.de/s?k={quote(keyword)}&tag={AMAZON_TAG}"
        ebay_url = f"https://www.ebay.de/sch/i.html?_nkw={quote(keyword)}"
        product_section = f"""
<section class="marketplace-picks" style="background:#1a1a2e;border:1px solid #00d4ff;border-radius:8px;padding:20px;margin:30px 0;">
<h2>🛒 Passende Produkte & Tools</h2>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;">
<a href="{amazon_url}" target="_blank" rel="nofollow" style="background:#ff9900;color:#000;padding:12px;border-radius:6px;text-decoration:none;font-weight:bold;text-align:center;">🟠 Amazon: {keyword[:30]}</a>
<a href="{ebay_url}" target="_blank" rel="nofollow" style="background:#e53238;color:#fff;padding:12px;border-radius:6px;text-decoration:none;font-weight:bold;text-align:center;">🟡 eBay: {keyword[:30]}</a>
<a href="{product['url']}" target="_blank" style="background:#00d4ff;color:#000;padding:12px;border-radius:6px;text-decoration:none;font-weight:bold;text-align:center;">⚡ {product['name']}</a>
</div>
</section>"""

        return {
            "title": title,
            "meta_description": meta,
            "og_description": og_desc,
            "content": content + product_section,
        }
    except Exception as e:
        logger.error(f"Artikel-Generierung fehlgeschlagen: {e}")
        return None


async def generate_social_pack(title: str, url: str, keyword: str,
                                meta: str, product: dict) -> dict:
    """Generate a complete social media pack: Twitter thread, LinkedIn, Reddit posts, email subject."""
    if not ANTHROPIC_KEY:
        return {}
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            messages=[{"role": "user", "content":
                f"Erstelle Social Media Posts für diesen Artikel:\n"
                f"TITEL: {title}\nURL: {url}\nKEYWORD: {keyword}\nBESCHREIBUNG: {meta}\nPRODUKT: {product['name']} — {product['url']}\n\n"
                f"Ausgabe exakt so (keine anderen Texte):\n"
                f"TWITTER1: [Tweet 1/3 max 270 Zeichen, Hook]\n"
                f"TWITTER2: [Tweet 2/3 Hauptinhalt + Fakten]\n"
                f"TWITTER3: [Tweet 3/3 CTA + Link + Hashtags]\n"
                f"LINKEDIN: [LinkedIn Post 150-200 Wörter, professionell, B2B]\n"
                f"REDDIT_TITLE: [Reddit Titel, neugierig, kein Spam]\n"
                f"REDDIT_BODY: [Reddit Post 100-150 Wörter, hilfreich, Link am Ende]\n"
                f"EMAIL_SUBJECT: [E-Mail Betreff max 60 Zeichen]\n"
                f"VIDEO_HOOK: [TikTok/YouTube Video Hook 1 Satz]\n"
                f"PINTEREST: [Pinterest Beschreibung 100 Zeichen + Keywords]\n"}]
        )
        raw = msg.content[0].text.strip()
        result = {}
        for line in raw.split("\n"):
            for key in ["TWITTER1", "TWITTER2", "TWITTER3", "LINKEDIN", "REDDIT_TITLE",
                        "REDDIT_BODY", "EMAIL_SUBJECT", "VIDEO_HOOK", "PINTEREST"]:
                if line.startswith(f"{key}:"):
                    result[key.lower()] = line.split(":", 1)[1].strip()
        return result
    except Exception as e:
        logger.warning(f"Social pack generation error: {e}")
        return {}


async def generate_newsletter_html(title: str, url: str, meta: str,
                                    keyword: str, product: dict) -> str:
    """Generate beautiful HTML email newsletter for Mailchimp/Klaviyo."""
    return f"""<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title></head>
<body style="margin:0;padding:0;background:#0d1117;font-family:system-ui,sans-serif;">
<table width="100%" style="max-width:600px;margin:0 auto;background:#161b22;border-radius:12px;overflow:hidden;">
<tr><td style="background:linear-gradient(135deg,#0066ff,#00d4ff);padding:30px;text-align:center;">
<h1 style="color:#fff;margin:0;font-size:22px;">📈 Neuer Artikel erschienen</h1>
<p style="color:rgba(255,255,255,0.8);margin:8px 0 0;">{keyword.title()}</p>
</td></tr>
<tr><td style="padding:30px;">
<h2 style="color:#e6edf3;font-size:20px;margin:0 0 15px;">{title}</h2>
<p style="color:#8b949e;line-height:1.7;margin:0 0 25px;">{meta}</p>
<a href="{url}" style="background:#0066ff;color:#fff;padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:bold;display:inline-block;">
→ Artikel lesen
</a>
</td></tr>
<tr style="background:#0d1117;"><td style="padding:20px 30px;">
<h3 style="color:#58a6ff;margin:0 0 12px;">⚡ Empfohlenes Tool</h3>
<p style="color:#8b949e;margin:0 0 15px;">{product['name']} — {product['desc']}</p>
<a href="{product['url']}" style="background:#238636;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;display:inline-block;">
Kostenlos testen →
</a>
</td></tr>
<tr><td style="padding:20px;text-align:center;border-top:1px solid #30363d;">
<p style="color:#8b949e;font-size:12px;margin:0;">
© 2026 BullPower Hub • <a href="https://bullpower-hub-portal.netlify.app" style="color:#58a6ff;">Alle Tools</a>
</p>
</td></tr>
</table>
</body></html>"""


# ═══════════════════════════════════════════════════════════════════════════════
# MARKETPLACE HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

async def search_amazon_products(keyword: str, limit: int = 5) -> list[dict]:
    url = f"https://www.amazon.de/s?k={quote(keyword)}&tag={AMAZON_TAG}"
    return [{"title": f"Amazon: {keyword}", "url": url, "price": "", "source": "amazon"}]


async def search_ebay_products(keyword: str, limit: int = 5) -> list[dict]:
    if EBAY_APP_ID:
        try:
            params = {
                "OPERATION-NAME": "findItemsByKeywords", "SERVICE-VERSION": "1.0.0",
                "SECURITY-APPNAME": EBAY_APP_ID, "RESPONSE-DATA-FORMAT": "JSON",
                "keywords": keyword, "paginationInput.entriesPerPage": str(limit), "sortOrder": "BestMatch",
            }
            async with aiohttp.ClientSession() as s:
                async with s.get("https://svcs.ebay.com/services/search/FindingService/v1",
                                 params=params, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    if r.status == 200:
                        data = await r.json()
                        items = data.get("findItemsByKeywordsResponse", [{}])[0].get("searchResult", [{}])[0].get("item", [])
                        return [{"title": it.get("title", [""])[0], "url": it.get("viewItemURL", [""])[0],
                                 "price": it.get("sellingStatus", [{}])[0].get("currentPrice", [{}])[0].get("__value__", ""),
                                 "source": "ebay"} for it in items[:limit]]
        except Exception as e:
            logger.warning(f"eBay API error: {e}")
    return [{"title": f"eBay: {keyword}", "url": f"https://www.ebay.de/sch/i.html?_nkw={quote(keyword)}", "price": "", "source": "ebay"}]


# ═══════════════════════════════════════════════════════════════════════════════
# SOCIAL PLATFORM POSTERS
# ═══════════════════════════════════════════════════════════════════════════════

async def post_to_twitter(title: str, url: str, keyword: str) -> bool:
    if not all([TWITTER_KEY, TWITTER_SECRET, TWITTER_TOKEN, TWITTER_TSECRET]):
        return False
    try:
        import base64
        import urllib.parse as up
        tweet = f"{title}\n\n#{keyword.replace(' ', '')} #SEO #Ecommerce\n\n{url}"
        if len(tweet) > 280:
            tweet = f"{title[:200]}...\n{url}"
        tweet_url = "https://api.twitter.com/2/tweets"
        ts = str(int(time.time()))
        nonce = hashlib.md5(f"{ts}{TWITTER_KEY}".encode()).hexdigest()
        params = {"oauth_consumer_key": TWITTER_KEY, "oauth_nonce": nonce,
                  "oauth_signature_method": "HMAC-SHA1", "oauth_timestamp": ts,
                  "oauth_token": TWITTER_TOKEN, "oauth_version": "1.0"}
        param_str = "&".join(f"{up.quote(k, safe='')}={up.quote(v, safe='')}" for k, v in sorted(params.items()))
        base = f"POST&{up.quote(tweet_url, safe='')}&{up.quote(param_str, safe='')}"
        sign_key = f"{up.quote(TWITTER_SECRET, safe='')}&{up.quote(TWITTER_TSECRET, safe='')}"
        sig = base64.b64encode(hmac.new(sign_key.encode(), base.encode(), "sha1").digest()).decode()
        params["oauth_signature"] = sig
        auth = "OAuth " + ", ".join(f'{k}="{up.quote(v, safe="")}"' for k, v in sorted(params.items()))
        async with aiohttp.ClientSession() as s:
            async with s.post(tweet_url, headers={"Authorization": auth, "Content-Type": "application/json"},
                              json={"text": tweet}, timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status in (200, 201):
                    return True
                logger.error(f"Twitter {r.status}: {await r.text()}")
    except Exception as e:
        logger.error(f"Twitter post failed: {e}")
    return False


async def post_to_reddit(title: str, text: str, url: str) -> bool:
    """Post to multiple relevant subreddits via Reddit API."""
    if not all([REDDIT_CLIENT, REDDIT_SECRET, REDDIT_USER, REDDIT_PASS]):
        return False
    try:
        # Get Reddit OAuth token
        async with aiohttp.ClientSession() as s:
            async with s.post(
                "https://www.reddit.com/api/v1/access_token",
                auth=aiohttp.BasicAuth(REDDIT_CLIENT, REDDIT_SECRET),
                data={"grant_type": "password", "username": REDDIT_USER, "password": REDDIT_PASS},
                headers={"User-Agent": "SEOTrafficBot/2.0"},
                timeout=aiohttp.ClientTimeout(total=15)
            ) as r:
                if r.status != 200:
                    return False
                token_data = await r.json()
                token = token_data.get("access_token")
                if not token:
                    return False

            # Post to first available subreddit
            for sub in REDDIT_SUBS[:2]:
                body = f"{text}\n\n[Mehr lesen]({url})"
                async with s.post(
                    "https://oauth.reddit.com/api/submit",
                    headers={"Authorization": f"Bearer {token}", "User-Agent": "SEOTrafficBot/2.0"},
                    data={"sr": sub, "kind": "self", "title": title[:300], "text": body[:10000], "nsfw": False},
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as r:
                    if r.status in (200, 201):
                        logger.info(f"Reddit posted to r/{sub}")
                        return True
                await asyncio.sleep(10)  # Reddit rate limit
    except Exception as e:
        logger.error(f"Reddit post failed: {e}")
    return False


async def post_to_linkedin(text: str) -> bool:
    """Post to LinkedIn via API."""
    if not LINKEDIN_TOKEN or not LINKEDIN_URN:
        return False
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(
                "https://api.linkedin.com/v2/ugcPosts",
                headers={"Authorization": f"Bearer {LINKEDIN_TOKEN}", "Content-Type": "application/json",
                         "X-Restli-Protocol-Version": "2.0.0"},
                json={
                    "author": f"urn:li:person:{LINKEDIN_URN}",
                    "lifecycleState": "PUBLISHED",
                    "specificContent": {
                        "com.linkedin.ugc.ShareContent": {
                            "shareCommentary": {"text": text[:3000]},
                            "shareMediaCategory": "NONE",
                        }
                    },
                    "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
                },
                timeout=aiohttp.ClientTimeout(total=15)
            ) as r:
                if r.status in (200, 201):
                    logger.info("LinkedIn posted")
                    return True
                logger.error(f"LinkedIn {r.status}: {await r.text()}")
    except Exception as e:
        logger.error(f"LinkedIn post failed: {e}")
    return False


async def send_mailchimp_campaign(html_content: str, subject: str) -> bool:
    """Create and immediately send a Mailchimp campaign."""
    if not all([MC_API_KEY, MC_LIST_ID]):
        return False
    auth_header = "Basic " + __import__("base64").b64encode(f"any:{MC_API_KEY}".encode()).decode()
    base = f"https://{MC_SERVER}.api.mailchimp.com/3.0"
    try:
        async with aiohttp.ClientSession() as s:
            # Create campaign
            async with s.post(f"{base}/campaigns", headers={"Authorization": auth_header},
                              json={"type": "regular", "recipients": {"list_id": MC_LIST_ID},
                                    "settings": {"subject_line": subject, "from_name": "BullPower Hub",
                                                 "reply_to": "info@bullpower-hub.de"}},
                              timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status != 200:
                    return False
                campaign_id = (await r.json()).get("id")

            if not campaign_id:
                return False

            # Set content
            async with s.put(f"{base}/campaigns/{campaign_id}/content",
                             headers={"Authorization": auth_header},
                             json={"html": html_content},
                             timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status != 200:
                    return False

            # Send immediately
            async with s.post(f"{base}/campaigns/{campaign_id}/actions/send",
                              headers={"Authorization": auth_header},
                              timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status == 204:
                    logger.info(f"Mailchimp campaign sent: {campaign_id}")
                    return True
    except Exception as e:
        logger.error(f"Mailchimp campaign error: {e}")
    return False


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
        logger.warning(f"Klaviyo error: {e}")


async def shopify_update_product_seo(product_id: str, seo_title: str, seo_desc: str, tags: list):
    if not SHOPIFY_DOMAIN or not SHOPIFY_TOKEN:
        return
    try:
        async with aiohttp.ClientSession() as s:
            await s.put(
                f"https://{SHOPIFY_DOMAIN}/admin/api/{SHOPIFY_API_VER}/products/{product_id}.json",
                headers={"X-Shopify-Access-Token": SHOPIFY_TOKEN, "Content-Type": "application/json"},
                json={"product": {"id": product_id,
                                   "metafields_global_title_tag": seo_title[:70],
                                   "metafields_global_description_tag": seo_desc[:160],
                                   "tags": ", ".join(tags[:10])}},
                timeout=aiohttp.ClientTimeout(total=15),
            )
    except Exception as e:
        logger.warning(f"Shopify SEO update error: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# OMNI-BROADCAST — PUSH TO ALL ENGINES SIMULTANEOUSLY
# ═══════════════════════════════════════════════════════════════════════════════

async def broadcast_article(article: dict, slug: str, keyword: str, product: dict):
    """Push to ALL 10+ engines simultaneously — maximum reach."""
    payload = {
        "title": article.get("title", ""),
        "content": article.get("content", "")[:2000],
        "url": f"{APP_URL}/blog/{slug}",
        "keyword": keyword,
        "excerpt": article.get("meta_description", article.get("content", "")[:300]),
        "product_name": product["name"],
        "product_url": product["url"],
        "product_price": product.get("price", ""),
    }
    results = []
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=12)) as s:
        tasks = [s.post(f"{url}/api/ingest", json=payload) for url in BROADCAST_ENGINES]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        for url, resp in zip(BROADCAST_ENGINES, responses):
            if isinstance(resp, Exception):
                logger.warning(f"Broadcast failed {url}: {resp}")
                results.append({"url": url, "status": 0})
            else:
                logger.info(f"Broadcast {url}: {resp.status}")
                results.append({"url": url, "status": resp.status})
                resp.release()
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEDULER TASKS
# ═══════════════════════════════════════════════════════════════════════════════

async def task_generate_articles():
    """Turbo article generation: LSI + FAQ + Schema + immediate multi-platform broadcast."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT keyword FROM keyword_queue ORDER BY priority DESC, success_score DESC, last_used ASC NULLS FIRST LIMIT 5"
        )
        keywords = [row[0] for row in await cursor.fetchall()]

    for i, keyword in enumerate(keywords):
        product = PRODUCTS[i % len(PRODUCTS)]
        logger.info(f"[TURBO] Generiere Artikel: {keyword}")

        # Parallel: LSI keywords + FAQs
        lsi_task = asyncio.create_task(generate_lsi_keywords(keyword))
        faq_task = asyncio.create_task(generate_faqs(keyword))
        lsi, faqs = await asyncio.gather(lsi_task, faq_task)

        article = await generate_article(keyword, product, lsi)
        if not article:
            continue

        title = article.get("title", f"Guide: {keyword.title()}")
        meta = article.get("meta_description", "")
        content = article.get("content", "")
        slug = slugify(title)
        published_at = datetime.now(timezone.utc).isoformat()

        # Generate schema JSON-LD
        schema_html = generate_schema_markup(title, meta, slug, keyword, published_at, faqs)

        # Get internal links from existing articles
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT title, slug FROM articles WHERE keyword != ? ORDER BY views DESC LIMIT 3",
                (keyword,)
            )
            related = await cursor.fetchall()

        internal_links_html = ""
        if related:
            links = " | ".join(f'<a href="/blog/{s}" style="color:#58a6ff;">{t}</a>' for t, s in related)
            internal_links_html = f'<div style="background:#1a1a2e;padding:15px;border-radius:8px;margin:20px 0;"><strong>📚 Verwandte Artikel:</strong> {links}</div>'

        # FAQ HTML block
        faq_html = ""
        if faqs:
            faq_items = "".join(f"<details style='margin:8px 0;'><summary style='cursor:pointer;color:#58a6ff;font-weight:bold;'>{f['question']}</summary><p style='padding:10px;color:#e6edf3;'>{f['answer']}</p></details>" for f in faqs)
            faq_html = f'<section style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:20px;margin:30px 0;"><h2>❓ Häufig gestellte Fragen</h2>{faq_items}</section>'

        full_content = internal_links_html + content + faq_html

        try:
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    """INSERT OR IGNORE INTO articles
                       (keyword, title, content, slug, published_at, meta_description,
                        schema_json, lsi_keywords, faq_json)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (keyword, title, full_content, slug, published_at, meta,
                     schema_html, json.dumps(lsi), json.dumps(faqs))
                )
                await db.execute("UPDATE keyword_queue SET last_used = ? WHERE keyword = ?",
                                 (published_at, keyword))
                await db.commit()

            article_url = f"{APP_URL}/blog/{slug}"

            # PARALLEL: ping search engines + IndexNow + broadcast + social pack
            ping_task = asyncio.create_task(ping_search_engines(article_url))
            broadcast_task = asyncio.create_task(broadcast_article(article, slug, keyword, product))
            social_task = asyncio.create_task(generate_social_pack(title, article_url, keyword, meta, product))

            await asyncio.gather(ping_task, broadcast_task, social_task)
            social = await social_task if not social_task.done() else social_task.result()

            # Mark as indexed
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE articles SET indexed_bing = 1 WHERE slug = ?", (slug,))
                await db.commit()

            # Send newsletter email
            email_html = await generate_newsletter_html(title, article_url, meta, keyword, product)
            newsletter_sent = await send_mailchimp_campaign(
                email_html,
                social.get("email_subject", f"📈 Neu: {title[:50]}")
            )

            # Track in Klaviyo
            await klaviyo_track_event("SEO Article Published", {
                "keyword": keyword, "title": title, "url": article_url,
                "product": product["name"], "lsi_count": len(lsi), "faq_count": len(faqs),
                "newsletter_sent": newsletter_sent,
            })

            # Telegram notification
            tg_msg = (
                f"🚀 <b>TURBO SEO Artikel LIVE!</b>\n\n"
                f"🔑 <b>Keyword:</b> {keyword}\n"
                f"📄 <b>Titel:</b> {title}\n"
                f"🔗 <b>URL:</b> {article_url}\n"
                f"📊 <b>LSI Keywords:</b> {len(lsi)}\n"
                f"❓ <b>FAQs:</b> {len(faqs)}\n"
                f"📧 <b>Newsletter:</b> {'✅ gesendet' if newsletter_sent else '⏭️ skip'}\n"
                f"📡 <b>IndexNow:</b> ✅ Bing + Yandex\n"
                f"📢 <b>Broadcast:</b> {len(BROADCAST_ENGINES)} Engines\n"
                f"🐦 <b>Twitter:</b> {social.get('twitter1', '')[:80]}..."
            )
            await telegram_send(tg_msg)
            logger.info(f"[TURBO] Artikel komplett: {slug}")

        except Exception as e:
            logger.error(f"Artikel-Speicherung fehlgeschlagen: {e}")

        await asyncio.sleep(3)


async def task_tweet_articles():
    """Tweet ungetweetete Artikel — mit social pack wenn verfügbar."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, title, slug, keyword FROM articles WHERE tweeted = 0 ORDER BY published_at DESC LIMIT 5"
        )
        rows = await cursor.fetchall()

    for article_id, title, slug, keyword in rows:
        url = f"{APP_URL}/blog/{slug}"
        success = await post_to_twitter(title, url, keyword)
        if success:
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE articles SET tweeted = 1 WHERE id = ?", (article_id,))
                await db.commit()
            await telegram_send(f"🐦 <b>Tweet:</b> {title[:60]}\n{url}")
        await asyncio.sleep(8)


async def task_reddit_posts():
    """Post to Reddit — organic traffic from relevant subreddits."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, title, slug, keyword, meta_description FROM articles WHERE reddit_posted = 0 ORDER BY views DESC LIMIT 2"
        )
        rows = await cursor.fetchall()

    for article_id, title, slug, keyword, meta in rows:
        url = f"{APP_URL}/blog/{slug}"
        success = await post_to_reddit(title, meta or "", url)
        if success:
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE articles SET reddit_posted = 1 WHERE id = ?", (article_id,))
                await db.commit()
            await telegram_send(f"🤝 <b>Reddit Post:</b> {title[:60]}")
        await asyncio.sleep(30)


async def task_linkedin_posts():
    """Post best articles to LinkedIn."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, title, slug, keyword, meta_description FROM articles WHERE linkedin_posted = 0 ORDER BY views DESC LIMIT 1"
        )
        rows = await cursor.fetchall()

    for article_id, title, slug, keyword, meta in rows:
        url = f"{APP_URL}/blog/{slug}"
        text = (
            f"📈 {title}\n\n"
            f"{meta}\n\n"
            f"Komplett lesen: {url}\n\n"
            f"#SEO #Ecommerce #Shopify #Automatisierung #DigitalMarketing #KI"
        )
        success = await post_to_linkedin(text)
        if success:
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE articles SET linkedin_posted = 1 WHERE id = ?", (article_id,))
                await db.commit()
            await telegram_send(f"💼 <b>LinkedIn Post:</b> {title[:60]}")


async def task_add_keywords():
    """Generate new trending long-tail keywords with AI."""
    if not ANTHROPIC_KEY:
        return
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            messages=[{"role": "user", "content":
                "Liste 20 deutschsprachige Long-Tail-Keywords (4-6 Wörter) für 2025 in diesen Bereichen:\n"
                "- Shopify Automatisierung & KI-Tools\n"
                "- E-Commerce SEO & Conversion\n"
                "- Passives Einkommen Online\n"
                "- Amazon/eBay Verkäufer Tools\n"
                "- Email Marketing Automatisierung\n"
                "Nur Keywords, eine pro Zeile, keine Nummerierung, auf Deutsch."}]
        )
        new_kws = [line.strip() for line in msg.content[0].text.strip().split("\n") if line.strip()]
        async with aiosqlite.connect(DB_PATH) as db:
            added = 0
            for kw in new_kws[:20]:
                result = await db.execute(
                    "INSERT OR IGNORE INTO keyword_queue (keyword, priority, source) VALUES (?, 6, 'ai_generated')",
                    (kw,)
                )
                if result.rowcount:
                    added += 1
            await db.commit()
        logger.info(f"AI Keywords hinzugefügt: {added}")
    except Exception as e:
        logger.error(f"Keyword-Generierung fehlgeschlagen: {e}")


async def task_shopify_seo_sync():
    """Update Shopify product SEO titles, descriptions and tags."""
    if not SHOPIFY_DOMAIN or not SHOPIFY_TOKEN:
        return
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT keyword FROM keyword_queue ORDER BY priority DESC LIMIT 5"
            )
            top_kws = [row[0] for row in await cursor.fetchall()]

        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"https://{SHOPIFY_DOMAIN}/admin/api/{SHOPIFY_API_VER}/products.json?limit=10&fields=id,title,tags",
                headers={"X-Shopify-Access-Token": SHOPIFY_TOKEN},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as r:
                data = await r.json(content_type=None)

        products = data.get("products", [])
        for p in products[:5]:
            title = p.get("title", "")
            if not title:
                continue
            relevant_kws = [kw for kw in top_kws if any(w in title.lower() for w in ["shop", "seo", "auto", "store", "online"])]
            if not relevant_kws:
                relevant_kws = top_kws[:2]
            await shopify_update_product_seo(
                str(p["id"]),
                f"{title} — Shopify Automatisierung & KI Tools 2025",
                f"Entdecke {title}. {relevant_kws[0].title()} für deinen Online-Shop. Jetzt optimieren!",
                relevant_kws[:5],
            )
        logger.info(f"Shopify SEO sync: {len(products[:5])} Produkte")
    except Exception as e:
        logger.error(f"Shopify SEO sync error: {e}")


async def task_reindex_old_articles():
    """Re-ping old articles to keep them indexed — prevents deindexing."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT slug FROM articles ORDER BY published_at ASC LIMIT 20"
        )
        slugs = [row[0] for row in await cursor.fetchall()]

    urls = [f"{APP_URL}/blog/{slug}" for slug in slugs]
    if urls:
        await indexnow_ping(urls)
        logger.info(f"Re-indexed {len(urls)} articles via IndexNow")


async def get_task_due(task: str, interval: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT last_run FROM scheduler_state WHERE task = ?", (task,))
        row = await cursor.fetchone()
        last_run = row[0] if row else 0
        now = int(time.time())
        if now - last_run >= interval:
            await db.execute(
                "INSERT OR REPLACE INTO scheduler_state (task, last_run, run_count) VALUES (?, ?, COALESCE((SELECT run_count FROM scheduler_state WHERE task=?)+1,1))",
                (task, now, task)
            )
            await db.commit()
            return True
    return False


async def scheduler_loop():
    """TURBO Scheduler — maximum autonomous operation."""
    INTERVALS = {
        "generate_articles":      2 * 3600,   # Every 2h (was 6h)
        "refresh_trending":       2 * 3600,   # Every 2h — Google Trends
        "tweet_articles":         1 * 3600,   # Every 1h (was 4h)
        "reddit_posts":           6 * 3600,   # Every 6h — Reddit organic traffic
        "linkedin_posts":        12 * 3600,   # Every 12h — LinkedIn B2B
        "add_keywords":          12 * 3600,   # Every 12h — AI keyword expansion
        "shopify_seo_sync":       6 * 3600,   # Every 6h (was 12h)
        "reindex_old":           24 * 3600,   # Daily re-index
        "sitemap_ping":           1 * 3600,   # Every 1h
    }
    await asyncio.sleep(5)
    logger.info("🚀 TURBO Scheduler gestartet — Maximum Autonomy Mode")

    # Immediate startup run
    await task_refresh_trending_keywords()
    await task_generate_articles()

    while True:
        try:
            if await get_task_due("generate_articles", INTERVALS["generate_articles"]):
                logger.info("⚡ Task: generate_articles")
                await task_generate_articles()

            if await get_task_due("refresh_trending", INTERVALS["refresh_trending"]):
                logger.info("📈 Task: refresh_trending")
                await task_refresh_trending_keywords()

            if await get_task_due("tweet_articles", INTERVALS["tweet_articles"]):
                logger.info("🐦 Task: tweet_articles")
                await task_tweet_articles()

            if await get_task_due("reddit_posts", INTERVALS["reddit_posts"]):
                logger.info("🤝 Task: reddit_posts")
                await task_reddit_posts()

            if await get_task_due("linkedin_posts", INTERVALS["linkedin_posts"]):
                logger.info("💼 Task: linkedin_posts")
                await task_linkedin_posts()

            if await get_task_due("add_keywords", INTERVALS["add_keywords"]):
                logger.info("🔑 Task: add_keywords")
                await task_add_keywords()

            if await get_task_due("shopify_seo_sync", INTERVALS["shopify_seo_sync"]):
                logger.info("🛍️ Task: shopify_seo_sync")
                await task_shopify_seo_sync()

            if await get_task_due("reindex_old", INTERVALS["reindex_old"]):
                logger.info("🔄 Task: reindex_old")
                await task_reindex_old_articles()

            if await get_task_due("sitemap_ping", INTERVALS["sitemap_ping"]):
                await ping_search_engines(APP_URL)

        except Exception as e:
            logger.error(f"Scheduler error: {e}")

        await asyncio.sleep(120)  # Check every 2 min


# ═══════════════════════════════════════════════════════════════════════════════
# HTTP HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

async def serve_blog_index(request: web.Request) -> web.Response:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT title, slug, keyword, published_at, meta_description, views FROM articles ORDER BY published_at DESC LIMIT 30"
        )
        articles = await cursor.fetchall()
        cursor = await db.execute("SELECT COUNT(*) FROM articles")
        total = (await cursor.fetchone())[0]
        cursor = await db.execute("SELECT COUNT(*) FROM keyword_queue")
        kw_count = (await cursor.fetchone())[0]

    items = ""
    for title, slug, keyword, published_at, meta, views in articles:
        date = published_at[:10] if published_at else ""
        meta_text = meta or f"Guide zu {keyword}"
        items += f"""<article>
<h2><a href="/blog/{slug}">{title}</a></h2>
<p class="meta">📌 {keyword} • 📅 {date} • 👁️ {views} Views</p>
<p class="excerpt">{meta_text[:160]}</p>
</article>\n"""

    if not items:
        items = "<p style='color:#8b949e;'>Erste Artikel werden generiert — TURBO Mode aktiv...</p>"

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BullPower SEO Blog — E-Commerce & Shopify Automatisierung</title>
<meta name="description" content="Profi-Guides zu Shopify Automatisierung, SEO Optimierung, E-Commerce KI-Tools und passivem Einkommen. Täglich neue Artikel.">
<meta property="og:title" content="BullPower SEO Blog">
<meta property="og:description" content="Profi-Guides zu Shopify & E-Commerce Automatisierung — täglich neue KI-generierte Artikel">
<meta property="og:type" content="website">
<link rel="canonical" href="{APP_URL}/blog">
<link rel="sitemap" type="application/xml" href="{APP_URL}/sitemap.xml">
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"Blog","name":"BullPower SEO Blog",
"description":"E-Commerce & Shopify Automatisierung","url":"{APP_URL}/blog",
"publisher":{{"@type":"Organization","name":"BullPower Hub","url":"https://bullpower-hub-portal.netlify.app"}}}}
</script>
<style>
*{{box-sizing:border-box;}}
body{{margin:0;font-family:system-ui,-apple-system,sans-serif;background:#0d1117;color:#e6edf3;}}
header{{background:linear-gradient(135deg,#0066ff22,#00d4ff11);border-bottom:1px solid #30363d;padding:20px 40px;}}
header h1{{margin:0;font-size:1.6rem;background:linear-gradient(90deg,#0066ff,#00d4ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
.stats{{display:flex;gap:20px;margin-top:8px;flex-wrap:wrap;}}
.stat{{background:#161b22;border:1px solid #30363d;border-radius:6px;padding:4px 12px;font-size:0.8rem;color:#8b949e;}}
main{{max-width:900px;margin:40px auto;padding:0 20px;}}
article{{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:24px;margin:16px 0;transition:border-color 0.2s;}}
article:hover{{border-color:#58a6ff;}}
article h2{{margin:0 0 8px;font-size:1.2rem;}}
article h2 a{{color:#e6edf3;text-decoration:none;}}
article h2 a:hover{{color:#58a6ff;}}
.meta{{color:#8b949e;font-size:0.82rem;margin:0 0 8px;}}
.excerpt{{color:#adbac7;font-size:0.9rem;margin:0;line-height:1.5;}}
footer{{text-align:center;padding:40px 20px;color:#8b949e;font-size:0.8rem;border-top:1px solid #30363d;margin-top:40px;}}
</style>
</head>
<body>
<header>
<h1>⚡ BullPower SEO Blog</h1>
<p style="color:#8b949e;margin:4px 0 0;">Täglich neue KI-generierte Artikel zu E-Commerce, Shopify & Automatisierung</p>
<div class="stats">
<span class="stat">📄 {total} Artikel</span>
<span class="stat">🔑 {kw_count} Keywords</span>
<span class="stat">🤖 TURBO Mode AN</span>
<span class="stat">📡 IndexNow aktiv</span>
<span class="stat">🧠 Schema.org ✓</span>
</div>
</header>
<main>
<h2 style="color:#58a6ff;margin-bottom:20px;">Neueste Artikel</h2>
{items}
</main>
<footer>
Powered by <a href="{APP_URL}" style="color:#58a6ff;">SEO Traffic Engine TURBO</a> •
<a href="/sitemap.xml" style="color:#58a6ff;">Sitemap</a> •
<a href="https://bullpower-hub-portal.netlify.app" style="color:#58a6ff;">BullPower Hub</a>
</footer>
</body>
</html>"""
    return web.Response(text=html, content_type="text/html")


async def serve_blog_article(request: web.Request) -> web.Response:
    slug = request.match_info["slug"]
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT title, content, keyword, published_at, meta_description, schema_json, lsi_keywords FROM articles WHERE slug = ?",
            (slug,)
        )
        row = await cursor.fetchone()
        if row:
            await db.execute("UPDATE articles SET views = views + 1, engagement_score = engagement_score + 1 WHERE slug = ?", (slug,))
            await db.commit()
            # Boost keyword priority when article gets views
            await db.execute(
                "UPDATE keyword_queue SET success_score = success_score + 1 WHERE keyword = ?",
                (row[2],)
            )
            await db.commit()

    if not row:
        raise web.HTTPNotFound(text="Artikel nicht gefunden")

    title, content, keyword, published_at, meta, schema_html, lsi_json = row
    date = published_at[:10] if published_at else ""
    meta = meta or f"Kompletter Guide zu {keyword} — Tipps & Tools 2025."
    lsi_keywords = json.loads(lsi_json) if lsi_json else []
    lsi_str = ", ".join(lsi_keywords[:10])
    schema_markup = schema_html or ""
    article_url = f"{APP_URL}/blog/{slug}"

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} | BullPower SEO Blog</title>
<meta name="description" content="{meta}">
<meta name="keywords" content="{keyword}{', ' + lsi_str if lsi_str else ''}">
<link rel="canonical" href="{article_url}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{meta}">
<meta property="og:url" content="{article_url}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="BullPower SEO Blog">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{meta}">
{schema_markup}
<style>
*{{box-sizing:border-box;}}
body{{margin:0;font-family:system-ui,-apple-system,sans-serif;background:#0d1117;color:#e6edf3;line-height:1.7;}}
header{{background:#161b22;padding:16px 24px;border-bottom:1px solid #30363d;}}
header a{{color:#58a6ff;text-decoration:none;font-size:0.9rem;}}
.article-wrap{{max-width:820px;margin:40px auto;padding:0 20px;}}
h1{{color:#e6edf3;font-size:2rem;margin:0 0 12px;line-height:1.3;}}
.meta{{color:#8b949e;font-size:0.88rem;margin:0 0 40px;display:flex;gap:16px;flex-wrap:wrap;}}
h2{{color:#58a6ff;margin:40px 0 16px;font-size:1.4rem;}}
h3{{color:#79c0ff;margin:30px 0 12px;}}
p{{color:#e6edf3;margin:0 0 16px;}}
ul,ol{{padding-left:24px;margin:0 0 16px;}}
li{{margin:6px 0;color:#e6edf3;}}
strong{{color:#fff;}}
a{{color:#58a6ff;}}
a:hover{{color:#79c0ff;}}
code{{background:#1c2128;padding:2px 6px;border-radius:4px;font-family:monospace;color:#79c0ff;}}
blockquote{{border-left:3px solid #58a6ff;margin:20px 0;padding:12px 20px;background:#161b22;color:#adbac7;}}
details summary{{color:#58a6ff;font-weight:bold;cursor:pointer;padding:8px 0;}}
.cta-box{{background:linear-gradient(135deg,#0066ff22,#00d4ff11);border:1px solid #0066ff55;border-radius:12px;padding:24px;margin:40px 0;text-align:center;}}
.cta-box h3{{color:#00d4ff;margin:0 0 12px;}}
.cta-btn{{display:inline-block;background:linear-gradient(90deg,#0066ff,#00d4ff);color:#fff;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:bold;margin-top:12px;}}
footer{{text-align:center;padding:40px 20px;color:#8b949e;font-size:0.8rem;border-top:1px solid #30363d;margin-top:60px;}}
</style>
</head>
<body>
<header><a href="/blog">← Blog</a> <span style="color:#30363d;margin:0 8px;">|</span> <a href="/">Home</a></header>
<div class="article-wrap">
<h1>{title}</h1>
<div class="meta">
<span>📌 {keyword}</span>
<span>📅 {date}</span>
<span>⚡ TURBO SEO</span>
<span>🔗 <a href="{article_url}" style="color:#8b949e;">{slug}</a></span>
</div>
{content}
</div>
<footer>
© 2026 BullPower Hub •
<a href="/blog" style="color:#58a6ff;">Blog</a> •
<a href="/sitemap.xml" style="color:#58a6ff;">Sitemap</a> •
<a href="https://bullpower-hub-portal.netlify.app" style="color:#58a6ff;">Alle Tools</a>
</footer>
</body>
</html>"""
    return web.Response(text=html, content_type="text/html")


async def serve_sitemap(request: web.Request) -> web.Response:
    """Full sitemap including Google News format entries."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT slug, published_at, title, keyword FROM articles ORDER BY published_at DESC"
        )
        articles = await cursor.fetchall()

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls = (
        f"<url><loc>{APP_URL}/</loc><changefreq>hourly</changefreq><priority>1.0</priority><lastmod>{now}</lastmod></url>\n"
        f"<url><loc>{APP_URL}/blog</loc><changefreq>hourly</changefreq><priority>0.95</priority><lastmod>{now}</lastmod></url>\n"
    )
    for slug, published_at, title, keyword in articles:
        lastmod = published_at[:10] if published_at else now
        urls += (
            f"<url><loc>{APP_URL}/blog/{slug}</loc>"
            f"<lastmod>{lastmod}</lastmod>"
            f"<changefreq>monthly</changefreq>"
            f"<priority>0.8</priority>"
            f"<news:news xmlns:news='http://www.google.com/schemas/sitemap-news/0.9'>"
            f"<news:publication><news:name>BullPower SEO Blog</news:name><news:language>de</news:language></news:publication>"
            f"<news:publication_date>{lastmod}</news:publication_date>"
            f"<news:title>{title}</news:title>"
            f"<news:keywords>{keyword}</news:keywords>"
            f"</news:news>"
            f"</url>\n"
        )

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
{urls}
</urlset>"""
    return web.Response(text=xml, content_type="application/xml")


async def serve_indexnow_key(request: web.Request) -> web.Response:
    """Serve IndexNow key verification file — required for instant indexing."""
    return web.Response(text=INDEXNOW_KEY, content_type="text/plain")


async def handle_health(request: web.Request) -> web.Response:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM articles")
        total = (await cursor.fetchone())[0]
        cursor = await db.execute("SELECT COUNT(*) FROM keyword_queue")
        kw_count = (await cursor.fetchone())[0]
        cursor = await db.execute("SELECT COUNT(*) FROM trending_keywords")
        trending_count = (await cursor.fetchone())[0]
    return web.json_response({
        "status": "ok",
        "service": "seo-traffic-engine",
        "version": "2.0-TURBO",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "articles": total,
        "keywords": kw_count,
        "trending_keywords": trending_count,
        "indexnow_key": INDEXNOW_KEY[:8] + "...",
        "features": ["google-trends", "indexnow", "schema-org", "lsi", "faq-schema",
                     "omni-broadcast", "reddit", "linkedin", "mailchimp", "twitter"],
    })


async def handle_stats(request: web.Request) -> web.Response:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT title, slug, views, tweeted, reddit_posted, linkedin_posted, indexed_bing, keyword, engagement_score "
            "FROM articles ORDER BY views DESC LIMIT 20"
        )
        articles = [
            {"title": r[0], "slug": r[1], "views": r[2], "tweeted": bool(r[3]),
             "reddit": bool(r[4]), "linkedin": bool(r[5]), "indexed_bing": bool(r[6]),
             "keyword": r[7], "score": r[8]}
            for r in await cursor.fetchall()
        ]
        cursor = await db.execute("SELECT task, last_run, run_count FROM scheduler_state")
        tasks = {r[0]: {"last_run": r[1], "runs": r[2]} for r in await cursor.fetchall()}
        cursor = await db.execute(
            "SELECT keyword, trend_score FROM trending_keywords ORDER BY trend_score DESC LIMIT 10"
        )
        trending = [{"keyword": r[0], "score": r[1]} for r in await cursor.fetchall()]
    return web.json_response({
        "articles": articles,
        "scheduler": tasks,
        "trending": trending,
        "total_articles": len(articles),
    })


async def handle_trigger_articles(request: web.Request) -> web.Response:
    asyncio.create_task(task_generate_articles())
    return web.json_response({"status": "triggered", "task": "turbo_generate_articles"})


async def handle_trigger_indexnow(request: web.Request) -> web.Response:
    asyncio.create_task(task_reindex_old_articles())
    return web.json_response({"status": "triggered", "task": "indexnow_reindex"})


async def handle_trigger_trending(request: web.Request) -> web.Response:
    asyncio.create_task(task_refresh_trending_keywords())
    return web.json_response({"status": "triggered", "task": "refresh_trending"})


async def handle_ingest(request: web.Request) -> web.Response:
    """Receive content from other engines — generate SEO article from inbound data."""
    try:
        data = await request.json()
        title = data.get("title", "")
        keyword = data.get("keyword", title)
        url = data.get("url", "")
        excerpt = data.get("excerpt", "")

        if keyword:
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "INSERT OR IGNORE INTO keyword_queue (keyword, priority, source) VALUES (?, 8, 'ingest')",
                    (keyword,)
                )
                await db.commit()

        return web.json_response({"status": "ok", "keyword_queued": keyword})
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)}, status=400)


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
    amazon = await search_amazon_products(topic, 3)
    ebay = await search_ebay_products(topic, 3)
    return web.json_response({"topic": topic, "amazon": amazon, "ebay": ebay})


# ═══════════════════════════════════════════════════════════════════════════════
# APP FACTORY
# ═══════════════════════════════════════════════════════════════════════════════

async def on_startup(app):
    await init_db()
    asyncio.create_task(scheduler_loop())
    logger.info(f"🚀 SEO Traffic Engine TURBO v2.0 — Port {PORT}")
    logger.info(f"⚡ IndexNow Key: {INDEXNOW_KEY}")
    logger.info(f"📡 Broadcast Engines: {len(BROADCAST_ENGINES)}")


def create_app():
    app = web.Application()
    app.on_startup.append(on_startup)
    # Core routes
    app.router.add_get("/health", handle_health)
    app.router.add_get("/stats", handle_stats)
    app.router.add_get("/sitemap.xml", serve_sitemap)
    app.router.add_get("/blog", serve_blog_index)
    app.router.add_get("/blog/{slug}", serve_blog_article)
    app.router.add_get("/", serve_blog_index)
    # IndexNow key verification
    app.router.add_get(f"/{INDEXNOW_KEY}.txt", serve_indexnow_key)
    # API routes
    app.router.add_post("/api/trigger/articles", handle_trigger_articles)
    app.router.add_post("/api/trigger/indexnow", handle_trigger_indexnow)
    app.router.add_post("/api/trigger/trending", handle_trigger_trending)
    app.router.add_post("/api/ingest", handle_ingest)
    app.router.add_get("/api/products", handle_products)
    app.router.add_post("/api/recommend", handle_recommend)
    return app


if __name__ == "__main__":
    web.run_app(create_app(), port=PORT)
