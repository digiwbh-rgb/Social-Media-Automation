/**
 * API client with automatic fallback to localStorage-backed mock data.
 *
 * Auto-detection: on startup the client sends a quick GET /api/ping.
 * If the Flask server responds, all calls go to the real backend.
 * Otherwise every call is handled locally (localStorage + MOCK_* constants).
 */

const API_BASE  = 'http://localhost:8080';
const LS_POSTS  = 'sma_posts';
const LS_GEN    = 'sma_generated';

const Api = (() => {
  let _online = false;

  // ── Connectivity ──────────────────────────────────────────────────────

  async function detect() {
    try {
      const r = await fetch(`${API_BASE}/api/ping`, { signal: AbortSignal.timeout(1500) });
      _online = r.ok;
    } catch {
      _online = false;
    }
    _updateBadge();
    return _online;
  }

  function isOnline() { return _online; }

  function _updateBadge() {
    const badge = document.getElementById('api-badge');
    const label = document.getElementById('api-label');
    if (!badge) return;
    if (_online) {
      badge.classList.add('online');
      label.textContent = 'live';
    } else {
      badge.classList.remove('online');
      label.textContent = 'offline';
    }
  }

  // ── Local storage helpers ─────────────────────────────────────────────

  function _loadPosts() {
    try {
      const raw = localStorage.getItem(LS_POSTS);
      return raw ? JSON.parse(raw) : JSON.parse(JSON.stringify(MOCK_POSTS));
    } catch { return JSON.parse(JSON.stringify(MOCK_POSTS)); }
  }

  function _savePosts(posts) {
    localStorage.setItem(LS_POSTS, JSON.stringify(posts));
  }

  function _loadGen() {
    try {
      const raw = localStorage.getItem(LS_GEN);
      return raw ? JSON.parse(raw) : JSON.parse(JSON.stringify(MOCK_GENERATED));
    } catch { return JSON.parse(JSON.stringify(MOCK_GENERATED)); }
  }

  function _saveGen(items) {
    localStorage.setItem(LS_GEN, JSON.stringify(items));
  }

  function _nextId(items) {
    return items.reduce((max, i) => Math.max(max, i.id ?? 0), 0) + 1;
  }

  // ── Core fetch wrapper ────────────────────────────────────────────────

  async function _fetch(path, opts = {}) {
    const r = await fetch(`${API_BASE}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...opts,
      body: opts.body ? JSON.stringify(opts.body) : undefined,
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({ error: r.statusText }));
      throw new Error(err.error || `HTTP ${r.status}`);
    }
    return r.json();
  }

  // ── Stats ─────────────────────────────────────────────────────────────

  async function getStats() {
    if (_online) return _fetch('/api/stats');
    const posts = _loadPosts();
    const count = (s) => posts.filter(p => p.status === s).length;
    const pending = posts
      .filter(p => p.status === 'pending')
      .sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at));
    return {
      total:     posts.length,
      pending:   count('pending'),
      published: count('published'),
      failed:    count('failed'),
      cancelled: count('cancelled'),
      next_due:  pending[0]?.scheduled_at ?? null,
    };
  }

  // ── Posts ─────────────────────────────────────────────────────────────

  async function getPosts({ platform, status, limit = 100 } = {}) {
    if (_online) {
      const params = new URLSearchParams();
      if (platform && platform !== 'all') params.set('platform', platform);
      if (status   && status   !== 'all') params.set('status',   status);
      params.set('limit', limit);
      return _fetch(`/api/posts?${params}`);
    }
    let posts = _loadPosts();
    if (platform && platform !== 'all') posts = posts.filter(p => p.platform === platform);
    if (status   && status   !== 'all') posts = posts.filter(p => p.status   === status);
    return posts.sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at)).slice(0, limit);
  }

  async function getPost(id) {
    if (_online) return _fetch(`/api/posts/${id}`);
    return _loadPosts().find(p => p.id === id) ?? null;
  }

  async function createPost({ platform, content, scheduled_at }) {
    if (_online) return _fetch('/api/posts', { method: 'POST', body: { platform, content, scheduled_at } });
    const posts = _loadPosts();
    const post = {
      id: _nextId(posts),
      platform,
      content,
      scheduled_at,
      status: 'pending',
      published_at: null,
      platform_id: null,
      error_message: null,
      retry_count: 0,
      created_at: new Date().toISOString(),
    };
    _savePosts([...posts, post]);
    return post;
  }

  async function cancelPost(id) {
    if (_online) return _fetch(`/api/posts/${id}/cancel`, { method: 'POST' });
    const posts = _loadPosts();
    const post  = posts.find(p => p.id === id);
    if (!post) throw new Error(`Post #${id} not found`);
    if (post.status !== 'pending') throw new Error(`Post #${id} is ${post.status}, cannot cancel`);
    post.status = 'cancelled';
    _savePosts(posts);
    return post;
  }

  async function deletePost(id) {
    if (_online) return _fetch(`/api/posts/${id}`, { method: 'DELETE' });
    const posts = _loadPosts();
    const idx   = posts.findIndex(p => p.id === id);
    if (idx < 0) throw new Error(`Post #${id} not found`);
    posts.splice(idx, 1);
    _savePosts(posts);
    return { ok: true };
  }

  async function publishNow({ platform, content }) {
    if (_online) return _fetch('/api/publish-now', { method: 'POST', body: { platform, content } });
    // Offline simulation: create a post and immediately "publish" it
    const posts = _loadPosts();
    const post  = {
      id: _nextId(posts),
      platform,
      content,
      scheduled_at: new Date().toISOString(),
      status: 'published',
      published_at: new Date().toISOString(),
      platform_id: `mock_${Date.now()}`,
      error_message: null,
      retry_count: 0,
      created_at: new Date().toISOString(),
    };
    _savePosts([...posts, post]);
    return { platform_id: post.platform_id };
  }

  // ── Scheduler ─────────────────────────────────────────────────────────

  async function runOnce() {
    if (_online) return _fetch('/api/scheduler/run-once', { method: 'POST' });
    // Offline: simulate the scheduler tick
    const posts   = _loadPosts();
    const now     = new Date();
    const due     = posts.filter(p => p.status === 'pending' && new Date(p.scheduled_at) <= now);
    const logs    = [];
    let published = 0;
    due.forEach(p => {
      p.status       = 'published';
      p.published_at = new Date().toISOString();
      p.platform_id  = `mock_${Date.now()}_${p.id}`;
      published++;
      logs.push({ level: 'success', msg: `Post #${p.id} published on ${p.platform} (mock)` });
    });
    if (due.length === 0) logs.push({ level: 'info', msg: 'No posts due right now.' });
    _savePosts(posts);
    return { published, logs };
  }

  // ── Generated content ─────────────────────────────────────────────────

  async function getGeneratedContent({ platform, unused_only } = {}) {
    if (_online) {
      const p = new URLSearchParams();
      if (platform && platform !== 'all') p.set('platform', platform);
      if (unused_only) p.set('unused_only', '1');
      return _fetch(`/api/generated?${p}`);
    }
    let items = _loadGen();
    if (platform && platform !== 'all') items = items.filter(g => g.platform === platform);
    if (unused_only) items = items.filter(g => !g.used);
    return items.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  }

  async function generateContent({ platform, topic, tone, context, variants }) {
    if (_online) {
      return _fetch('/api/generate', { method: 'POST', body: { platform, topic, tone, context, variants } });
    }
    // Offline: return plausible-looking stubs
    const templates = {
      twitter: {
        professional: `${topic}: here's what the data actually shows. Thread incoming 🧵 #${topic.replace(/\s+/g,'').substring(0,12)}`,
        casual:       `ok so ${topic} just changed everything for me. no cap 👀`,
        humorous:     `me: I'll just quickly research ${topic}\nalso me: *3 hours later* 🤡`,
        inspirational:`You don't need to master ${topic} overnight. One step, consistently, beats ten steps sporadically. 💡`,
        educational:  `${topic} explained in one tweet:\n\n→ [key insight]\n→ [common mistake]\n→ [actionable takeaway]\n\nSave this. 📌`,
      },
      linkedin: {
        professional: `${topic} is reshaping how professionals operate.\n\nAfter months of research, here are three insights worth sharing:\n\n1. [First insight]\n2. [Second insight]\n3. [Third insight]\n\nWhat's your experience with ${topic}?`,
        casual:       `Real talk about ${topic}:\n\nI used to think it was complicated. Turns out I was overcomplicating it.\n\nHere's the simple version...`,
        inspirational:`${topic} taught me the most important lesson of my career:\n\nProgress compounds. Every small step adds up.\n\nWhat lesson has shaped your professional journey?`,
        educational:  `Everything you need to know about ${topic} in under 60 seconds:\n\n✅ What it is\n✅ Why it matters\n✅ How to start today\n\n[Thread below ↓]`,
        humorous:     `My relationship with ${topic}:\n\nYear 1: "What is this?"\nYear 2: "I sort of get it"\nYear 3: "I've been doing it wrong"\nNow: "OK, THIS time I understand it"\n\nAnyone else? 😅`,
      },
    };
    const plat = platform || 'twitter';
    const t    = tone || 'professional';
    const base = templates[plat]?.[t] || `Sample content about ${topic} for ${plat}.`;

    const results = [];
    for (let i = 0; i < (variants || 1); i++) {
      const content = i === 0 ? base : `${base} (variant ${i + 1})`;
      const item = {
        id: _nextId(_loadGen()) + i,
        topic,
        platform: plat,
        tone: t,
        content,
        used: false,
        created_at: new Date().toISOString(),
      };
      results.push(item);
    }

    const gen = _loadGen();
    _saveGen([...results, ...gen]);
    return results;
  }

  async function scheduleFromGenerated(gcId, scheduledAt) {
    if (_online) return _fetch('/api/generated/schedule', { method: 'POST', body: { id: gcId, scheduled_at: scheduledAt } });
    const gen  = _loadGen();
    const item = gen.find(g => g.id === gcId);
    if (!item) throw new Error('Generated content not found');
    item.used = true;
    _saveGen(gen);
    return createPost({ platform: item.platform, content: item.content, scheduled_at: scheduledAt });
  }

  // ── Config ────────────────────────────────────────────────────────────

  async function getConfig() {
    if (_online) return _fetch('/api/config');
    // Return empty config (never store real keys in localStorage)
    return {
      twitter:  { api_key: '', api_secret: '', bearer_token: '', access_token: '', access_token_secret: '' },
      linkedin: { client_id: '', client_secret: '', access_token: '', person_urn: '' },
      claude:   { api_key: '', model: 'claude-sonnet-4-6', max_tokens: 1024 },
      db_path:  '~/.social_media_automation/posts.db',
      scheduler_interval: 60,
    };
  }

  async function saveConfig(data) {
    if (_online) return _fetch('/api/config', { method: 'POST', body: data });
    return { ok: true, note: 'Config saved in-memory only (server offline). Use env vars for persistence.' };
  }

  async function verifyPlatform(platform) {
    if (_online) return _fetch(`/api/config/verify/${platform}`, { method: 'POST' });
    return { ok: false, message: 'Cannot verify credentials while server is offline.' };
  }

  return {
    detect, isOnline,
    getStats,
    getPosts, getPost, createPost, cancelPost, deletePost, publishNow,
    runOnce,
    getGeneratedContent, generateContent, scheduleFromGenerated,
    getConfig, saveConfig, verifyPlatform,
  };
})();
