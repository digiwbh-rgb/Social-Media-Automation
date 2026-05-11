/**
 * Social Media Automation — Dashboard SPA
 * Single-file vanilla JS. No build step, no dependencies.
 */

// ── State ──────────────────────────────────────────────────────────────────
const State = {
  view:      'overview',
  posts:     [],
  generated: [],
  stats:     null,
  config:    null,
  filters:   { platform: 'all', status: 'all' },
  schedulerLog: [],
};

// ── Icons (inline SVG strings) ─────────────────────────────────────────────
const ICONS = {
  twitter:  `<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.741l7.735-8.835L1.254 2.25H8.08l4.253 5.622zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>`,
  linkedin: `<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>`,
  copy:     `<svg width="13" height="13" viewBox="0 0 16 16" fill="currentColor"><path d="M4 1.5H3a2 2 0 00-2 2V14a2 2 0 002 2h10a2 2 0 002-2V3.5a2 2 0 00-2-2h-1v1h1a1 1 0 011 1V14a1 1 0 01-1 1H3a1 1 0 01-1-1V3.5a1 1 0 011-1h1v-1z"/><path d="M9.5 1a.5.5 0 01.5.5v1a.5.5 0 01-.5.5h-3a.5.5 0 01-.5-.5v-1a.5.5 0 01.5-.5h3zm-3-1A1.5 1.5 0 005 1.5v1A1.5 1.5 0 006.5 4h3A1.5 1.5 0 0011 2.5v-1A1.5 1.5 0 009.5 0h-3z"/></svg>`,
  trash:    `<svg width="13" height="13" viewBox="0 0 16 16" fill="currentColor"><path d="M5.5 5.5A.5.5 0 016 6v6a.5.5 0 01-1 0V6a.5.5 0 01.5-.5zm2.5 0a.5.5 0 01.5.5v6a.5.5 0 01-1 0V6a.5.5 0 01.5-.5zm3 .5a.5.5 0 00-1 0v6a.5.5 0 001 0V6z"/><path fill-rule="evenodd" d="M14.5 3a1 1 0 01-1 1H13v9a2 2 0 01-2 2H5a2 2 0 01-2-2V4h-.5a1 1 0 01-1-1V2a1 1 0 011-1H6a1 1 0 011-1h2a1 1 0 011 1h3.5a1 1 0 011 1v1zM4.118 4L4 4.059V13a1 1 0 001 1h6a1 1 0 001-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/></svg>`,
  eye:      `<svg width="13" height="13" viewBox="0 0 16 16" fill="currentColor"><path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zM1.173 8a13.133 13.133 0 011.66-2.043C4.12 4.668 5.88 3.5 8 3.5c2.12 0 3.879 1.168 5.168 2.457A13.133 13.133 0 0114.828 8c-.058.087-.122.183-.195.288-.335.48-.83 1.12-1.465 1.755C11.879 11.332 10.119 12.5 8 12.5c-2.12 0-3.879-1.168-5.168-2.457A13.134 13.134 0 011.172 8z"/><path d="M8 5.5a2.5 2.5 0 100 5 2.5 2.5 0 000-5zM4.5 8a3.5 3.5 0 117 0 3.5 3.5 0 01-7 0z"/></svg>`,
  calendar: `<svg width="13" height="13" viewBox="0 0 16 16" fill="currentColor"><path d="M3.5 0a.5.5 0 01.5.5V1h8V.5a.5.5 0 011 0V1h1a2 2 0 012 2v11a2 2 0 01-2 2H2a2 2 0 01-2-2V3a2 2 0 012-2h1V.5a.5.5 0 01.5-.5zM1 4v10a1 1 0 001 1h12a1 1 0 001-1V4H1z"/></svg>`,
  sparkle:  `<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M7.657 6.247c.11-.33.576-.33.686 0l.645 1.937a2.89 2.89 0 001.829 1.828l1.936.645c.33.11.33.576 0 .686l-1.937.645a2.89 2.89 0 00-1.828 1.829l-.645 1.936a.361.361 0 01-.686 0l-.645-1.937a2.89 2.89 0 00-1.828-1.828l-1.937-.645a.361.361 0 010-.686l1.937-.645a2.89 2.89 0 001.828-1.828l.645-1.937zM3.794 1.148a.217.217 0 01.412 0l.387 1.162c.173.518.579.924 1.097 1.097l1.162.387a.217.217 0 010 .412l-1.162.387A1.734 1.734 0 004.593 5.69l-.387 1.162a.217.217 0 01-.412 0L3.407 5.69A1.734 1.734 0 002.31 4.593l-1.162-.387a.217.217 0 010-.412l1.162-.387A1.734 1.734 0 003.407 2.31l.387-1.162zM10.863.099a.145.145 0 01.274 0l.258.774c.115.346.386.617.732.732l.774.258a.145.145 0 010 .274l-.774.258a1.156 1.156 0 00-.732.732l-.258.774a.145.145 0 01-.274 0l-.258-.774a1.156 1.156 0 00-.732-.732L9.1 2.137a.145.145 0 010-.274l.774-.258c.346-.115.617-.386.732-.732L10.863.1z"/></svg>`,
};

// ── Helpers ────────────────────────────────────────────────────────────────
function fmtDt(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
    + ' ' + d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
}

function fmtRelative(iso) {
  if (!iso) return '';
  const diff = new Date(iso) - new Date();
  const abs  = Math.abs(diff);
  const mins = Math.floor(abs / 60000);
  const hrs  = Math.floor(abs / 3600000);
  const days = Math.floor(abs / 86400000);
  const past = diff < 0;
  if (mins < 1)   return past ? 'just now' : 'any moment';
  if (mins < 60)  return past ? `${mins}m ago` : `in ${mins}m`;
  if (hrs  < 24)  return past ? `${hrs}h ago`  : `in ${hrs}h`;
  return past ? `${days}d ago` : `in ${days}d`;
}

