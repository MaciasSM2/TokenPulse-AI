// TokenPulse AI - Multi-IDE, Multi-Model & Date-Range Project-Centric Logic

let currentViewMode = 'global'; // 'global' | 'project'
let currentSelectedProject = null;
let currentIdeFilter = 'all';
let searchQuery = '';
let searchDebounceTimer = null;
let allProjectsList = [];
let cachedPricingModels = {};
let currentPricingProvider = 'all';

// Date Filter State (Defaults to 'today' as requested)
let currentPreset = 'today';
let currentStartDate = null;
let currentEndDate = null;
let dateBounds = null; // { min_date, max_date, today }

// DOM Elements: Views
const globalViewContainer = document.getElementById('globalViewContainer');
const projectViewContainer = document.getElementById('projectViewContainer');
const tabGlobalView = document.getElementById('tabGlobalView');
const tabProjectView = document.getElementById('tabProjectView');
const projectSelect = document.getElementById('projectSelect');
const btnBackToGlobal = document.getElementById('btnBackToGlobal');
const ideHubContainer = document.getElementById('ideHubContainer');

// DOM Elements: Date Range Filter Bar
const globalPresetButtons = document.getElementById('globalPresetButtons');
const projPresetButtons = document.getElementById('projPresetButtons');
const dateRangeStart = document.getElementById('dateRangeStart');
const dateRangeEnd = document.getElementById('dateRangeEnd');
const btnApplyCustomDates = document.getElementById('btnApplyCustomDates');
const dateActivePillText = document.getElementById('dateActivePillText');
const projDateActivePillText = document.getElementById('projDateActivePillText');

// DOM Elements: Global KPIs
const kpiLabelCost = document.getElementById('kpiLabelCost');
const kpiTotalCost = document.getElementById('kpiTotalCost');
const kpiCostAntigravity = document.getElementById('kpiCostAntigravity');
const kpiCostOpenCode = document.getElementById('kpiCostOpenCode');
const kpiCostLifetime = document.getElementById('kpiCostLifetime');

const kpiLabelTokens = document.getElementById('kpiLabelTokens');
const kpiTotalTokens = document.getElementById('kpiTotalTokens');
const kpiInTokens = document.getElementById('kpiInTokens');
const kpiOutTokens = document.getElementById('kpiOutTokens');
const kpiTokensLifetime = document.getElementById('kpiTokensLifetime');

const kpiLabelSessions = document.getElementById('kpiLabelSessions');
const kpiTotalSessions = document.getElementById('kpiTotalSessions');
const kpiSessionsAntigravity = document.getElementById('kpiSessionsAntigravity');
const kpiSessionsOpenCode = document.getElementById('kpiSessionsOpenCode');
const kpiSessionsLifetime = document.getElementById('kpiSessionsLifetime');

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
const projLabelCost = document.getElementById('projLabelCost');
const projKpiCost = document.getElementById('projKpiCost');
const projCostLifetime = document.getElementById('projCostLifetime');
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
const eventIdeSelect = document.getElementById('eventIde');
const eventDescInput = document.getElementById('eventDesc');
const eventCmdInput = document.getElementById('eventCmd');
const eventModelSelect = document.getElementById('eventModel');
const eventTokensInput = document.getElementById('eventTokens');

const pricingModal = document.getElementById('pricingModal');
const btnPricingModal = document.getElementById('btnPricingModal');
const btnClosePricingModal = document.getElementById('btnClosePricingModal');
const btnClosePricingDone = document.getElementById('btnClosePricingDone');
const pricingTableBody = document.getElementById('pricingTableBody');
const providerFilterTabs = document.getElementById('providerFilterTabs');

// Helpers for IDE Info
const IDE_REGISTRY = {
  antigravity: { name: 'Antigravity IDE', badgeClass: 'badge-antigravity', color: '#38bdf8' },
  opencode: { name: 'OpenCode Desktop', badgeClass: 'badge-opencode', color: '#c084fc' },
  claude: { name: 'Claude Code', badgeClass: 'badge-claude', color: '#fbbf24' },
  cursor: { name: 'Cursor AI', badgeClass: 'badge-cursor', color: '#00f0ff' },
  windsurf: { name: 'Windsurf', badgeClass: 'badge-windsurf', color: '#22d3ee' },
  vscode: { name: 'VS Code AI', badgeClass: 'badge-vscode', color: '#60a5fa' },
  ollama: { name: 'Ollama Local', badgeClass: 'badge-ollama', color: '#34d399' },
  continue: { name: 'Continue.dev', badgeClass: 'badge-continue', color: '#f472b6' },
  aider: { name: 'Aider Pair', badgeClass: 'badge-aider', color: '#a3e635' }
};

