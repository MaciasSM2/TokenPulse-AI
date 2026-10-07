// TokenPulse AI - Project-Centric & Global Logic

let currentViewMode = 'global'; // 'global' | 'project'
let currentSelectedProject = null;
let currentIdeFilter = 'all';
let searchQuery = '';
let searchDebounceTimer = null;
let allProjectsList = [];

// DOM Elements: Views
const globalViewContainer = document.getElementById('globalViewContainer');
const projectViewContainer = document.getElementById('projectViewContainer');
const tabGlobalView = document.getElementById('tabGlobalView');
const tabProjectView = document.getElementById('tabProjectView');
const projectSelect = document.getElementById('projectSelect');
const btnBackToGlobal = document.getElementById('btnBackToGlobal');

// DOM Elements: Global KPIs
const kpiTotalCost = document.getElementById('kpiTotalCost');
const kpiCostAntigravity = document.getElementById('kpiCostAntigravity');
const kpiCostOpenCode = document.getElementById('kpiCostOpenCode');
const kpiTotalTokens = document.getElementById('kpiTotalTokens');
const kpiInTokens = document.getElementById('kpiInTokens');
const kpiOutTokens = document.getElementById('kpiOutTokens');
const kpiReasonTokens = document.getElementById('kpiReasonTokens');
const kpiTotalSessions = document.getElementById('kpiTotalSessions');
const kpiSessionsAntigravity = document.getElementById('kpiSessionsAntigravity');
const kpiSessionsOpenCode = document.getElementById('kpiSessionsOpenCode');

const syncStatusText = document.getElementById('syncStatusText');
const lastSyncTime = document.getElementById('lastSyncTime');
const btnSync = document.getElementById('btnSync');

// Global Panels
const ideCompareContainer = document.getElementById('ideCompareContainer');
const modelsContainer = document.getElementById('modelsContainer');
const projectsContainer = document.getElementById('projectsContainer');
const timelineChartWrapper = document.getElementById('timelineChartWrapper');
const sessionsTableBody = document.getElementById('sessionsTableBody');
const sessionSearch = document.getElementById('sessionSearch');

// Project View Elements
const projHeroName = document.getElementById('projHeroName');
const projHeroPath = document.getElementById('projHeroPath');
const projKpiCost = document.getElementById('projKpiCost');
const projKpiTokens = document.getElementById('projKpiTokens');
const projKpiIn = document.getElementById('projKpiIn');
const projKpiOut = document.getElementById('projKpiOut');
const projKpiReason = document.getElementById('projKpiReason');
const projKpiSessions = document.getElementById('projKpiSessions');
const projFirstDate = document.getElementById('projFirstDate');
const projLastDate = document.getElementById('projLastDate');
const projKpiModelCount = document.getElementById('projKpiModelCount');

const projModelsTableBody = document.getElementById('projModelsTableBody');
const projTimelineWrapper = document.getElementById('projTimelineWrapper');
const projSessionsTableBody = document.getElementById('projSessionsTableBody');

// Modal Elements
const linkProjectModal = document.getElementById('linkProjectModal');
const btnLinkProject = document.getElementById('btnLinkProject');
const btnCloseLinkModal = document.getElementById('btnCloseLinkModal');
const btnCancelLink = document.getElementById('btnCancelLink');
const btnSubmitLink = document.getElementById('btnSubmitLink');
const linkPathInput = document.getElementById('linkPath');
const linkNameInput = document.getElementById('linkName');
const linkBudgetInput = document.getElementById('linkBudget');

const logEventModal = document.getElementById('logEventModal');
const btnLogCommandModal = document.getElementById('btnLogCommandModal');
const btnCloseLogModal = document.getElementById('btnCloseLogModal');
const btnCancelLog = document.getElementById('btnCancelLog');
const btnSubmitLog = document.getElementById('btnSubmitLog');
const eventDescInput = document.getElementById('eventDesc');
const eventCmdInput = document.getElementById('eventCmd');
const eventModelSelect = document.getElementById('eventModel');
const eventTokensInput = document.getElementById('eventTokens');