function statusBadge(status) {
  return `<span class="badge badge-${status}"><span class="badge-dot"></span>${status}</span>`;
}

function platformBadge(platform) {
  const icon = ICONS[platform] || '';
  return `<span class="badge badge-${platform}">${icon} ${platform}</span>`;
}

function charLimit(platform) {
  return platform === 'linkedin' ? 3000 : 280;
}

function esc(str) {
  return String(str ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── Toast ──────────────────────────────────────────────────────────────────
function toast(message, type = 'success') {
  const icons = { success: '✓', error: '✕', warning: '⚠' };
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `<span class="toast-icon">${icons[type] || 'ℹ'}</span><span>${esc(message)}</span>`;
  document.getElementById('toast-container').appendChild(el);
  setTimeout(() => { el.classList.add('fade-out'); setTimeout(() => el.remove(), 300); }, 3200);
}

// ── Modal ──────────────────────────────────────────────────────────────────
function openModal(title, bodyHtml, { wide = false } = {}) {
  document.getElementById('modal-title').textContent = title;
  document.getElementById('modal-body').innerHTML = bodyHtml;
  const modal = document.getElementById('modal');
  modal.style.maxWidth = wide ? '680px' : '520px';
  document.getElementById('modal-overlay').classList.remove('hidden');
}

function closeModal() {
  document.getElementById('modal-overlay').classList.add('hidden');
}

// ── Router ─────────────────────────────────────────────────────────────────
function navigate(view) {
  State.view = view;
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.view === view);
  });
  const titles = {
    overview:  'Overview',
    posts:     'Posts',
    generate:  'Generate Content',
    scheduler: 'Scheduler',
    config:    'Config',
  };
  document.getElementById('topbar-title').textContent = titles[view] || view;
  renderView();
}

function renderView() {
  const container = document.getElementById('view-container');
  switch (State.view) {
    case 'overview':  renderOverview(container); break;
    case 'posts':     renderPosts(container);    break;
    case 'generate':  renderGenerate(container); break;
    case 'scheduler': renderScheduler(container); break;
    case 'config':    renderConfig(container);  break;
    default:          container.innerHTML = '<p style="color:var(--text-3)">Unknown view.</p>';
  }
}

// ── Overview ───────────────────────────────────────────────────────────────
async function renderOverview(container) {
  const stats  = State.stats  || await Api.getStats();
  const recent = State.posts.slice(0, 5);

  State.stats = stats;

  const nextDue = stats.next_due
    ? `Next: ${fmtDt(stats.next_due)} (${fmtRelative(stats.next_due)})`
    : 'No pending posts';

  container.innerHTML = `
    <div class="stats-grid">
      <div class="stat-card total">
        <div class="stat-label">Total Posts</div>
        <div class="stat-value">${stats.total}</div>
        <div class="stat-sub">all time</div>
      </div>
      <div class="stat-card pending">
        <div class="stat-label">Pending</div>
        <div class="stat-value">${stats.pending}</div>
        <div class="stat-sub">${nextDue}</div>
      </div>
      <div class="stat-card published">
        <div class="stat-label">Published</div>
        <div class="stat-value">${stats.published}</div>
        <div class="stat-sub">successfully sent</div>
      </div>
      <div class="stat-card failed">
        <div class="stat-label">Failed</div>
        <div class="stat-value">${stats.failed}</div>
        <div class="stat-sub">need attention</div>
      </div>
      <div class="stat-card cancelled">
        <div class="stat-label">Cancelled</div>
        <div class="stat-value">${stats.cancelled}</div>
        <div class="stat-sub">manually stopped</div>
      </div>
    </div>

    <div class="quick-actions">
      <button class="quick-action-card" id="qa-schedule">
        <div class="qa-icon purple">
          ${ICONS.calendar}
        </div>
        <div class="qa-text">
          <strong>Schedule Post</strong>
          <span>Queue content for later</span>
        </div>
      </button>
      <button class="quick-action-card" id="qa-generate">
        <div class="qa-icon green">
          ${ICONS.sparkle}
        </div>
        <div class="qa-text">
          <strong>Generate with AI</strong>
          <span>Claude drafts the copy</span>
        </div>
      </button>
      <button class="quick-action-card" id="qa-run-once">
        <div class="qa-icon amber">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 3.5a4.5 4.5 0 100 9 4.5 4.5 0 000-9zM1 8a7 7 0 1114 0A7 7 0 011 8zm7-3.5a.5.5 0 01.5.5v3.25l2.03 1.218a.5.5 0 01-.5.866L7.5 8.866V5a.5.5 0 01.5-.5z"/>
          </svg>
        </div>
        <div class="qa-text">
          <strong>Run Scheduler</strong>
          <span>Publish due posts now</span>
        </div>
      </button>
    </div>

    <div class="section-header">
      <div class="section-title">Recent Posts</div>
      <button class="btn btn-ghost btn-sm" data-view="posts">View all →</button>
    </div>
    <div class="table-wrap">
      ${buildPostsTable(recent, { compact: true })}
    </div>
  `;

  container.querySelector('#qa-schedule').addEventListener('click', () => openScheduleModal());
  container.querySelector('#qa-generate').addEventListener('click', () => navigate('generate'));
  container.querySelector('#qa-run-once').addEventListener('click', runSchedulerOnce);
  container.querySelector('[data-view="posts"]').addEventListener('click', () => navigate('posts'));
  bindPostTableActions(container);
}