function getIdeInfo(ideKey) {
  if (!ideKey) return { name: 'General', badgeClass: 'badge-ide', color: '#94a3b8' };
  const key = ideKey.toLowerCase();
  return IDE_REGISTRY[key] || {
    name: ideKey.charAt(0).toUpperCase() + ideKey.slice(1),
    badgeClass: 'badge-ide',
    color: '#38bdf8'
  };
}

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

function formatDateOnly(d) {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// Date Range Calculation Logic
function computeDatesForPreset(preset) {
  const baseToday = (dateBounds && dateBounds.today) ? new Date(dateBounds.today + 'T12:00:00') : new Date();
  const todayStr = formatDateOnly(baseToday);

  if (preset === 'today') {
    const startStr = (dateBounds && dateBounds.today_local) ? dateBounds.today_local : todayStr;
    const endStr = (dateBounds && dateBounds.today_utc) ? dateBounds.today_utc : todayStr;
    return { start: startStr, end: endStr, label: `Hoy (${startStr})` };
  } else if (preset === '3days') {
    const s = new Date(baseToday);
    s.setDate(s.getDate() - 2);
    const endStr = (dateBounds && dateBounds.today_utc) ? dateBounds.today_utc : todayStr;
    return { start: formatDateOnly(s), end: endStr, label: `3 Días (${formatDateOnly(s)} a ${endStr})` };
  } else if (preset === '7days') {
    const s = new Date(baseToday);
    s.setDate(s.getDate() - 6);
    const endStr = (dateBounds && dateBounds.today_utc) ? dateBounds.today_utc : todayStr;
    return { start: formatDateOnly(s), end: endStr, label: `1 Semana (${formatDateOnly(s)} a ${endStr})` };
  } else if (preset === '30days') {
    const s = new Date(baseToday);
    s.setDate(s.getDate() - 29);
    const endStr = (dateBounds && dateBounds.today_utc) ? dateBounds.today_utc : todayStr;
    return { start: formatDateOnly(s), end: endStr, label: `1 Mes (${formatDateOnly(s)} a ${endStr})` };
  } else if (preset === 'all') {
    return { start: null, end: null, label: 'Todo el Histórico (Ilimitado)' };
  }
  return { start: currentStartDate, end: currentEndDate, label: `${currentStartDate || '--'} a ${currentEndDate || '--'}` };
}

function setDatePreset(preset, customStart = null, customEnd = null) {
  currentPreset = preset;

  if (preset === 'custom') {
    currentStartDate = customStart;
    currentEndDate = customEnd;
    const label = `${customStart || 'Inicio'} ➔ ${customEnd || 'Hoy'}`;
    updateDateUI(preset, customStart, customEnd, label);
  } else {
    const res = computeDatesForPreset(preset);
    currentStartDate = res.start;
    currentEndDate = res.end;
    updateDateUI(preset, res.start, res.end, res.label);
  }

  // Reload current view
  if (currentViewMode === 'global') {
    loadStats();
    loadSessions();
  } else if (currentSelectedProject) {
    loadProjectDetail(currentSelectedProject);
  }
}

function updateDateUI(preset, start, end, label) {
  // Update inputs
  if (dateRangeStart && start) dateRangeStart.value = start;
  if (dateRangeEnd && end) dateRangeEnd.value = end;

  // Update pill indicators
  if (dateActivePillText) dateActivePillText.textContent = label;
  if (projDateActivePillText) projDateActivePillText.textContent = label;

  // Update tab highlights on global and project preset buttons
  document.querySelectorAll('.preset-tab').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.preset === preset);
  });
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
    loadIdesHub();
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

