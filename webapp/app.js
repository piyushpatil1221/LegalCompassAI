/**
 * LegalCompass AI — Frontend Application
 * =========================================================
 * Manages all UI interactions, API communication, and
 * dynamic rendering for the four main pages:
 *   1. Chat — RAG-powered legal Q&A
 *   2. Search — Semantic search with filters
 *   3. Analytics — Corpus stats + evaluation results + charts
 *   4. Explorer — Browse indexed corpus chunks
 */

'use strict';

// ─────────────────────────────────────────────────────────────────
// CONFIG
// ─────────────────────────────────────────────────────────────────
const API_BASE      = window.location.origin;   // same host as FastAPI
const TOP_K_DEFAULT = 5;
let   activeFilter  = '';
let   chartInstances = {};

// ─────────────────────────────────────────────────────────────────
// INIT
// ─────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  checkHealth();
  buildSidebarActs();
  loadAnalytics();
  loadExplorer();
});

// ─────────────────────────────────────────────────────────────────
// NAVIGATION / TABS
// ─────────────────────────────────────────────────────────────────
function switchTab(tab) {
  // Deactivate all
  document.querySelectorAll('.tab-btn').forEach(b => {
    b.classList.remove('active');
    b.setAttribute('aria-selected', 'false');
  });
  document.querySelectorAll('.page-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  // Activate selected
  const tabBtn  = document.getElementById(`tab-${tab}`);
  const pageEl  = document.getElementById(`page-${tab}`);
  const navItem = document.getElementById(`nav-${tab}`);

  if (tabBtn)  { tabBtn.classList.add('active'); tabBtn.setAttribute('aria-selected', 'true'); }
  if (pageEl)  pageEl.classList.add('active');
  if (navItem) navItem.classList.add('active');

  // Lazy-load per tab
  if (tab === 'analytics') loadAnalytics();
  if (tab === 'explorer')  loadExplorer();
}

// ─────────────────────────────────────────────────────────────────
// API HEALTH CHECK
// ─────────────────────────────────────────────────────────────────
async function checkHealth() {
  const pill  = document.getElementById('status-pill');
  const label = document.getElementById('status-text');

  try {
    const res  = await fetchJSON('/api/health');
    if (res.pipeline_ready) {
      setStatus('ok', '🟢 Pipeline Ready');
    } else {
      setStatus('loading', '⚠ RAG Not Indexed');
    }
  } catch {
    setStatus('error', '🔴 API Offline');
  }
}

function setStatus(type, text) {
  const pill = document.getElementById('status-pill');
  pill.className = `status-pill ${type}`;
  document.getElementById('status-text').textContent = text;
}

// ─────────────────────────────────────────────────────────────────
// FETCH HELPER
// ─────────────────────────────────────────────────────────────────
async function fetchJSON(url, options = {}) {
  const resp = await fetch(API_BASE + url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${resp.status}`);
  }
  return resp.json();
}

// ─────────────────────────────────────────────────────────────────
// SIDEBAR: BARE ACTS TREE
// ─────────────────────────────────────────────────────────────────
const ACT_COLORS = {
  BNS:  '#d4a843',
  BNSS: '#4a8fe8',
  BSA:  '#2ec4b6',
};

const SIDEBAR_SECTIONS = {
  BNS: [
    { num: '1',   title: 'Short Title, Extent & Commencement' },
    { num: '2',   title: 'Definitions' },
    { num: '100', title: 'Right of Private Defence' },
    { num: '101', title: 'Defence of Body — When Fatal Force Justified' },
    { num: '103', title: 'Punishment for Murder' },
    { num: '104', title: 'Culpable Homicide' },
    { num: '105', title: 'Causing Death by Negligence' },
    { num: '109', title: 'Abetment' },
    { num: '111', title: 'Organised Crime' },
    { num: '112', title: 'Petty Organised Crime' },
  ],
  BNSS: [
    { num: '2',   title: 'Definitions' },
    { num: '35',  title: 'Arrest Without Warrant' },
    { num: '41',  title: 'Search of Person Arrested' },
    { num: '167', title: 'Procedure When Investigation Cannot Finish in 24 Hrs' },
    { num: '436', title: 'Bail in Bailable Offences' },
    { num: '480', title: 'Special Provisions for Bail' },
  ],
  BSA: [
    { num: '2',  title: 'Definitions' },
    { num: '23', title: 'Admissions' },
    { num: '57', title: 'Facts of Which Court Must Take Judicial Notice' },
    { num: '61', title: 'Proof of Contents of Documents' },
  ],
};

function buildSidebarActs() {
  const container = document.getElementById('sidebar-acts');
  if (!container) return;

  for (const [act, sections] of Object.entries(SIDEBAR_SECTIONS)) {
    // Act header
    const hdr = document.createElement('div');
    hdr.style.cssText = `
      font-size:11px; font-weight:700; color:${ACT_COLORS[act]};
      letter-spacing:0.8px; text-transform:uppercase;
      padding:8px 10px 4px; margin-top:6px;
    `;
    hdr.textContent = act;
    container.appendChild(hdr);

    // Sections
    for (const sec of sections) {
      const item = document.createElement('button');
      item.className = 'act-tree-item';
      item.innerHTML = `
        <span class="act-dot" style="background:${ACT_COLORS[act]}"></span>
        <span class="act-section-num">S.${sec.num}</span>
        <span style="flex:1;text-align:left;font-size:11px;line-height:1.3;">${sec.title}</span>
      `;
      item.addEventListener('click', () => lookupSection(act, sec.num));
      container.appendChild(item);
    }
  }
}

async function lookupSection(act, sectionNum) {
  switchTab('chat');
  const q = `${act} Section ${sectionNum}`;
  document.getElementById('chat-input').value = q;
  await sendMessage();
}

// ─────────────────────────────────────────────────────────────────
// CHAT
// ─────────────────────────────────────────────────────────────────
function handleChatKey(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
}

function autoResizeTextarea(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

function sendSuggestion(chipEl) {
  document.getElementById('chat-input').value = chipEl.textContent;
  sendMessage();
}

let isLoading = false;

async function sendMessage() {
  if (isLoading) return;
  const input  = document.getElementById('chat-input');
  const question = input.value.trim();
  if (!question) return;

  const searchMode  = document.getElementById('search-mode-select').value;
  const categoryFilter = document.getElementById('category-filter-select').value || null;

  // Hide welcome screen
  const welcome = document.getElementById('chat-welcome');
  if (welcome) welcome.style.display = 'none';

  // Append user message
  appendMessage('user', question);
  input.value = '';
  input.style.height = 'auto';

  // Show typing indicator
  const typingId = appendTyping();
  isLoading = true;
  document.getElementById('send-btn').disabled = true;

  try {
    const result = await fetchJSON('/api/agent-query', {
      method: 'POST',
      body: JSON.stringify({
        question,
        top_k: TOP_K_DEFAULT,
        search_mode: searchMode,
        category_filter: categoryFilter,
      }),
    });

    removeTyping(typingId);
    appendAIMessage(result);
  } catch (err) {
    removeTyping(typingId);
    appendMessage('ai', `⚠ Error: ${err.message}\n\nMake sure the API server is running:\n  python scripts/api_server.py`);
    showToast('error', `API Error: ${err.message}`);
  } finally {
    isLoading = false;
    document.getElementById('send-btn').disabled = false;
  }
}

function appendMessage(role, text) {
  const container = document.getElementById('chat-messages');
  const row = document.createElement('div');
  row.className = `message-row ${role}`;

  const isAI = role === 'ai';
  const avatarEmoji = isAI ? '⚖' : '👤';
  const avatarClass = isAI ? 'ai-avatar' : 'user-avatar';
  const bubbleClass = isAI ? 'ai-bubble' : 'user-bubble';

  row.innerHTML = `
    <div class="msg-avatar ${avatarClass}">${avatarEmoji}</div>
    <div class="msg-body">
      <div class="msg-bubble ${bubbleClass}">${escapeHtml(text)}</div>
    </div>
  `;

  container.appendChild(row);
  scrollToBottom(container);
  return row;
}

function appendAIMessage(result) {
  const container = document.getElementById('chat-messages');
  const row = document.createElement('div');
  row.className = 'message-row ai';

  const chunks = result.retrieved_chunks || [];
  const elapsed = result.elapsed_ms || 0;
  const mode = result.search_mode || 'hybrid';
  const count = result.retrieved_count || 0;
  
  // Build Agent Badges
  let agentHTML = '';
  if (result.agent_data) {
    const crimes = result.agent_data.crime_types || [];
    let crimeBadges = crimes.map(c => `<span class="meta-badge" style="background:#dc3545;color:white;">${c.crime}</span>`).join('');
    
    let roleBadge = '';
    if (result.agent_data.role) {
      roleBadge = `<span class="meta-badge" style="background:#0d6efd;color:white;">Role: ${result.agent_data.role.toUpperCase()}</span>`;
    }
    
    let bailHTML = '';
    if (result.agent_data.bail_prediction) {
      const bailColor = result.agent_data.bail_prediction.toLowerCase() === 'granted' ? '#198754' : '#dc3545';
      bailHTML = `
        <div style="margin-top:10px; padding:10px; border:2px solid ${bailColor}; border-radius:8px; font-weight:bold; color:${bailColor};">
          ⚖️ Bail Prediction: ${result.agent_data.bail_prediction.toUpperCase()}
        </div>
      `;
    }
    
    let clarifyHTML = '';
    if (result.agent_data.clarification) {
      clarifyHTML = `
        <div style="margin-top:10px; padding:10px; background-color:#fff3cd; color:#856404; border-radius:8px; font-weight:bold;">
          🤔 Clarification Needed: ${result.agent_data.clarification}
        </div>
      `;
    }
    
    agentHTML = `
      <div class="agent-metadata" style="margin-bottom:10px;">
        ${crimeBadges}
        ${roleBadge}
      </div>
      ${clarifyHTML}
      ${bailHTML}
    `;
  }

  // Build chunk cards HTML
  let chunksHTML = '';
  if (chunks.length > 0) {
    const chunkItems = chunks.map((c, i) => {
      const score = c.score || 0;
      const scoreClass = score > 0.75 ? 'high' : score > 0.5 ? 'medium' : 'low';
      const catClass = `cat-${c.category || 'bare_acts'}`;
      const catLabel = (c.category || '').replace('_', ' ');
      const preview = (c.text || '').substring(0, 180) + '…';

      return `
        <div class="chunk-item" onclick="openChunkDetail(${i}, ${JSON.stringify(JSON.stringify(c))})" role="button" tabindex="0">
          <div class="chunk-item-header">
            <span class="chunk-score ${scoreClass}">${(score * 100).toFixed(0)}%</span>
            <span class="chunk-cat-badge ${catClass}">${catLabel}</span>
            <span class="chunk-title">${escapeHtml(c.title || '')}</span>
          </div>
          <div class="chunk-preview">${escapeHtml(preview)}</div>
        </div>
      `;
    }).join('');

    chunksHTML = `
      <div class="chunks-panel">
        <div class="chunks-panel-header">
          📚 Retrieved Sources (${count})
        </div>
        ${chunkItems}
      </div>
    `;
  }

  row.innerHTML = `
    <div class="msg-avatar ai-avatar">⚖</div>
    <div class="msg-body">
      ${agentHTML}
      <div class="msg-bubble ai-bubble markdown-body" style="background:transparent; padding:0;">${marked.parse(result.answer || '')}</div>
      <div class="msg-meta">
        <span class="meta-badge">Mode: ${mode}</span>
        <span class="meta-badge">${count} sources</span>
        <span class="meta-badge">${elapsed}ms</span>
      </div>
      ${chunksHTML}
    </div>
  `;

  container.appendChild(row);
  scrollToBottom(container);
}

let _typingCounter = 0;
function appendTyping() {
  const id = `typing-${++_typingCounter}`;
  const container = document.getElementById('chat-messages');
  const row = document.createElement('div');
  row.className = 'message-row ai';
  row.id = id;
  row.innerHTML = `
    <div class="msg-avatar ai-avatar">⚖</div>
    <div class="msg-body">
      <div class="msg-bubble ai-bubble">
        <div class="typing-indicator">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
      </div>
    </div>
  `;
  container.appendChild(row);
  scrollToBottom(container);
  return id;
}

function removeTyping(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function scrollToBottom(el) {
  el.scrollTop = el.scrollHeight;
}

// ─────────────────────────────────────────────────────────────────
// SEARCH PAGE
// ─────────────────────────────────────────────────────────────────
function setFilter(btn, cat) {
  activeFilter = cat;
  document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
  btn.classList.add('active');
}

async function performSearch() {
  const query = document.getElementById('search-query').value.trim();
  if (!query) return;

  const container = document.getElementById('search-results');
  container.innerHTML = renderSkeletons(5);

  try {
    const params = new URLSearchParams({ q: query, top_k: 10 });
    if (activeFilter) params.set('category', activeFilter);

    const result = await fetchJSON(`/api/search?${params}`);
    const results = result.results || [];

    if (results.length === 0) {
      container.innerHTML = `<div style="color:var(--text-muted);text-align:center;padding:40px;">No results found.</div>`;
      return;
    }

    container.innerHTML = results.map((r, i) => {
      const score = r.score || 0;
      const cat   = r.category || '';
      const catBadge = `<span class="chunk-cat-badge cat-${cat}" style="font-size:10px;padding:2px 8px;">${cat.replace('_',' ')}</span>`;
      return `
        <div class="result-card" onclick="openDetailFromResult(${JSON.stringify(JSON.stringify(r))})" role="button" tabindex="0">
          <div class="result-card-header">
            <span class="result-title">${escapeHtml(r.title || r.chunk_id || `Result ${i+1}`)}</span>
            <span class="result-score">${(score*100).toFixed(0)}%</span>
          </div>
          <div class="result-text">${escapeHtml(r.text || '')}</div>
          <div class="result-footer">
            ${catBadge}
            <span>${r.chunk_id || ''}</span>
          </div>
        </div>
      `;
    }).join('');

  } catch (err) {
    container.innerHTML = `<div style="color:var(--accent-red);padding:20px;">Error: ${escapeHtml(err.message)}</div>`;
    showToast('error', err.message);
  }
}

function openDetailFromResult(jsonStr) {
  const r = JSON.parse(jsonStr);
  openModal(r.title || r.chunk_id || 'Detail', r.text_full || r.text || '');
}

// ─────────────────────────────────────────────────────────────────
// ANALYTICS
// ─────────────────────────────────────────────────────────────────
async function loadAnalytics() {
  await Promise.all([loadStats(), loadEvalResults()]);
  renderCharts();
}

async function loadStats() {
  try {
    const stats = await fetchJSON('/api/stats');

    // Update chunk counts from live data
    const chunks = stats?.chunks?.categories;
    if (chunks) {
      setTextIfExists('stat-bare-acts',  formatNum(chunks.bare_acts?.chunk_count));
      setTextIfExists('stat-case-docs',  formatNum(chunks.case_docs?.chunk_count));
      setTextIfExists('stat-crime-stats',formatNum(chunks.crime_stats?.chunk_count));
    }

    const emb = stats?.embeddings?.collections;
    if (emb?.legalcompass_iltur) {
      setTextIfExists('stat-iltur', formatNum(emb.legalcompass_iltur.chunks_indexed));
    }
  } catch { /* Use defaults already in HTML */ }
}

async function loadEvalResults() {
  try {
    const report = await fetchJSON('/api/evaluation');
    if (report.error) return;

    const results = report.results || {};

    renderEvalCard('eval-lsi-content', results.lsi);
    renderEvalCard('eval-cjpe-content', results.cjpe);
    renderEvalCard('eval-bail-content', results.bail);
  } catch { /* Not yet evaluated */ }
}

function renderEvalCard(containerId, data) {
  const el = document.getElementById(containerId);
  if (!el || !data || data.error) return;

  const metrics = Object.entries(data)
    .filter(([k]) => !['task','n_samples','label_distribution'].includes(k))
    .map(([k, v]) => {
      if (typeof v !== 'number') return '';
      const cls = v >= 0.7 ? 'good' : v >= 0.5 ? 'mid' : 'low';
      return `
        <div class="eval-metric-row">
          <span class="eval-metric-name">${k.replace(/_/g,' ')}</span>
          <span class="eval-metric-val ${cls}">${v.toFixed(4)}</span>
        </div>
      `;
    }).join('');

  el.innerHTML = `
    <div style="font-size:11px;color:var(--text-muted);margin-bottom:8px;">n=${data.n_samples || 0}</div>
    ${metrics}
  `;
}

function renderCharts() {
  // Corpus Distribution — Doughnut
  const ctxCorpus = document.getElementById('chart-corpus');
  if (ctxCorpus && !chartInstances['corpus']) {
    chartInstances['corpus'] = new Chart(ctxCorpus, {
      type: 'doughnut',
      data: {
        labels: ['Bare Acts', 'Case Docs', 'Crime Stats', 'IL-TUR (sampled)'],
        datasets: [{
          data: [1057, 19834, 14799, 50000],
          backgroundColor: ['#d4a843','#4a8fe8','#e84a6a','#2ec4b6'],
          borderColor:     ['#0a0d14','#0a0d14','#0a0d14','#0a0d14'],
          borderWidth: 3,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right',
            labels: { color: '#8890aa', font: { size: 11, family: 'Inter' }, padding: 10 },
          },
        },
      },
    });
  }

  // IL-TUR Task Distribution — Bar
  const ctxIltur = document.getElementById('chart-iltur');
  if (ctxIltur && !chartInstances['iltur']) {
    let ilturLabels = ['bail', 'cjpe', 'lmt', 'lner', 'lsi', 'pcr', 'rr', 'summ'];
    let ilturData = [297800, 124100, 3200, 900, 70400, 50000, 1100, 88300];
    
    if (stats?.chunks?.categories?.iltur?.tasks) {
      const t = stats.chunks.categories.iltur.tasks;
      ilturData = ilturLabels.map(l => t[l] || 0);
    }

    chartInstances['iltur'] = new Chart(ctxIltur, {
      type: 'bar',
      data: {
        labels: ilturLabels,
        datasets: [{
          label: 'Chunks',
          data: ilturData,
          backgroundColor: 'rgba(74,143,232,0.6)',
          borderColor: '#4a8fe8',
          borderWidth: 1,
          borderRadius: 4,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { ticks: { color: '#8890aa', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,0.04)' } },
          y: { ticks: { color: '#8890aa', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,0.04)' } },
        },
        plugins: {
          legend: { display: false },
        },
      },
    });
  }
}

// ─────────────────────────────────────────────────────────────────
// CORPUS EXPLORER
// ─────────────────────────────────────────────────────────────────
const EXPLORER_COLLECTIONS = {
  bare_acts:   { catLabel: '📜 Bare Acts', searchQ: 'section punishment offence' },
  case_docs:   { catLabel: '📋 Case Law',  searchQ: 'murder culpable homicide conviction' },
  crime_stats: { catLabel: '📊 Crime Stats', searchQ: 'district crime 2013 2014' },
  iltur:       { catLabel: '🔬 IL-TUR',    searchQ: 'bail judgment accused' },
};

async function loadExplorer() {
  const cat = document.getElementById('explorer-category')?.value || 'bare_acts';
  const container = document.getElementById('explorer-content');
  if (!container) return;

  container.innerHTML = renderSkeletons(6);

  const info = EXPLORER_COLLECTIONS[cat] || EXPLORER_COLLECTIONS.bare_acts;

  try {
    const params = new URLSearchParams({ q: info.searchQ, top_k: 20, category: cat, mode: 'semantic' });
    const result = await fetchJSON(`/api/search?${params}`);
    const items = result.results || [];

    if (!items.length) {
      container.innerHTML = `<div style="color:var(--text-muted);padding:40px;grid-column:1/-1;text-align:center;">
        No indexed data in this category yet.<br>
        <small>Run embed_and_index.py to index the corpus.</small>
      </div>`;
      return;
    }

    container.innerHTML = items.map((item) => `
      <div class="explorer-card" onclick="openDetailFromResult(${JSON.stringify(JSON.stringify(item))})" role="button" tabindex="0">
        <div class="explorer-card-title">${escapeHtml(item.title || item.chunk_id || 'Unknown')}</div>
        <div class="explorer-card-meta">${item.chunk_id || ''} · score: ${(item.score||0).toFixed(3)}</div>
        <div class="explorer-card-text">${escapeHtml(item.text || '')}</div>
      </div>
    `).join('');

  } catch (err) {
    // API not available — show placeholder cards
    container.innerHTML = renderPlaceholderCards(cat);
  }
}

function renderPlaceholderCards(cat) {
  const examples = {
    bare_acts: [
      { title: 'BNS Section 103 — Punishment for Murder', text: '(1) Whoever commits murder shall be punished with death or imprisonment for life, and shall also be liable to fine. (2) When a group of five or more persons commits murder on grounds of race, caste, sex or language, each member shall be punished with death or imprisonment for life.' },
      { title: 'BNS Section 104 — Culpable Homicide', text: 'Whoever commits culpable homicide not amounting to murder shall be punished with imprisonment for life, or imprisonment of either description for a term which may extend to ten years, and shall also be liable to fine.' },
      { title: 'BNSS Section 167 — Remand & Custody', text: 'Whenever any person is arrested and detained in custody, and it appears that the investigation cannot be completed within twenty-four hours, the officer in charge shall immediately transmit to the nearest Judicial Magistrate a copy of the entries in the diary.' },
    ],
    case_docs: [
      { title: 'Case: Vinay Sharma vs State of Madhya Pradesh', text: 'The conviction under Section 302 IPC is confirmed. The High Court rightly upheld the trial court\'s judgment. The accused was found guilty of murder with premeditation and the death penalty was confirmed.' },
    ],
    crime_stats: [
      { title: 'NCRB: District-wise IPC Crimes 2013 — Maharashtra', text: 'Dataset: District_wise_crimes_IPC_2013 | State: Maharashtra | District: Mumbai | Total IPC Crimes: 42,150 | Murder: 215 | Rape: 389 | Robbery: 1,842 | Burglary: 8,421' },
    ],
    iltur: [
      { title: 'IL-TUR [BAIL] — Bail Application Case', text: 'The applicant seeks bail under Section 436-A CrPC. The accused has been in custody for more than half the maximum period of imprisonment for the offence. Court considers nature of offence, criminal antecedents, and likelihood of flight risk.' },
    ],
  };

  const cards = (examples[cat] || examples.bare_acts).map(e => `
    <div class="explorer-card">
      <div class="explorer-card-title">${escapeHtml(e.title)}</div>
      <div class="explorer-card-meta">Sample preview · Run embed_and_index.py to load live data</div>
      <div class="explorer-card-text">${escapeHtml(e.text)}</div>
    </div>
  `).join('');

  return cards + `
    <div class="explorer-card" style="grid-column:1/-1;border-color:rgba(212,168,67,0.2);">
      <div style="color:var(--accent-gold);font-size:13px;font-weight:600;margin-bottom:8px;">ℹ Showing sample data</div>
      <div style="color:var(--text-secondary);font-size:12px;">The API server is not running or the corpus is not yet indexed. Run embed_and_index.py and then api_server.py to load live data.</div>
    </div>
  `;
}

// ─────────────────────────────────────────────────────────────────
// MODAL
// ─────────────────────────────────────────────────────────────────
function openChunkDetail(index, jsonStr) {
  const chunk = JSON.parse(jsonStr);
  openModal(chunk.title || `Chunk ${index + 1}`, formatChunkDetail(chunk));
}

function formatChunkDetail(chunk) {
  const meta = chunk.metadata || {};
  const lines = [
    `Chunk ID : ${chunk.chunk_id || chunk.id || 'N/A'}`,
    `Category : ${chunk.category || 'N/A'}`,
    `Score    : ${chunk.score != null ? (chunk.score * 100).toFixed(2) + '%' : 'N/A'}`,
    '',
    '── METADATA ──────────────────────────────────────────',
    ...Object.entries(meta).map(([k, v]) => `${k.padEnd(20)}: ${v}`),
    '',
    '── TEXT ──────────────────────────────────────────────',
    chunk.text_full || chunk.text || '(no text)',
  ];
  return lines.join('\n');
}

function openModal(title, content) {
  document.getElementById('modal-title-text').textContent = title;
  document.getElementById('modal-content').textContent = content;
  document.getElementById('detail-modal').classList.add('open');
}

function closeModal(event) {
  if (!event || event.target === document.getElementById('detail-modal')) {
    document.getElementById('detail-modal').classList.remove('open');
  }
}

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeModal();
});

// ─────────────────────────────────────────────────────────────────
// TOAST
// ─────────────────────────────────────────────────────────────────
function showToast(type, message) {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `${type === 'error' ? '❌' : '✅'} ${escapeHtml(message)}`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ─────────────────────────────────────────────────────────────────
// UTILITIES
// ─────────────────────────────────────────────────────────────────
function escapeHtml(str) {
  if (typeof str !== 'string') return String(str ?? '');
  return str
    .replace(/&/g,  '&amp;')
    .replace(/</g,  '&lt;')
    .replace(/>/g,  '&gt;')
    .replace(/"/g,  '&quot;')
    .replace(/'/g,  '&#039;');
}

function formatNum(n) {
  if (n == null) return '—';
  return Number(n).toLocaleString();
}

function setTextIfExists(id, val) {
  const el = document.getElementById(id);
  if (el && val) el.textContent = val;
}

function renderSkeletons(n) {
  return Array.from({ length: n }, () => `
    <div class="explorer-card" style="gap:10px;display:flex;flex-direction:column;">
      <div class="skeleton" style="width:60%;height:14px;"></div>
      <div class="skeleton" style="width:30%;height:10px;"></div>
      <div class="skeleton" style="width:100%;height:10px;"></div>
      <div class="skeleton" style="width:90%;height:10px;"></div>
    </div>
  `).join('');
}