// ── Posts view ─────────────────────────────────────────────────────────────
async function renderPosts(container) {
  const { platform, status } = State.filters;
  const posts = await Api.getPosts({ platform, status });
  State.posts = posts;

  container.innerHTML = `
    <div class="filters">
      <div class="filter-group">
        <span class="filter-label">Platform</span>
        <select id="filter-platform" class="btn btn-ghost" style="padding:5px 10px">
          <option value="all"     ${platform==='all'     ?'selected':''}>All platforms</option>
          <option value="twitter" ${platform==='twitter' ?'selected':''}>Twitter / X</option>
          <option value="linkedin"${platform==='linkedin'?'selected':''}>LinkedIn</option>
        </select>
      </div>
      <div class="filter-group">
        <span class="filter-label">Status</span>
        <select id="filter-status" class="btn btn-ghost" style="padding:5px 10px">
          <option value="all"       ${status==='all'      ?'selected':''}>All statuses</option>
          <option value="pending"   ${status==='pending'  ?'selected':''}>Pending</option>
          <option value="published" ${status==='published'?'selected':''}>Published</option>
          <option value="failed"    ${status==='failed'   ?'selected':''}>Failed</option>
          <option value="cancelled" ${status==='cancelled'?'selected':''}>Cancelled</option>
        </select>
      </div>
      <span style="margin-left:auto;font-size:12px;color:var(--text-3)">${posts.length} post${posts.length!==1?'s':''}</span>
    </div>
    <div class="table-wrap">
      ${buildPostsTable(posts)}
    </div>
  `;

  container.querySelector('#filter-platform').addEventListener('change', e => {
    State.filters.platform = e.target.value;
    renderView();
  });
  container.querySelector('#filter-status').addEventListener('change', e => {
    State.filters.status = e.target.value;
    renderView();
  });
  bindPostTableActions(container);
}

function buildPostsTable(posts, { compact = false } = {}) {
  if (!posts.length) {
    return `<div class="empty-state">
      <svg width="40" height="40" viewBox="0 0 16 16" fill="currentColor">
        <path d="M14.5 3a.5.5 0 01.5.5v9a.5.5 0 01-.5.5h-13a.5.5 0 01-.5-.5v-9a.5.5 0 01.5-.5h13z"/>
      </svg>
      <p>No posts found.</p>
    </div>`;
  }

  const rows = posts.map(p => `
    <tr>
      <td class="td-mono">#${p.id}</td>
      <td>${platformBadge(p.platform)}</td>
      <td>${statusBadge(p.status)}</td>
      <td class="td-dim">${fmtDt(p.scheduled_at)}</td>
      ${!compact ? `<td class="td-dim">${fmtDt(p.published_at)}</td>` : ''}
      <td><div class="content-preview">${esc(p.content)}</div></td>
      <td>
        <div class="td-actions">
          <button class="btn btn-ghost btn-sm btn-icon post-action-view" data-id="${p.id}" title="View details">${ICONS.eye}</button>
          ${p.status === 'pending' ? `<button class="btn btn-ghost btn-sm post-action-cancel" data-id="${p.id}" title="Cancel">Cancel</button>` : ''}
          <button class="btn btn-ghost btn-sm btn-icon post-action-delete" data-id="${p.id}" title="Delete">${ICONS.trash}</button>
        </div>
      </td>
    </tr>
  `).join('');

  return `
    <div class="table-scroll">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Platform</th>
            <th>Status</th>
            <th>Scheduled</th>
            ${!compact ? '<th>Published</th>' : ''}
            <th>Content</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

function bindPostTableActions(container) {
  container.querySelectorAll('.post-action-view').forEach(btn => {
    btn.addEventListener('click', () => openPostDetail(+btn.dataset.id));
  });
  container.querySelectorAll('.post-action-cancel').forEach(btn => {
    btn.addEventListener('click', () => confirmCancelPost(+btn.dataset.id));
  });
  container.querySelectorAll('.post-action-delete').forEach(btn => {
    btn.addEventListener('click', () => confirmDeletePost(+btn.dataset.id));
  });
}

async function openPostDetail(id) {
  const post = await Api.getPost(id);
  if (!post) { toast('Post not found', 'error'); return; }

  openModal(`Post #${post.id}`, `
    <div class="detail-row"><span class="detail-key">Platform</span><span class="detail-val">${platformBadge(post.platform)}</span></div>
    <div class="detail-row"><span class="detail-key">Status</span><span class="detail-val">${statusBadge(post.status)}</span></div>
    <div class="detail-row"><span class="detail-key">Scheduled</span><span class="detail-val">${fmtDt(post.scheduled_at)}</span></div>
    <div class="detail-row"><span class="detail-key">Published</span><span class="detail-val">${fmtDt(post.published_at)}</span></div>
    <div class="detail-row"><span class="detail-key">Platform ID</span><span class="detail-val td-mono">${esc(post.platform_id) || '—'}</span></div>
    <div class="detail-row"><span class="detail-key">Retry count</span><span class="detail-val">${post.retry_count}</span></div>
    ${post.error_message ? `<div class="detail-row"><span class="detail-key">Error</span><span class="detail-val" style="color:var(--danger)">${esc(post.error_message)}</span></div>` : ''}
    <div class="detail-row"><span class="detail-key">Created</span><span class="detail-val">${fmtDt(post.created_at)}</span></div>
    <div style="margin-top:12px"><div class="detail-key" style="margin-bottom:6px">Content</div>
    <div class="detail-content">${esc(post.content)}</div></div>
    <div class="modal-footer" style="margin: 16px -20px -20px; padding: 14px 20px;">
      ${post.status === 'pending' ? `<button class="btn btn-danger btn-sm" id="modal-cancel-post" data-id="${post.id}">Cancel post</button>` : ''}
      <button class="btn btn-ghost btn-sm" id="modal-copy-content">Copy content</button>
      <button class="btn btn-ghost btn-sm" onclick="closeModal()">Close</button>
    </div>
  `, { wide: true });

  document.getElementById('modal-copy-content')?.addEventListener('click', () => {
    navigator.clipboard?.writeText(post.content);
    toast('Content copied to clipboard');
  });
  document.getElementById('modal-cancel-post')?.addEventListener('click', () => {
    closeModal();
    confirmCancelPost(post.id);
  });
}

function confirmCancelPost(id) {
  openModal('Cancel Post', `
    <p class="confirm-text">Cancel post #${id}? It will stay in the database with status <strong>cancelled</strong>.</p>
    <div class="modal-footer" style="margin:16px -20px -20px;padding:14px 20px;">
      <button class="btn btn-ghost btn-sm" onclick="closeModal()">Keep it</button>
      <button class="btn btn-danger btn-sm" id="confirm-cancel-btn">Yes, cancel</button>
    </div>
  `);
  document.getElementById('confirm-cancel-btn').addEventListener('click', async () => {
    try {
      await Api.cancelPost(id);
      toast(`Post #${id} cancelled`);
      closeModal();
      await refreshData();
      renderView();
    } catch (e) { toast(e.message, 'error'); }
  });
}