// Data Fetching: Global Stats
async function loadStats() {
  try {
    let url = '/api/stats';
    const params = [];
    if (currentStartDate) params.push(`start_date=${encodeURIComponent(currentStartDate)}`);
    if (currentEndDate) params.push(`end_date=${encodeURIComponent(currentEndDate)}`);
    if (params.length > 0) url += '?' + params.join('&');

    const res = await fetch(url);
    if (!res.ok) throw new Error('Error al obtener estadísticas');
    const data = await res.json();

    // Store date bounds if received
    if (data.date_bounds) {
      dateBounds = data.date_bounds;
      if (dateRangeStart && !dateRangeStart.min) {
        dateRangeStart.min = dateBounds.min_date;
        dateRangeStart.max = dateBounds.today;
      }
      if (dateRangeEnd && !dateRangeEnd.min) {
        dateRangeEnd.min = dateBounds.min_date;
        dateRangeEnd.max = dateBounds.today;
      }
    }

    renderStats(data);
  } catch (err) {
    console.error('Error fetching stats:', err);
  }
}

async function loadIdesHub() {
  if (!ideHubContainer) return;
  try {
    const res = await fetch('/api/ides');
    if (!res.ok) throw new Error('Error al obtener IDEs');
    const ides = await res.json();
    renderIdesHub(ides);
  } catch (err) {
    console.error('Error fetching IDEs:', err);
  }
}

