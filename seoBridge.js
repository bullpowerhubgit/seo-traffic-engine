'use strict';
/**
 * SEO Bridge — connect any Node.js service to the SEO Traffic Engine.
 * Usage: const SEOBridge = require('./seoBridge');
 *        const bridge = new SEOBridge({ projectName: 'my-app', keywords: ['shopify'] });
 *        bridge.startBackgroundSync();
 */
const https = require('https');
const http = require('http');

const SEO_ENGINE_URL = process.env.SEO_ENGINE_URL || 'https://seo-traffic-engine-production.up.railway.app';

class SEOBridge {
    constructor({ projectName, keywords = [], intervalHours = 6 } = {}) {
        this.projectName = projectName;
        this.keywords = keywords;
        this.interval = intervalHours * 3600 * 1000;
        this._timer = null;
    }

    async _fetch(method, path, body = null) {
        const url = new URL(path, SEO_ENGINE_URL);
        const isHttps = url.protocol === 'https:';
        const lib = isHttps ? https : http;
        return new Promise((resolve, reject) => {
            const opts = {
                hostname: url.hostname,
                port: url.port || (isHttps ? 443 : 80),
                path: url.pathname + url.search,
                method,
                headers: { 'Content-Type': 'application/json' },
                timeout: 10000,
            };
            const payload = body ? JSON.stringify(body) : null;
            if (payload) opts.headers['Content-Length'] = Buffer.byteLength(payload);
            const req = lib.request(opts, (res) => {
                let data = '';
                res.on('data', c => data += c);
                res.on('end', () => {
                    try { resolve(JSON.parse(data)); }
                    catch { resolve({}); }
                });
            });
            req.on('error', reject);
            req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
            if (payload) req.write(payload);
            req.end();
        });
    }

    async pushKeywords(keywords) {
        const kws = keywords || this.keywords;
        const results = [];
        for (const kw of kws) {
            try {
                await this._fetch('POST', '/api/trigger/articles', { keyword: kw, project: this.projectName });
                results.push({ keyword: kw, ok: true });
            } catch (e) {
                results.push({ keyword: kw, ok: false, error: e.message });
            }
        }
        return results;
    }

    async getProducts(keyword, source = 'all') {
        try {
            const path = `/api/products?keyword=${encodeURIComponent(keyword)}&source=${source}`;
            const data = await this._fetch('GET', path);
            return data.products || [];
        } catch (e) { return []; }
    }

    async getRecommendations(topic) {
        try {
            return await this._fetch('POST', '/api/recommend', { topic, limit: 5 });
        } catch (e) { return { topic, amazon: [], ebay: [], total: 0 }; }
    }

    async getStats() {
        try {
            return await this._fetch('GET', '/stats');
        } catch (e) { return {}; }
    }

    startBackgroundSync() {
        const sync = async () => {
            try {
                await this.pushKeywords();
                console.log(`[SEOBridge] Synced ${this.keywords.length} keywords for ${this.projectName}`);
            } catch (e) {
                console.warn('[SEOBridge] Sync error:', e.message);
            }
        };
        // First sync after 2 minutes
        setTimeout(sync, 120000);
        this._timer = setInterval(sync, this.interval);
        return this;
    }

    // Add Express.js routes
    addExpressRoutes(app) {
        app.get('/api/seo', async (req, res) => {
            const stats = await this.getStats();
            res.json({
                project: this.projectName,
                seo_engine: SEO_ENGINE_URL,
                articles_tracked: (stats.articles || []).length,
                keywords: this.keywords.slice(0, 10),
                top_articles: (stats.articles || []).slice(0, 5),
            });
        });
        app.get('/api/seo/products', async (req, res) => {
            const keyword = req.query.keyword || this.keywords[0] || 'shopify';
            const products = await this.getProducts(keyword);
            res.json({ keyword, products });
        });
    }
}

module.exports = SEOBridge;