function confirmDeletePost(id) {
  openModal('Delete Post', `
    <p class="confirm-text">Permanently delete post #${id}? This cannot be undone.</p>
    <div class="modal-footer" style="margin:16px -20px -20px;padding:14px 20px;">
      <button class="btn btn-ghost btn-sm" onclick="closeModal()">Keep it</button>
      <button class="btn btn-danger btn-sm" id="confirm-delete-btn">Delete</button>
    </div>
  `);
  document.getElementById('confirm-delete-btn').addEventListener('click', async () => {
    try {
      await Api.deletePost(id);
      toast(`Post #${id} deleted`);
      closeModal();
      await refreshData();
      renderView();
    } catch (e) { toast(e.message, 'error'); }
  });
}

// ── Schedule Post modal ────────────────────────────────────────────────────
function openScheduleModal(prefill = {}) {
  // Default to 1 hour from now
  const defaultDt = new Date(Date.now() + 3600000);
  const pad = n => String(n).padStart(2, '0');
  const defaultDtStr = `${defaultDt.getFullYear()}-${pad(defaultDt.getMonth()+1)}-${pad(defaultDt.getDate())}T${pad(defaultDt.getHours())}:${pad(defaultDt.getMinutes())}`;

  openModal('Schedule Post', `
    <div class="form-group">
      <label class="form-label" for="sp-platform">Platform</label>
      <select id="sp-platform">
        <option value="twitter"  ${prefill.platform==='twitter' ?'selected':''}>Twitter / X</option>
        <option value="linkedin" ${prefill.platform==='linkedin'?'selected':''}>LinkedIn</option>
      </select>
    </div>
    <div class="form-group">
      <label class="form-label" for="sp-content">Content</label>
      <textarea id="sp-content" rows="5" placeholder="What do you want to say?">${esc(prefill.content || '')}</textarea>
      <div class="char-counter" id="sp-char-counter">0 / 280</div>
    </div>
    <div class="form-group">
      <label class="form-label" for="sp-scheduled-at">Schedule At</label>
      <input type="datetime-local" id="sp-scheduled-at" value="${defaultDtStr}" />
      <span class="form-hint">Times are in your local timezone.</span>
    </div>
    <div class="modal-footer" style="margin:16px -20px -20px;padding:14px 20px;">
      <button class="btn btn-ghost btn-sm" onclick="closeModal()">Cancel</button>
      <button class="btn btn-primary btn-sm" id="sp-submit">Schedule</button>
    </div>
  `);

  const contentEl  = document.getElementById('sp-content');
  const platformEl = document.getElementById('sp-platform');
  const counterEl  = document.getElementById('sp-char-counter');

  function updateCounter() {
    const limit = charLimit(platformEl.value);
    const len   = contentEl.value.length;
    const pct   = len / limit;
    counterEl.textContent = `${len} / ${limit}`;
    counterEl.className = 'char-counter' + (pct > 1 ? ' danger' : pct > .85 ? ' warn' : '');
  }

  if (prefill.content) updateCounter();
  contentEl.addEventListener('input', updateCounter);
  platformEl.addEventListener('change', updateCounter);

  document.getElementById('sp-submit').addEventListener('click', async () => {
    const platform     = platformEl.value;
    const content      = contentEl.value.trim();
    const scheduled_at = document.getElementById('sp-scheduled-at').value;
    const limit        = charLimit(platform);

    if (!content)      { toast('Content is required', 'error'); return; }
    if (!scheduled_at) { toast('Schedule time is required', 'error'); return; }
    if (content.length > limit) { toast(`Content exceeds ${limit}-character limit`, 'error'); return; }

    const btn = document.getElementById('sp-submit');
    btn.disabled = true; btn.textContent = 'Scheduling…';

    try {
      const post = await Api.createPost({ platform, content, scheduled_at: new Date(scheduled_at).toISOString() });
      toast(`Post #${post.id} scheduled for ${fmtDt(post.scheduled_at)}`);
      closeModal();
      await refreshData();
      renderView();
    } catch (e) {
      toast(e.message, 'error');
      btn.disabled = false; btn.textContent = 'Schedule';
    }
  });
}