function renderIdesHub(ides) {
  if (!ideHubContainer) return;
  ideHubContainer.innerHTML = ides.map(ide => {
    const isActive = ide.status === 'active';
    const isDetected = ide.detected;
    const dotClass = isActive ? 'active' : (isDetected ? 'detected' : 'inactive');

    let statText = 'No detectado';
    if (isActive && ide.tokens_count > 0) {
      statText = `${formatNumber(ide.tokens_count)} tokens • ${formatUSD(ide.cost_usd)}`;
    } else if (isDetected) {
      statText = 'Detectado en Disco';
    }

    return `
      <div class="ide-hub-card" data-ide-id="${escapeHtml(ide.id)}" title="${escapeHtml(ide.description || ide.name)} - Haz clic para filtrar">
        <div class="ide-hub-info">
          <span class="ide-hub-dot ${dotClass}"></span>
          <div>
            <div class="ide-hub-title">${escapeHtml(ide.name)}</div>
            <div class="ide-hub-vendor">${escapeHtml(ide.vendor)}</div>
          </div>
        </div>
        <div class="ide-hub-stats">
          <span class="badge-ide ${ide.badge_class || 'badge-ide'}" style="font-size: 10px; padding: 2px 6px;">
            ${isActive ? 'Activo' : (isDetected ? 'Detectado' : 'Pendiente')}
          </span>
          <div style="color: var(--text-dim); margin-top: 3px; font-size: 10px;">${statText}</div>
        </div>
      </div>
    `;
  }).join('');

  // Add click handlers on IDE cards to filter sessions
  document.querySelectorAll('.ide-hub-card').forEach(card => {
    card.addEventListener('click', () => {
      const ideId = card.dataset.ideId;
      if (ideId) {
        document.querySelectorAll('.filter-tab').forEach(t => {
          t.classList.toggle('active', t.dataset.ide === ideId);
        });
        currentIdeFilter = ideId;
        loadSessions();
      }
    });
  });
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
    let url = `/api/sessions?limit=80&ide=${encodeURIComponent(currentIdeFilter)}`;
    if (searchQuery) url += `&search=${encodeURIComponent(searchQuery)}`;
    if (currentStartDate) url += `&start_date=${encodeURIComponent(currentStartDate)}`;
    if (currentEndDate) url += `&end_date=${encodeURIComponent(currentEndDate)}`;

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

    let url = `/api/projects/${encodeURIComponent(projectName)}`;
    const params = [];
    if (currentStartDate) params.push(`start_date=${encodeURIComponent(currentStartDate)}`);
    if (currentEndDate) params.push(`end_date=${encodeURIComponent(currentEndDate)}`);
    if (params.length > 0) url += '?' + params.join('&');

    const res = await fetch(url);
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
  const life = detail.lifetime || {};
  const models = detail.models || [];
  const timeline = detail.timeline || [];
  const sessions = detail.sessions || [];

  // Hero Card
  projHeroName.textContent = sm.project_name || 'Proyecto';
  projHeroPath.textContent = sm.project_path || 'Ruta no especificada';

  // KPIs
  projKpiCost.textContent = formatUSD(sm.total_cost_usd);
  if (projCostLifetime) {
    projCostLifetime.textContent = formatUSD(life.lifetime_cost_usd || sm.total_cost_usd);
  }
  if (projLabelCost) {
    projLabelCost.textContent = (currentPreset === 'today') ? 'Gasto de Hoy en este Proyecto' : 'Gasto del Período';
  }

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
    projModelsTableBody.innerHTML = `<tr><td colspan="8" class="loading-cell">Sin consumo registrado para este proyecto en el período seleccionado.</td></tr>`;
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
    projTimelineWrapper.innerHTML = `<p class="panel-hint" style="margin: auto;">No hay suficiente actividad en este rango para graficar.</p>`;
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
    projSessionsTableBody.innerHTML = `<tr><td colspan="8" class="loading-cell">Sin sesiones registradas en este período.</td></tr>`;
  } else {
    projSessionsTableBody.innerHTML = sessions.map(s => {
      const ideInfo = getIdeInfo(s.source_ide);
      return `
        <tr>
          <td><span class="badge-ide ${ideInfo.badgeClass}">${escapeHtml(ideInfo.name)}</span></td>
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
  const lifetime = data.lifetime || {};
  const byIde = data.by_ide || [];
  const byModel = data.by_model || [];
  const timeline = data.timeline || [];

  // Dynamic KPI Labels based on active preset
  if (kpiLabelCost) {
    if (currentPreset === 'today') {
      kpiLabelCost.textContent = 'Gasto de Hoy';
      kpiLabelTokens.textContent = 'Tokens de Hoy';
      kpiLabelSessions.textContent = 'Sesiones de Hoy';
    } else if (currentPreset === '3days') {
      kpiLabelCost.textContent = 'Gasto (3 Días)';
      kpiLabelTokens.textContent = 'Tokens (3 Días)';
      kpiLabelSessions.textContent = 'Sesiones (3 Días)';
    } else if (currentPreset === '7days') {
      kpiLabelCost.textContent = 'Gasto (1 Semana)';
      kpiLabelTokens.textContent = 'Tokens (1 Semana)';
      kpiLabelSessions.textContent = 'Sesiones (1 Semana)';
    } else if (currentPreset === '30days') {
      kpiLabelCost.textContent = 'Gasto (1 Mes)';
      kpiLabelTokens.textContent = 'Tokens (1 Mes)';
      kpiLabelSessions.textContent = 'Sesiones (1 Mes)';
    } else if (currentPreset === 'all') {
      kpiLabelCost.textContent = 'Gasto Total Acumulado';
      kpiLabelTokens.textContent = 'Tokens Totales Consumidos';
      kpiLabelSessions.textContent = 'Sesiones de Desarrollo';
    } else {
      kpiLabelCost.textContent = 'Gasto del Período';
      kpiLabelTokens.textContent = 'Tokens del Período';
      kpiLabelSessions.textContent = 'Sesiones del Período';
    }
  }

  // Values: Period totals
  kpiTotalCost.textContent = formatUSD(overall.total_cost_usd);
  if (kpiCostLifetime) kpiCostLifetime.textContent = formatUSD(lifetime.total_cost_usd);

  kpiTotalTokens.textContent = formatNumber(overall.total_tokens);
  if (kpiTokensLifetime) kpiTokensLifetime.textContent = formatNumber(lifetime.total_tokens);

  kpiInTokens.textContent = formatNumber(overall.total_input_tokens);
  kpiOutTokens.textContent = formatNumber(overall.total_output_tokens);

  kpiTotalSessions.textContent = formatNumber(overall.total_sessions);
  if (kpiSessionsLifetime) kpiSessionsLifetime.textContent = formatNumber(lifetime.total_sessions);

  let agCost = 0, agSessions = 0;
  let ocCost = 0, ocSessions = 0;

  byIde.forEach(item => {
    if (item.source_ide === 'antigravity') {
      agCost = item.cost_usd || 0;
      agSessions = item.sessions || 0;
    } else if (item.source_ide === 'opencode') {
      ocCost = item.cost_usd || 0;
      ocSessions = item.sessions || 0;
    }
  });

  kpiCostAntigravity.textContent = formatUSD(agCost);
  kpiCostOpenCode.textContent = formatUSD(ocCost);
  kpiSessionsAntigravity.textContent = formatNumber(agSessions);
  kpiSessionsOpenCode.textContent = formatNumber(ocSessions);

  if (data.last_sync && data.last_sync.timestamp) {
    lastSyncTime.textContent = data.last_sync.timestamp.split(' ')[1] || data.last_sync.timestamp;
  }

  // Multi-IDE Comparison Bars
  const totalTokens = (overall.total_tokens || 1);
  if (byIde.length === 0) {
    ideCompareContainer.innerHTML = `<p class="panel-hint">Sin actividad en este período para los IDEs.</p>`;
  } else {
    ideCompareContainer.innerHTML = byIde.map(item => {
      const info = getIdeInfo(item.source_ide);
      const pct = Math.round((item.tokens / totalTokens) * 100);
      return `
        <div class="ide-stat-item">
          <div class="ide-stat-header">
            <span class="ide-badge-label"><span class="badge-ide ${info.badgeClass}">${escapeHtml(info.name)}</span></span>
            <span class="mono-num">${formatNumber(item.tokens)} tokens (${pct}%) • ${formatUSD(item.cost_usd)}</span>
          </div>
          <div class="progress-track">
            <div class="progress-fill" style="width: ${pct}%; background: ${info.color};"></div>
          </div>
        </div>
      `;
    }).join('');
  }

  // Top Models
  if (byModel.length === 0) {
    modelsContainer.innerHTML = `<p class="panel-hint">Sin datos de modelos en este período.</p>`;
  } else {
    modelsContainer.innerHTML = byModel.slice(0, 6).map(m => `
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

  // Timeline
  if (timeline.length === 0) {
    timelineChartWrapper.innerHTML = `<p class="panel-hint" style="margin: auto;">No hay suficiente actividad en este rango para graficar.</p>`;
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
    sessionsTableBody.innerHTML = `<tr><td colspan="8" class="loading-cell">No se encontraron sesiones para los filtros de fecha y entorno seleccionados.</td></tr>`;
    return;
  }

  sessionsTableBody.innerHTML = sessions.map(s => {
    const ideInfo = getIdeInfo(s.source_ide);

    return `
      <tr>
        <td><span class="badge-ide ${ideInfo.badgeClass}">${escapeHtml(ideInfo.name)}</span></td>
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

// Preset Buttons Event Listeners
function setupPresetButtonListeners() {
  document.querySelectorAll('.preset-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      const preset = btn.dataset.preset;
      if (preset) {
        setDatePreset(preset);
      }
    });
  });

  if (btnApplyCustomDates) {
    btnApplyCustomDates.addEventListener('click', () => {
      const start = dateRangeStart ? dateRangeStart.value : null;
      const end = dateRangeEnd ? dateRangeEnd.value : null;

      if (!start && !end) {
        setDatePreset('all');
        return;
      }

      setDatePreset('custom', start, end);
    });
  }
}

// Sync Button
btnSync.addEventListener('click', async () => {
  btnSync.classList.add('spinning');
  syncStatusText.textContent = 'Sincronizando...';
  try {
    const res = await fetch('/api/sync', { method: 'POST' });
    await Promise.all([loadStats(), loadIdesHub(), loadProjectsList(), loadSessions()]);
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
  const ide = eventIdeSelect ? eventIdeSelect.value : 'antigravity';
  const tokens = parseInt(eventTokensInput.value, 10) || 0;

  if (!desc && !cmd) {
    alert('Por favor especifica una descripción o comando.');
    return;
  }

  try {
    const res = await fetch(`/api/projects/${encodeURIComponent(currentSelectedProject)}/event`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description: desc, command: cmd, model: model, ide: ide, tokens: tokens })
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

// Modal: Pricing & Provider Filtering
btnPricingModal.addEventListener('click', () => {
  pricingModal.classList.add('open');
  loadPricing();
});
btnClosePricingModal.addEventListener('click', () => pricingModal.classList.remove('open'));
btnClosePricingDone.addEventListener('click', () => pricingModal.classList.remove('open'));

async function loadPricing() {
  try {
    const res = await fetch('/api/pricing');
    cachedPricingModels = await res.json();
    renderPricingTable();
    updateEventModelSelect();
  } catch (err) {
    console.error('Error fetching pricing:', err);
  }
}

function renderPricingTable() {
  const keys = Object.keys(cachedPricingModels);
  const filteredKeys = keys.filter(key => {
    if (currentPricingProvider === 'all') return true;
    const provider = cachedPricingModels[key].provider || 'General';
    return provider === currentPricingProvider;
  });

  if (filteredKeys.length === 0) {
    pricingTableBody.innerHTML = `<tr><td colspan="4" class="loading-cell">Sin modelos para este proveedor.</td></tr>`;
    return;
  }

  pricingTableBody.innerHTML = filteredKeys.map(key => {
    const m = cachedPricingModels[key];
    const prov = m.provider || 'General';
    return `
      <tr>
        <td><span class="mono-num" style="font-size: 11px; color: var(--text-dim);">${escapeHtml(prov)}</span></td>
        <td><strong>${escapeHtml(m.name || key)}</strong></td>
        <td class="mono-num">$${m.input_per_million.toFixed(2)}</td>
        <td class="mono-num">$${m.output_per_million.toFixed(2)}</td>
      </tr>
    `;
  }).join('');
}

function updateEventModelSelect() {
  if (!eventModelSelect || Object.keys(cachedPricingModels).length === 0) return;
  const currentVal = eventModelSelect.value;
  eventModelSelect.innerHTML = Object.keys(cachedPricingModels).map(key => {
    const m = cachedPricingModels[key];
    return `<option value="${escapeHtml(key)}">${escapeHtml(m.name || key)} ($${m.input_per_million.toFixed(2)} / $${m.output_per_million.toFixed(2)})</option>`;
  }).join('');
  if (currentVal && cachedPricingModels[currentVal]) {
    eventModelSelect.value = currentVal;
  }
}

// Provider Filter Tabs Click Listeners
if (providerFilterTabs) {
  providerFilterTabs.querySelectorAll('.provider-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      providerFilterTabs.querySelectorAll('.provider-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      currentPricingProvider = tab.dataset.provider;
      renderPricingTable();
    });
  });
}

// Scan Projects Button
const btnScanProjects = document.getElementById('btnScanProjects');
if (btnScanProjects) {
  btnScanProjects.addEventListener('click', async () => {
    btnScanProjects.classList.add('spinning');
    try {
      const res = await fetch('/api/projects/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      const data = await res.json();
      alert(`¡Escaneo Completado! Se detectaron y vincularon ${data.count} proyectos.`);
      await Promise.all([loadStats(), loadIdesHub(), loadProjectsList(), loadSessions()]);
    } catch (err) {
      alert('Error durante el escaneo: ' + err.message);
    } finally {
      btnScanProjects.classList.remove('spinning');
    }
  });
}

// Export Project Report Button
const btnExportProject = document.getElementById('btnExportProject');
if (btnExportProject) {
  btnExportProject.addEventListener('click', () => {
    if (!currentSelectedProject) return;
    window.open(`/api/projects/${encodeURIComponent(currentSelectedProject)}/export`, '_blank');
  });
}

// Initial Boot
async function initApp() {
  setupPresetButtonListeners();

  // First fetch stats to get server dates and bounds
  await loadStats();

  // Initialize preset to 'today' by default
  const todayPreset = computeDatesForPreset('today');
  currentStartDate = todayPreset.start;
  currentEndDate = todayPreset.end;
  updateDateUI('today', todayPreset.start, todayPreset.end, todayPreset.label);

  await Promise.all([
    loadStats(),
    loadIdesHub(),
    loadProjectsList(),
    loadSessions(),
    loadPricing()
  ]);

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
    loadIdesHub();
  } else if (currentSelectedProject) {
    loadProjectDetail(currentSelectedProject);
  }
}, 20000);