const pricingModal = document.getElementById('pricingModal');
const btnPricingModal = document.getElementById('btnPricingModal');
const btnClosePricingModal = document.getElementById('btnClosePricingModal');
const btnClosePricingDone = document.getElementById('btnClosePricingDone');
const pricingTableBody = document.getElementById('pricingTableBody');

// Formatters
function formatNumber(num) {
  if (num === undefined || num === null) return '0';
  return new Intl.NumberFormat('en-US').format(num);
}

function formatUSD(num) {
  if (num === undefined || num === null) return '$0.00';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 4
  }).format(num);
}

function formatDate(isoStr) {
  if (!isoStr) return '--';
  try {
    const d = new Date(isoStr);
    return d.toLocaleString('es-ES', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (e) {
    return isoStr;
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// Mode Switching
function switchViewMode(mode, projectName = null) {
  currentViewMode = mode;
  if (mode === 'global') {
    tabGlobalView.classList.add('active');
    tabProjectView.classList.remove('active');
    globalViewContainer.style.display = 'block';
    projectViewContainer.style.display = 'none';
    currentSelectedProject = null;
    projectSelect.value = '';
    loadStats();
    loadSessions();
  } else {
    tabProjectView.classList.add('active');
    tabGlobalView.classList.remove('active');
    globalViewContainer.style.display = 'none';
    projectViewContainer.style.display = 'block';

    const projToLoad = projectName || currentSelectedProject || (allProjectsList[0] && allProjectsList[0].project_name);
    if (projToLoad) {
      currentSelectedProject = projToLoad;
      projectSelect.value = projToLoad;
      loadProjectDetail(projToLoad);
    }
  }
}

// Data Fetching: Global
async function loadStats() {
  try {
    const res = await fetch('/api/stats');
    if (!res.ok) throw new Error('Error al obtener estadísticas');
    const data = await res.json();
    renderStats(data);
  } catch (err) {
    console.error('Error fetching stats:', err);
  }
}

async function loadProjectsList() {
  try {
    const res = await fetch('/api/projects');
    if (!res.ok) throw new Error('Error al cargar proyectos');
    allProjectsList = await res.json();
    renderProjectSelectOptions();
    renderProjectsListWidget();
  } catch (err) {
    console.error('Error fetching projects list:', err);
  }
}

async function loadSessions() {
  try {
    const url = `/api/sessions?limit=60&ide=${encodeURIComponent(currentIdeFilter)}${searchQuery ? `&search=${encodeURIComponent(searchQuery)}` : ''}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Error al obtener sesiones');
    const data = await res.json();
    renderSessions(data);
  } catch (err) {
    console.error('Error fetching sessions:', err);
    sessionsTableBody.innerHTML = `<tr><td colspan="8" class="loading-cell text-danger">Error al cargar sesiones.</td></tr>`;
  }
}

// Data Fetching: Project Detail
async function loadProjectDetail(projectName) {
  if (!projectName) return;
  try {
    projHeroName.textContent = projectName;
    projHeroPath.textContent = 'Cargando información...';

    const res = await fetch(`/api/projects/${encodeURIComponent(projectName)}`);
    if (!res.ok) throw new Error('Error al cargar detalle del proyecto');
    const data = await res.json();
    renderProjectDetail(data);
  } catch (err) {
    console.error('Error fetching project detail:', err);
    projHeroPath.textContent = 'Error al cargar este proyecto.';
  }
}

// Rendering: Project Detail
function renderProjectDetail(detail) {
  const sm = detail.summary || {};
  const models = detail.models || [];
  const timeline = detail.timeline || [];
  const sessions = detail.sessions || [];
  const events = detail.events || [];

  // Hero Card
  projHeroName.textContent = sm.project_name || 'Proyecto';
  projHeroPath.textContent = sm.project_path || 'Ruta no especificada';

  // KPIs
  projKpiCost.textContent = formatUSD(sm.total_cost_usd);
  projKpiTokens.textContent = formatNumber(sm.total_tokens);
  projKpiIn.textContent = formatNumber(sm.input_tokens);
  projKpiOut.textContent = formatNumber(sm.output_tokens);
  projKpiReason.textContent = formatNumber(sm.reasoning_tokens);
  projKpiSessions.textContent = formatNumber(sm.session_count);
  projFirstDate.textContent = formatDate(sm.first_session_date);
  projLastDate.textContent = formatDate(sm.last_session_date);
  projKpiModelCount.textContent = models.length;

  // Render AI Models Breakdown Table
  const totalProjTokens = sm.total_tokens || 1;
  if (models.length === 0) {
    projModelsTableBody.innerHTML = `<tr><td colspan="8" class="loading-cell">Sin modelos registrados para este proyecto.</td></tr>`;
  } else {
    projModelsTableBody.innerHTML = models.map(m => {
      const pct = Math.round((m.total_tokens / totalProjTokens) * 100);
      return `
        <tr>
          <td>
            <strong>${escapeHtml(m.model_name)}</strong>
          </td>
          <td class="mono-num">${m.session_count}</td>
          <td class="mono-num">${formatNumber(m.input_tokens)}</td>
          <td class="mono-num">${formatNumber(m.output_tokens)}</td>
          <td class="mono-num">${formatNumber(m.reasoning_tokens)}</td>
          <td class="mono-num font-bold">${formatNumber(m.total_tokens)}</td>
          <td>
            <div style="display: flex; align-items: center; gap: 8px;">
              <div class="progress-track" style="width: 80px;">
                <div class="progress-fill fill-antigravity" style="width: ${pct}%;"></div>
              </div>
              <span class="mono-num" style="font-size: 11px;">${pct}%</span>
            </div>
          </td>
          <td class="mono-num cost-highlight">${formatUSD(m.cost_usd)}</td>
        </tr>
      `;
    }).join('');
  }

  // Render Historical Timeline
  if (timeline.length === 0) {
    projTimelineWrapper.innerHTML = `<p class="panel-hint" style="margin: auto;">No hay suficiente historial para graficar.</p>`;
  } else {
    const maxTokens = Math.max(...timeline.map(t => t.tokens), 1);
    projTimelineWrapper.innerHTML = timeline.map(t => {
      const heightPercent = Math.max(8, Math.round((t.tokens / maxTokens) * 100));
      const shortDate = t.date.slice(5);
      return `
        <div class="timeline-bar-col">
          <div class="timeline-bar-pill" style="height: ${heightPercent}%;" title="${t.date}: ${formatNumber(t.tokens)} tokens (${formatUSD(t.cost_usd)}) - ${t.session_count} eventos"></div>
          <span class="timeline-date-label">${shortDate}</span>
        </div>
      `;
    }).join('');
  }

  // Render Sessions and Processes
  if (sessions.length === 0) {
    projSessionsTableBody.innerHTML = `<tr><td colspan="8" class="loading-cell">Sin sesiones registradas.</td></tr>`;
  } else {
    projSessionsTableBody.innerHTML = sessions.map(s => {
      const isAntigravity = s.source_ide === 'antigravity';
      const ideBadge = isAntigravity ? 'badge-antigravity' : 'badge-opencode';
      const ideText = isAntigravity ? 'Antigravity' : 'OpenCode';

      return `
        <tr>
          <td><span class="badge-ide ${ideBadge}">${ideText}</span></td>
          <td>
            <div class="cell-project">${escapeHtml(s.title || 'Sesión de Trabajo')}</div>
          </td>
          <td><span class="mono-num">${escapeHtml(s.model_name)}</span></td>
          <td class="mono-num">${formatNumber(s.input_tokens)}</td>
          <td class="mono-num">${formatNumber(s.output_tokens)}</td>
          <td class="mono-num font-bold">${formatNumber(s.total_tokens)}</td>
          <td class="mono-num cost-highlight">${formatUSD(s.cost_usd)}</td>
          <td class="mono-num text-dim">${formatDate(s.start_time)}</td>
        </tr>
      `;
    }).join('');
  }
}

// Rendering: Dropdown & Widgets
function renderProjectSelectOptions() {
  const currentVal = projectSelect.value;
  projectSelect.innerHTML = `<option value="">📁 Seleccionar Proyecto...</option>` +
    allProjectsList.map(p => `
      <option value="${escapeHtml(p.project_name)}">${escapeHtml(p.project_name)} (${formatNumber(p.total_tokens)} tokens)</option>
    `).join('');
  
  if (currentVal) projectSelect.value = currentVal;
}

function renderProjectsListWidget() {
  if (allProjectsList.length === 0) {
    projectsContainer.innerHTML = `<p class="panel-hint">Sin proyectos registrados.</p>`;
    return;
  }

  projectsContainer.innerHTML = allProjectsList.slice(0, 7).map(p => `
    <div class="project-row" data-project="${escapeHtml(p.project_name)}" title="Ver auditoría de ${escapeHtml(p.project_name)}">
      <span class="project-name">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
        </svg>
        ${escapeHtml(p.project_name)}
      </span>
      <span class="project-tokens">${formatNumber(p.total_tokens)} tokens (${formatUSD(p.total_cost_usd)})</span>
    </div>
  `).join('');

  // Add click handlers on project rows
  document.querySelectorAll('.project-row').forEach(row => {
    row.addEventListener('click', () => {
      const pName = row.dataset.project;
      if (pName) {
        switchViewMode('project', pName);
      }
    });
  });
}

function renderStats(data) {
  const overall = data.overall || {};
  const byIde = data.by_ide || [];
  const byModel = data.by_model || [];
  const timeline = data.timeline || [];

  kpiTotalCost.textContent = formatUSD(overall.total_cost_usd);
  kpiTotalTokens.textContent = formatNumber(overall.total_tokens);
  kpiInTokens.textContent = formatNumber(overall.total_input_tokens);
  kpiOutTokens.textContent = formatNumber(overall.total_output_tokens);
  kpiReasonTokens.textContent = formatNumber(overall.total_reasoning_tokens);
  kpiTotalSessions.textContent = formatNumber(overall.total_sessions);

  let agCost = 0, agSessions = 0, agTokens = 0;
  let ocCost = 0, ocSessions = 0, ocTokens = 0;

  byIde.forEach(item => {
    if (item.source_ide === 'antigravity') {
      agCost = item.cost_usd || 0;
      agSessions = item.sessions || 0;
      agTokens = item.tokens || 0;
    } else if (item.source_ide === 'opencode') {
      ocCost = item.cost_usd || 0;
      ocSessions = item.sessions || 0;
      ocTokens = item.tokens || 0;
    }
  });

  kpiCostAntigravity.textContent = formatUSD(agCost);
  kpiCostOpenCode.textContent = formatUSD(ocCost);
  kpiSessionsAntigravity.textContent = formatNumber(agSessions);
  kpiSessionsOpenCode.textContent = formatNumber(ocSessions);

  if (data.last_sync && data.last_sync.timestamp) {
    lastSyncTime.textContent = data.last_sync.timestamp.split(' ')[1] || data.last_sync.timestamp;
  }

  const totalTokens = (overall.total_tokens || 1);
  const agPercent = Math.round((agTokens / totalTokens) * 100);
  const ocPercent = Math.round((ocTokens / totalTokens) * 100);

  ideCompareContainer.innerHTML = `
    <div class="ide-stat-item">
      <div class="ide-stat-header">
        <span class="ide-badge-label"><span class="badge-ide badge-antigravity">Antigravity</span></span>
        <span class="mono-num">${formatNumber(agTokens)} tokens (${agPercent}%) • ${formatUSD(agCost)}</span>
      </div>
      <div class="progress-track">
        <div class="progress-fill fill-antigravity" style="width: ${agPercent}%;"></div>
      </div>
    </div>
    <div class="ide-stat-item">
      <div class="ide-stat-header">
        <span class="ide-badge-label"><span class="badge-ide badge-opencode">OpenCode</span></span>
        <span class="mono-num">${formatNumber(ocTokens)} tokens (${ocPercent}%) • ${formatUSD(ocCost)}</span>
      </div>
      <div class="progress-track">
        <div class="progress-fill fill-opencode" style="width: ${ocPercent}%;"></div>
      </div>
    </div>
  `;

  if (byModel.length === 0) {
    modelsContainer.innerHTML = `<p class="panel-hint">Sin datos de modelos.</p>`;
  } else {
    modelsContainer.innerHTML = byModel.slice(0, 5).map(m => `
      <div class="model-row">
        <span class="model-name" title="${m.model_name}">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
          </svg>
          ${m.model_name || 'Desconocido'}
        </span>
        <span class="model-tokens">${formatNumber(m.tokens)} (${formatUSD(m.cost_usd)})</span>
      </div>
    `).join('');
  }

  if (timeline.length === 0) {
    timelineChartWrapper.innerHTML = `<p class="panel-hint" style="margin: auto;">No hay suficiente historial para graficar.</p>`;
  } else {
    const maxTokens = Math.max(...timeline.map(t => t.tokens), 1);
    timelineChartWrapper.innerHTML = timeline.map(t => {
      const heightPercent = Math.max(8, Math.round((t.tokens / maxTokens) * 100));
      const shortDate = t.date.slice(5);
      return `
        <div class="timeline-bar-col">
          <div class="timeline-bar-pill" style="height: ${heightPercent}%;" title="${t.date}: ${formatNumber(t.tokens)} tokens (${formatUSD(t.cost_usd)})"></div>
          <span class="timeline-date-label">${shortDate}</span>
        </div>
      `;
    }).join('');
  }
}

function renderSessions(sessions) {
  if (!sessions || sessions.length === 0) {
    sessionsTableBody.innerHTML = `<tr><td colspan="8" class="loading-cell">No se encontraron sesiones para los filtros seleccionados.</td></tr>`;
    return;
  }

  sessionsTableBody.innerHTML = sessions.map(s => {
    const isAntigravity = s.source_ide === 'antigravity';
    const ideBadgeClass = isAntigravity ? 'badge-antigravity' : 'badge-opencode';
    const ideName = isAntigravity ? 'Antigravity' : 'OpenCode';

    return `
      <tr>
        <td><span class="badge-ide ${ideBadgeClass}">${ideName}</span></td>
        <td>
          <div class="cell-project">${escapeHtml(s.project_name || 'General')}</div>
          <div class="cell-title">${escapeHtml(s.title || '')}</div>
        </td>
        <td><span class="mono-num">${escapeHtml(s.model_name || s.model_id || 'Default')}</span></td>
        <td class="mono-num">${formatNumber(s.input_tokens)}</td>
        <td class="mono-num">${formatNumber(s.output_tokens)}</td>
        <td class="mono-num font-bold">${formatNumber(s.total_tokens)}</td>
        <td class="mono-num cost-highlight">${formatUSD(s.cost_usd)}</td>
        <td class="mono-num text-dim">${formatDate(s.start_time)}</td>
      </tr>
    `;
  }).join('');
}

// Event Listeners: Navigation
tabGlobalView.addEventListener('click', () => switchViewMode('global'));
tabProjectView.addEventListener('click', () => switchViewMode('project'));
btnBackToGlobal.addEventListener('click', () => switchViewMode('global'));

projectSelect.addEventListener('change', (e) => {
  const pName = e.target.value;
  if (pName) {
    switchViewMode('project', pName);
  } else {
    switchViewMode('global');
  }
});

// Sync Button
btnSync.addEventListener('click', async () => {
  btnSync.classList.add('spinning');
  syncStatusText.textContent = 'Sincronizando...';
  try {
    const res = await fetch('/api/sync', { method: 'POST' });
    await Promise.all([loadStats(), loadProjectsList(), loadSessions()]);
    if (currentViewMode === 'project' && currentSelectedProject) {
      loadProjectDetail(currentSelectedProject);
    }
    syncStatusText.textContent = 'Actualizado';
  } catch (err) {
    console.error('Error during sync:', err);
    syncStatusText.textContent = 'Error';
  } finally {
    btnSync.classList.remove('spinning');
  }
});

// Table Filter Tabs
document.querySelectorAll('.filter-tab').forEach(tab => {
  tab.addEventListener('click', (e) => {
    document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    currentIdeFilter = tab.dataset.ide;
    loadSessions();
  });
});

// Search input debounce
sessionSearch.addEventListener('input', (e) => {
  clearTimeout(searchDebounceTimer);
  searchDebounceTimer = setTimeout(() => {
    searchQuery = e.target.value.trim();
    loadSessions();
  }, 300);
});

// Modal: Link Project
btnLinkProject.addEventListener('click', () => {
  linkProjectModal.classList.add('open');
});
btnCloseLinkModal.addEventListener('click', () => linkProjectModal.classList.remove('open'));
btnCancelLink.addEventListener('click', () => linkProjectModal.classList.remove('open'));

btnSubmitLink.addEventListener('click', async () => {
  const pathVal = linkPathInput.value.trim();
  const nameVal = linkNameInput.value.trim();
  const budgetVal = parseFloat(linkBudgetInput.value) || 0.0;

  if (!pathVal) {
    alert('Por favor ingresa la ruta de la carpeta del proyecto.');
    return;
  }

  try {
    const res = await fetch('/api/projects/init', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: pathVal, name: nameVal || null, budget: budgetVal })
    });
    if (!res.ok) throw new Error('Error al vincular proyecto');
    linkProjectModal.classList.remove('open');
    linkPathInput.value = '';
    linkNameInput.value = '';
    await loadProjectsList();
    if (nameVal) {
      switchViewMode('project', nameVal);
    }
  } catch (err) {
    alert('Error al vincular el proyecto: ' + err.message);
  }
});

// Modal: Log Process Event
btnLogCommandModal.addEventListener('click', () => {
  logEventModal.classList.add('open');
});
btnCloseLogModal.addEventListener('click', () => logEventModal.classList.remove('open'));
btnCancelLog.addEventListener('click', () => logEventModal.classList.remove('open'));

btnSubmitLog.addEventListener('click', async () => {
  if (!currentSelectedProject) return;
  const desc = eventDescInput.value.trim();
  const cmd = eventCmdInput.value.trim();
  const model = eventModelSelect.value;
  const tokens = parseInt(eventTokensInput.value, 10) || 0;

  if (!desc && !cmd) {
    alert('Por favor especifica una descripción o comando.');
    return;
  }

  try {
    const res = await fetch(`/api/projects/${encodeURIComponent(currentSelectedProject)}/event`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description: desc, command: cmd, model: model, tokens: tokens })
    });
    if (!res.ok) throw new Error('Error al registrar evento');
    logEventModal.classList.remove('open');
    eventDescInput.value = '';
    eventCmdInput.value = '';
    loadProjectDetail(currentSelectedProject);
  } catch (err) {
    alert('Error: ' + err.message);
  }
});

// Modal: Pricing
btnPricingModal.addEventListener('click', () => {
  pricingModal.classList.add('open');
  loadPricing();
});
btnClosePricingModal.addEventListener('click', () => pricingModal.classList.remove('open'));
btnClosePricingDone.addEventListener('click', () => pricingModal.classList.remove('open'));

async function loadPricing() {
  try {
    const res = await fetch('/api/pricing');
    const models = await res.json();
    pricingTableBody.innerHTML = Object.keys(models).map(key => {
      const m = models[key];
      return `
        <tr>
          <td><strong>${escapeHtml(m.name || key)}</strong></td>
          <td class="mono-num">$${m.input_per_million.toFixed(2)}</td>
          <td class="mono-num">$${m.output_per_million.toFixed(2)}</td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    console.error('Error fetching pricing:', err);
  }
}

// Initial Boot
async function initApp() {
  await Promise.all([loadStats(), loadProjectsList(), loadSessions()]);

  // Check URL query param ?project=...
  const urlParams = new URLSearchParams(window.location.search);
  const projParam = urlParams.get('project');
  if (projParam) {
    switchViewMode('project', projParam);
  }
}

initApp();

// Periodic Auto-Refresh
setInterval(() => {
  if (currentViewMode === 'global') {
    loadStats();
  } else if (currentSelectedProject) {
    loadProjectDetail(currentSelectedProject);
  }
}, 20000);