// ── Publish Now modal ──────────────────────────────────────────────────────
function openPublishNowModal() {
  openModal('Publish Now', `
    <div class="form-group">
      <label class="form-label" for="pn-platform">Platform</label>
      <select id="pn-platform">
        <option value="twitter">Twitter / X</option>
        <option value="linkedin">LinkedIn</option>
      </select>
    </div>
    <div class="form-group">
      <label class="form-label" for="pn-content">Content</label>
      <textarea id="pn-content" rows="5" placeholder="Write your post…"></textarea>
      <div class="char-counter" id="pn-char-counter">0 / 280</div>
    </div>
    <div class="modal-footer" style="margin:16px -20px -20px;padding:14px 20px;">
      <button class="btn btn-ghost btn-sm" onclick="closeModal()">Cancel</button>
      <button class="btn btn-success btn-sm" id="pn-submit">Publish Now</button>
    </div>
  `);

  const contentEl  = document.getElementById('pn-content');
  const platformEl = document.getElementById('pn-platform');
  const counterEl  = document.getElementById('pn-char-counter');

  function updateCounter() {
    const limit = charLimit(platformEl.value);
    const len   = contentEl.value.length;
    counterEl.textContent = `${len} / ${limit}`;
    counterEl.className = 'char-counter' + (len > limit ? ' danger' : len > limit * .85 ? ' warn' : '');
  }
  contentEl.addEventListener('input', updateCounter);
  platformEl.addEventListener('change', updateCounter);

  document.getElementById('pn-submit').addEventListener('click', async () => {
    const platform = platformEl.value;
    const content  = contentEl.value.trim();
    const limit    = charLimit(platform);

    if (!content)          { toast('Content is required', 'error'); return; }
    if (content.length > limit) { toast(`Content exceeds ${limit}-char limit`, 'error'); return; }

    const btn = document.getElementById('pn-submit');
    btn.disabled = true; btn.textContent = 'Publishing…';

    try {
      const result = await Api.publishNow({ platform, content });
      toast(`Published! Platform ID: ${result.platform_id}`);
      closeModal();
      await refreshData();
      renderView();
    } catch (e) {
      toast(e.message, 'error');
      btn.disabled = false; btn.textContent = 'Publish Now';
    }
  });
}

// ── Generate view ──────────────────────────────────────────────────────────
async function renderGenerate(container) {
  container.innerHTML = `
    <div class="generate-layout">
      <!-- Left: form panel -->
      <div class="card" style="position:sticky;top:0">
        <div class="card-title">Generate with Claude AI</div>
        <div class="form-group">
          <label class="form-label" for="gen-platform">Platform</label>
          <select id="gen-platform">
            <option value="twitter">Twitter / X</option>
            <option value="linkedin">LinkedIn</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label" for="gen-topic">Topic</label>
          <input type="text" id="gen-topic" placeholder="e.g. AI productivity tips" />
        </div>
        <div class="form-group">
          <label class="form-label" for="gen-tone">Tone</label>
          <select id="gen-tone">
            <option value="professional">Professional</option>
            <option value="casual">Casual</option>
            <option value="humorous">Humorous</option>
            <option value="inspirational">Inspirational</option>
            <option value="educational">Educational</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label" for="gen-variants">Variants</label>
          <select id="gen-variants">
            <option value="1">1 variant</option>
            <option value="2">2 variants</option>
            <option value="3">3 variants</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label" for="gen-context">Extra context <span style="color:var(--text-3);font-weight:400;text-transform:none">(optional)</span></label>
          <textarea id="gen-context" rows="3" placeholder="Any context Claude should know…"></textarea>
        </div>
        <button class="btn btn-primary" id="gen-submit" style="width:100%">
          ${ICONS.sparkle} Generate
        </button>
      </div>

      <!-- Right: results -->
      <div class="results-area" id="gen-results">
        <div style="color:var(--text-3);font-size:13px;padding:20px 0">
          Fill in the form and click Generate. Results appear here.
        </div>
      </div>
    </div>
  `;

  document.getElementById('gen-submit').addEventListener('click', handleGenerate);
}

async function handleGenerate() {
  const platform = document.getElementById('gen-platform').value;
  const topic    = document.getElementById('gen-topic').value.trim();
  const tone     = document.getElementById('gen-tone').value;
  const variants = +document.getElementById('gen-variants').value;
  const context  = document.getElementById('gen-context').value.trim();

  if (!topic) { toast('Topic is required', 'error'); return; }

  const btn = document.getElementById('gen-submit');
  btn.disabled = true; btn.innerHTML = `<div class="spinner" style="width:14px;height:14px;border-width:2px;margin:0 auto"></div>`;

  const resultsEl = document.getElementById('gen-results');
  resultsEl.innerHTML = `
    <div class="generating-placeholder">
      <div class="spinner"></div>
      Asking Claude to write your posts…
    </div>`;

  try {
    const results = await Api.generateContent({ platform, topic, tone, context, variants });
    renderGenerateResults(resultsEl, results);
    toast(`Generated ${results.length} variant${results.length > 1 ? 's' : ''}`);
  } catch (e) {
    resultsEl.innerHTML = `<div style="color:var(--danger);padding:16px;font-size:13px">${esc(e.message)}</div>`;
    toast(e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = `${ICONS.sparkle} Generate`;
  }
}

function renderGenerateResults(container, results) {
  container.innerHTML = results.map((gc, i) => {
    const limit = charLimit(gc.platform);
    const len   = gc.content.length;
    const pct   = len / limit;
    const cc    = pct > 1 ? 'danger' : pct > .85 ? 'warn' : '';
    return `
      <div class="result-card">
        <div class="result-card-header">
          <div class="result-meta">
            ${platformBadge(gc.platform)}
            <span class="badge" style="background:var(--grey-muted);color:var(--text-2)">${gc.tone}</span>
            ${gc.id ? `<span class="td-mono" style="font-size:11px;color:var(--text-3)">#${gc.id}</span>` : ''}
          </div>
          <div class="result-actions">
            <span class="char-counter ${cc}" style="margin-right:4px">${len} / ${limit}</span>
            <button class="btn btn-ghost btn-sm btn-icon result-copy" data-idx="${i}" title="Copy">${ICONS.copy}</button>
            <button class="btn btn-primary btn-sm result-schedule" data-idx="${i}">
              ${ICONS.calendar} Schedule
            </button>
          </div>
        </div>
        <div class="result-content">${esc(gc.content)}</div>
      </div>
    `;
  }).join('');

  // Bind actions
  container.querySelectorAll('.result-copy').forEach(btn => {
    btn.addEventListener('click', () => {
      const content = results[+btn.dataset.idx].content;
      navigator.clipboard?.writeText(content);
      toast('Copied to clipboard');
    });
  });
  container.querySelectorAll('.result-schedule').forEach(btn => {
    btn.addEventListener('click', () => {
      const gc = results[+btn.dataset.idx];
      openScheduleModal({ platform: gc.platform, content: gc.content });
    });
  });
}

// ── Scheduler view ─────────────────────────────────────────────────────────
async function renderScheduler(container) {
  const stats = await Api.getStats();

  const pendingPosts = await Api.getPosts({ status: 'pending' });
  const duePosts     = pendingPosts.filter(p => new Date(p.scheduled_at) <= new Date());
  const upcomingPosts = pendingPosts.filter(p => new Date(p.scheduled_at) > new Date()).slice(0, 5);

  const logHtml = State.schedulerLog.length
    ? State.schedulerLog.map(l => `
        <div class="log-line">
          <span class="log-ts">${l.ts}</span>
          <span class="log-msg ${l.level}">${esc(l.msg)}</span>
        </div>`).join('')
    : `<div class="log-line"><span class="log-msg" style="color:var(--text-3)">No scheduler runs yet this session.</span></div>`;

  container.innerHTML = `
    <div class="scheduler-grid">
      <div class="card">
        <div class="card-title">Queue Status</div>
        <div style="display:flex;flex-direction:column;gap:12px">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <span style="font-size:13px;color:var(--text-2)">Due now</span>
            <span style="font-size:20px;font-weight:700;color:${duePosts.length > 0 ? 'var(--warning)' : 'var(--text-3)'}">${duePosts.length}</span>
          </div>
          <div style="display:flex;justify-content:space-between;align-items:center">
            <span style="font-size:13px;color:var(--text-2)">Upcoming</span>
            <span style="font-size:20px;font-weight:700;color:var(--text-1)">${upcomingPosts.length}</span>
          </div>
          <div style="display:flex;justify-content:space-between;align-items:center">
            <span style="font-size:13px;color:var(--text-2)">Next post</span>
            <span style="font-size:12px;color:var(--text-3)">${stats.next_due ? fmtDt(stats.next_due) : '—'}</span>
          </div>
          <hr style="border:none;border-top:1px solid var(--border);margin:4px 0"/>
          <button class="btn btn-primary" id="sched-run-once" style="width:100%">
            <svg width="13" height="13" viewBox="0 0 16 16" fill="currentColor"><path d="M8 3.5a4.5 4.5 0 100 9 4.5 4.5 0 000-9zM1 8a7 7 0 1114 0A7 7 0 011 8zm7-3.5a.5.5 0 01.5.5v3.25l2.03 1.218a.5.5 0 01-.5.866L7.5 8.866V5a.5.5 0 01.5-.5z"/></svg>
            Run Once
          </button>
          <button class="btn btn-ghost" id="sched-publish-now" style="width:100%">Publish Now (custom)</button>
        </div>
      </div>

      <div class="card">
        <div class="card-title">Activity Log</div>
        <div class="log-feed" id="sched-log">${logHtml}</div>
      </div>
    </div>

    <div class="section-header">
      <div class="section-title">Upcoming Posts</div>
    </div>
    <div class="table-wrap">
      ${upcomingPosts.length ? buildPostsTable(upcomingPosts, { compact: true }) : `<div class="empty-state"><p>No upcoming posts scheduled.</p></div>`}
    </div>

    ${duePosts.length ? `
    <div class="section-header" style="margin-top:24px">
      <div class="section-title" style="color:var(--warning)">⚠ Overdue Posts (${duePosts.length})</div>
    </div>
    <div class="table-wrap">
      ${buildPostsTable(duePosts, { compact: true })}
    </div>` : ''}
  `;

  document.getElementById('sched-run-once').addEventListener('click', runSchedulerOnce);
  document.getElementById('sched-publish-now').addEventListener('click', openPublishNowModal);
  bindPostTableActions(container);
}

async function runSchedulerOnce() {
  const btn = document.getElementById('btn-run-once');
  if (btn) { btn.disabled = true; btn.textContent = 'Running…'; }

  const ts = new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

  try {
    const result = await Api.runOnce();
    const n      = result.published ?? 0;
    const msg    = n > 0 ? `Published ${n} post${n > 1 ? 's' : ''}` : 'No posts were due';
    const level  = n > 0 ? 'success' : 'info';

    State.schedulerLog.unshift({ ts, level, msg });
    if (result.logs) result.logs.forEach(l => State.schedulerLog.unshift({ ts, level: l.level, msg: l.msg }));
    State.schedulerLog = State.schedulerLog.slice(0, 40);

    toast(msg, n > 0 ? 'success' : undefined);
    await refreshData();
    if (State.view === 'scheduler') renderView();
  } catch (e) {
    State.schedulerLog.unshift({ ts, level: 'error', msg: e.message });
    toast(e.message, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = 'Run Now'; btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M8 3.5a4.5 4.5 0 100 9 4.5 4.5 0 000-9zM1 8a7 7 0 1114 0A7 7 0 011 8zm7-3.5a.5.5 0 01.5.5v3.25l2.03 1.218a.5.5 0 01-.5.866L7.5 8.866V5a.5.5 0 01.5-.5z"/></svg> Run Now`; }
  }
}

// ── Config view ────────────────────────────────────────────────────────────
async function renderConfig(container) {
  const cfg = State.config || await Api.getConfig();
  State.config = cfg;

  const revealBtn = (id) => `
    <div class="input-group">
      <input type="password" id="${id}" value="${esc(cfg[id.split('-')[0]]?.[id.split('-').slice(1).join('_')] ?? '')}" placeholder="••••••••••••••••" />
      <button type="button" class="input-reveal" data-target="${id}" title="Show/hide">
        <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zM1.173 8a13.133 13.133 0 011.66-2.043C4.12 4.668 5.88 3.5 8 3.5c2.12 0 3.879 1.168 5.168 2.457A13.133 13.133 0 0114.828 8c-.058.087-.122.183-.195.288-.335.48-.83 1.12-1.465 1.755C11.879 11.332 10.119 12.5 8 12.5c-2.12 0-3.879-1.168-5.168-2.457A13.134 13.134 0 011.172 8z"/><path d="M8 5.5a2.5 2.5 0 100 5 2.5 2.5 0 000-5zM4.5 8a3.5 3.5 0 117 0 3.5 3.5 0 01-7 0z"/></svg>
      </button>
    </div>`;

  container.innerHTML = `
    <div class="config-sections">

      <!-- Twitter -->
      <div class="config-section">
        <div class="config-section-header">
          <div class="config-section-title">
            <div class="config-icon twitter">${ICONS.twitter}</div>
            Twitter / X
          </div>
          <div style="display:flex;align-items:center;gap:8px">
            <span class="verify-result hidden" id="verify-twitter-result"></span>
            <button class="btn btn-ghost btn-sm" id="verify-twitter">Verify</button>
          </div>
        </div>
        <div class="config-section-body">
          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="twitter-api_key">API Key</label>
              <input type="text" id="twitter-api_key" value="${esc(cfg.twitter?.api_key)}" placeholder="Consumer key" />
            </div>
            <div class="form-group">
              <label class="form-label">API Secret</label>
              ${revealBtn('twitter-api_secret')}
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="twitter-access_token">Access Token</label>
              <input type="text" id="twitter-access_token" value="${esc(cfg.twitter?.access_token)}" placeholder="OAuth access token" />
            </div>
            <div class="form-group">
              <label class="form-label">Access Token Secret</label>
              ${revealBtn('twitter-access_token_secret')}
            </div>
          </div>
          <div class="form-group">
            <label class="form-label" for="twitter-bearer_token">Bearer Token <span style="color:var(--text-3);font-weight:400">(optional)</span></label>
            <input type="text" id="twitter-bearer_token" value="${esc(cfg.twitter?.bearer_token)}" placeholder="App-only bearer token" />
          </div>
        </div>
      </div>

      <!-- LinkedIn -->
      <div class="config-section">
        <div class="config-section-header">
          <div class="config-section-title">
            <div class="config-icon linkedin">${ICONS.linkedin}</div>
            LinkedIn
          </div>
          <div style="display:flex;align-items:center;gap:8px">
            <span class="verify-result hidden" id="verify-linkedin-result"></span>
            <button class="btn btn-ghost btn-sm" id="verify-linkedin">Verify</button>
          </div>
        </div>
        <div class="config-section-body">
          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="linkedin-client_id">Client ID</label>
              <input type="text" id="linkedin-client_id" value="${esc(cfg.linkedin?.client_id)}" />
            </div>
            <div class="form-group">
              <label class="form-label">Client Secret</label>
              ${revealBtn('linkedin-client_secret')}
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Access Token</label>
            ${revealBtn('linkedin-access_token')}
          </div>
          <div class="form-group">
            <label class="form-label" for="linkedin-person_urn">Person URN</label>
            <input type="text" id="linkedin-person_urn" value="${esc(cfg.linkedin?.person_urn)}" placeholder="urn:li:person:XXXXXXXX" />
          </div>
        </div>
      </div>

      <!-- Claude -->
      <div class="config-section">
        <div class="config-section-header">
          <div class="config-section-title">
            <div class="config-icon claude">${ICONS.sparkle}</div>
            Claude / Anthropic
          </div>
        </div>
        <div class="config-section-body">
          <div class="form-row">
            <div class="form-group" style="grid-column:1/-1">
              <label class="form-label">API Key</label>
              ${revealBtn('claude-api_key')}
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="claude-model">Model</label>
              <select id="claude-model">
                <option value="claude-sonnet-4-6" ${cfg.claude?.model==='claude-sonnet-4-6'?'selected':''}>claude-sonnet-4-6</option>
                <option value="claude-opus-4-7"   ${cfg.claude?.model==='claude-opus-4-7'  ?'selected':''}>claude-opus-4-7</option>
                <option value="claude-haiku-4-5-20251001" ${cfg.claude?.model==='claude-haiku-4-5-20251001'?'selected':''}>claude-haiku-4-5</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label" for="claude-max_tokens">Max tokens</label>
              <input type="number" id="claude-max_tokens" value="${cfg.claude?.max_tokens ?? 1024}" min="256" max="4096" />
            </div>
          </div>
        </div>
      </div>

      <!-- App settings -->
      <div class="config-section">
        <div class="config-section-header">
          <div class="config-section-title">
            <div class="config-icon settings">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M1 2.5A1.5 1.5 0 012.5 1h3A1.5 1.5 0 017 2.5v3A1.5 1.5 0 015.5 7h-3A1.5 1.5 0 011 5.5v-3zM9 2.5A1.5 1.5 0 0110.5 1h3A1.5 1.5 0 0115 2.5v3A1.5 1.5 0 0113.5 7h-3A1.5 1.5 0 019 5.5v-3zM1 10.5A1.5 1.5 0 012.5 9h3A1.5 1.5 0 017 10.5v3A1.5 1.5 0 015.5 15h-3A1.5 1.5 0 011 13.5v-3zM9 10.5A1.5 1.5 0 0110.5 9h3A1.5 1.5 0 0115 10.5v3A1.5 1.5 0 0113.5 15h-3A1.5 1.5 0 019 13.5v-3z"/></svg>
            </div>
            App Settings
          </div>
        </div>
        <div class="config-section-body">
          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="app-db_path">Database path</label>
              <input type="text" id="app-db_path" value="${esc(cfg.db_path ?? '~/.social_media_automation/posts.db')}" />
            </div>
            <div class="form-group">
              <label class="form-label" for="app-scheduler_interval">Scheduler interval (s)</label>
              <input type="number" id="app-scheduler_interval" value="${cfg.scheduler_interval ?? 60}" min="10" />
            </div>
          </div>
        </div>
      </div>

      <div style="display:flex;gap:10px;padding-bottom:8px">
        <button class="btn btn-primary" id="save-config">Save Configuration</button>
        <p style="font-size:12px;color:var(--text-3);align-self:center">
          ${Api.isOnline() ? 'Changes will be written to disk.' : 'Server offline — use env vars for persistence.'}
        </p>
      </div>

    </div>
  `;

  // Reveal toggles
  container.querySelectorAll('.input-reveal').forEach(btn => {
    btn.addEventListener('click', () => {
      const input = document.getElementById(btn.dataset.target);
      if (input) input.type = input.type === 'password' ? 'text' : 'password';
    });
  });

  // Populate secret fields from cfg
  const secretMap = {
    'twitter-api_secret':          cfg.twitter?.api_secret,
    'twitter-access_token_secret': cfg.twitter?.access_token_secret,
    'linkedin-client_secret':      cfg.linkedin?.client_secret,
    'linkedin-access_token':       cfg.linkedin?.access_token,
    'claude-api_key':              cfg.claude?.api_key,
  };
  Object.entries(secretMap).forEach(([id, val]) => {
    const el = document.getElementById(id);
    if (el && val) el.value = val;
  });

  // Verify buttons
  ['twitter', 'linkedin'].forEach(platform => {
    document.getElementById(`verify-${platform}`).addEventListener('click', async () => {
      const btn = document.getElementById(`verify-${platform}`);
      const res = document.getElementById(`verify-${platform}-result`);
      btn.disabled = true; btn.textContent = 'Checking…';
      try {
        const result = await Api.verifyPlatform(platform);
        res.textContent = result.ok ? '✓ Valid' : `✕ ${result.message || 'Failed'}`;
        res.className = `verify-result ${result.ok ? 'ok' : 'err'}`;
      } catch (e) {
        res.textContent = `✕ ${e.message}`;
        res.className = 'verify-result err';
      } finally {
        btn.disabled = false; btn.textContent = 'Verify';
      }
    });
  });

  // Save
  document.getElementById('save-config').addEventListener('click', async () => {
    const payload = {
      twitter: {
        api_key:              document.getElementById('twitter-api_key').value,
        api_secret:           document.getElementById('twitter-api_secret').value,
        access_token:         document.getElementById('twitter-access_token').value,
        access_token_secret:  document.getElementById('twitter-access_token_secret').value,
        bearer_token:         document.getElementById('twitter-bearer_token').value,
      },
      linkedin: {
        client_id:     document.getElementById('linkedin-client_id').value,
        client_secret: document.getElementById('linkedin-client_secret').value,
        access_token:  document.getElementById('linkedin-access_token').value,
        person_urn:    document.getElementById('linkedin-person_urn').value,
      },
      claude: {
        api_key:    document.getElementById('claude-api_key').value,
        model:      document.getElementById('claude-model').value,
        max_tokens: +document.getElementById('claude-max_tokens').value,
      },
      db_path:            document.getElementById('app-db_path').value,
      scheduler_interval: +document.getElementById('app-scheduler_interval').value,
    };

    const btn = document.getElementById('save-config');
    btn.disabled = true; btn.textContent = 'Saving…';
    try {
      const result = await Api.saveConfig(payload);
      State.config = null; // force reload next time
      toast(result.note || 'Configuration saved');
    } catch (e) { toast(e.message, 'error'); }
    finally { btn.disabled = false; btn.textContent = 'Save Configuration'; }
  });
}

// ── Data refresh ───────────────────────────────────────────────────────────
async function refreshData() {
  try {
    const [posts, stats] = await Promise.all([Api.getPosts(), Api.getStats()]);
    State.posts = posts;
    State.stats = stats;
  } catch { /* silent */ }
}

// ── Bootstrap ──────────────────────────────────────────────────────────────
async function init() {
  // Wire nav
  document.querySelectorAll('.nav-item').forEach(el => {
    el.addEventListener('click', e => { e.preventDefault(); navigate(el.dataset.view); });
  });

  // Wire topbar buttons
  document.getElementById('btn-new-post').addEventListener('click', openScheduleModal);
  document.getElementById('btn-run-once').addEventListener('click', runSchedulerOnce);

  // Wire modal close
  document.getElementById('modal-close').addEventListener('click', closeModal);
  document.getElementById('modal-overlay').addEventListener('click', e => {
    if (e.target === e.currentTarget) closeModal();
  });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

  // Detect API
  await Api.detect();

  // Load initial data
  await refreshData();

  // Render default view
  navigate('overview');

  // Refresh stats every 60s
  setInterval(async () => {
    await refreshData();
    if (State.view === 'overview') renderView();
  }, 60000);
}

document.addEventListener('DOMContentLoaded', init);
