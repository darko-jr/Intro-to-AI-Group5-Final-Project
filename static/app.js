const state = {
  currentInputs: {
    G1: 11,
    failures: 0,
    absences: 4,
    age: 17,
    health: 4,
    freetime: 3,
    Walc: 1,
    goout: 3,
    Medu: 2,
    famrel: 4
  },
  lastPrediction: null,
  whatIfBaseline: null,
  activeStudent: null,
  roster: {
    all: [],
    filtered: [],
    page: 1,
    pageSize: 8,
    filter: 'all',
    search: '',
    selectedId: null
  },
  batchData: [],
  batchFilter: 'all',
  history: JSON.parse(localStorage.getItem('student_risk_history_v3') || '[]'),
  debounceTimer: null
};

const METADATA = {
  G1: { label: 'First Period Grade (G1)', suffix: ' / 20' },
  failures: { label: 'Past Failures', suffix: '' },
  absences: { label: 'Term Absences', suffix: ' days' },
  age: { label: 'Student Age', suffix: ' yrs' },
  health: { label: 'Health Status', suffix: ' / 5' },
  freetime: { label: 'Free Time', suffix: ' / 5' },
  Walc: { label: 'Weekend Alcohol', suffix: ' / 5' },
  goout: { label: 'Going Out', suffix: ' / 5' },
  Medu: { label: "Mother's Education", suffix: '' },
  famrel: { label: 'Family Relationships', suffix: ' / 5' }
};

const MEDU_NAMES = ['None (0)', 'Primary (1)', 'Middle (2)', 'Secondary (3)', 'Higher Ed (4)'];

document.addEventListener('DOMContentLoaded', async () => {
  setupSidebarNavigation();
  setupDropzone();
  updateHistoryCount();
  renderHistoryTable();
  await initRoster();
  
  const savedTab = localStorage.getItem('smartech_saved_active_tab');
  if (savedTab && document.getElementById(`tab-${savedTab}`)) {
    switchToTab(savedTab);
  }
});

function setupSidebarNavigation() {
  document.querySelectorAll('.nav-item').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTab = btn.dataset.tab;
      switchToTab(targetTab);
    });
  });
}

function switchToTab(tabName) {
  try {
    localStorage.setItem('smartech_saved_active_tab', tabName);
  } catch (e) {}

  document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));

  const btn = document.getElementById(`btn-tab-${tabName}`);
  const panel = document.getElementById(`tab-${tabName}`);

  if (btn) btn.classList.add('active');
  if (panel) panel.classList.add('active');

  if (tabName === 'whatif') {
    syncWhatIfWithBaseline();
  }
}

function updateInput(feature, value) {
  const numVal = parseFloat(value);
  state.currentInputs[feature] = numVal;
  
  const disp = document.getElementById(`val-${feature}`);
  if (disp) {
    if (feature === 'Medu') {
      disp.textContent = MEDU_NAMES[Math.min(parseInt(value), 4)];
    } else {
      disp.textContent = `${value}${METADATA[feature]?.suffix || ''}`;
    }
  }

  clearTimeout(state.debounceTimer);
  state.debounceTimer = setTimeout(() => {
    runPrediction();
  }, 180);
}

async function runPrediction() {
  try {
    const res = await fetch('/api/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(state.currentInputs)
    });
    
    if (!res.ok) throw new Error('Prediction API failed');
    const data = await res.json();
    state.lastPrediction = data;
    renderPredictionResults(data);
  } catch (err) {
    console.error('Error running prediction:', err);
  }
}

function renderPredictionResults(data) {
  const { predicted_class, confidence, risk_score, probabilities, contributions, recommendations, raw_inputs } = data;

  const riskBadge = document.getElementById('rail-risk-badge');
  const riskPct = document.getElementById('rail-risk-pct');
  const riskRing = document.getElementById('ring-risk');

  if (riskBadge && riskPct && riskRing) {
    riskBadge.textContent = `${predicted_class} Risk`;
    riskBadge.className = `rail-risk-badge ${predicted_class}`;
    riskPct.textContent = `${Math.round(risk_score)}%`;

    const circumference = 301.6;
    const offset = circumference - (risk_score / 100) * circumference;
    riskRing.style.strokeDashoffset = offset;

    if (predicted_class === 'High') {
      riskRing.style.stroke = '#EF4444';
    } else if (predicted_class === 'Medium') {
      riskRing.style.stroke = '#F59E0B';
    } else {
      riskRing.style.stroke = '#10B981';
    }
  }

  const confPct = document.getElementById('rail-conf-pct');
  const confRing = document.getElementById('ring-conf');
  if (confPct && confRing) {
    confPct.textContent = `${Math.round(confidence)}%`;
    const circumference = 301.6;
    const offset = circumference - (confidence / 100) * circumference;
    confRing.style.strokeDashoffset = offset;
  }

  const g1Val = document.getElementById('rail-g1-val');
  const g1Status = document.getElementById('rail-g1-status');
  const g1Ring = document.getElementById('ring-g1');
  if (g1Val && g1Status && g1Ring) {
    const g1Score = raw_inputs.G1;
    g1Val.textContent = `${Math.round(g1Score)}/20`;
    
    const pct = Math.round((g1Score / 20) * 100);
    if (g1Score <= 9) {
      g1Status.textContent = `At Risk (${pct}%)`;
      g1Status.style.color = '#EF4444';
      g1Ring.style.stroke = '#EF4444';
    } else if (g1Score <= 13) {
      g1Status.textContent = `Passing (${pct}%)`;
      g1Status.style.color = '#F59E0B';
      g1Ring.style.stroke = '#F59E0B';
    } else {
      g1Status.textContent = `Strong (${pct}%)`;
      g1Status.style.color = '#10B981';
      g1Ring.style.stroke = '#10B981';
    }
    
    const circumference = 301.6;
    const offset = circumference - (g1Score / 20) * circumference;
    g1Ring.style.strokeDashoffset = offset;
  }

  const dashRecsWrap = document.getElementById('dashboard-recs-preview');
  if (dashRecsWrap) {
    dashRecsWrap.innerHTML = '';
    if (!recommendations || recommendations.length === 0) {
      dashRecsWrap.innerHTML = '<p class="empty-state">No immediate intervention required. Student performance is stable.</p>';
    } else {
      recommendations.slice(0, 2).forEach(r => {
        const item = document.createElement('div');
        item.className = 'rec-preview-item';
        item.innerHTML = `
          <div class="rec-preview-meta">
            <span class="rec-preview-title">${r.action}</span>
            <span class="rec-preview-sub">${r.category} | ${r.timeline || 'Immediate'}</span>
          </div>
          <span class="rec-badge-pill ${r.urgency}">${r.urgency}</span>
        `;
        dashRecsWrap.appendChild(item);
      });
    }
  }

  const fullRecsWrap = document.getElementById('full-recommendations-container');
  const heroRecLabel = document.getElementById('rec-hero-risk-label');
  if (heroRecLabel) {
    heroRecLabel.textContent = `${predicted_class} Academic Risk (${confidence}% Certainty)`;
  }

  if (fullRecsWrap) {
    fullRecsWrap.innerHTML = '';
    if (!recommendations || recommendations.length === 0) {
      fullRecsWrap.innerHTML = '<div class="soft-card"><p>No active intervention required. Student profile is in the Low-Risk category.</p></div>';
    } else {
      recommendations.forEach((r, idx) => {
        const card = document.createElement('div');
        card.className = 'full-plan-card';

        let stepsHtml = '';
        if (r.steps && r.steps.length > 0) {
          stepsHtml = `
            <ul class="plan-steps-checklist">
              ${r.steps.map((s, sIdx) => `
                <li class="checklist-step" onclick="toggleStepCheckbox(this)">
                  <span class="step-box" id="step-box-${idx}-${sIdx}"></span>
                  <span>${s}</span>
                </li>
              `).join('')}
            </ul>
          `;
        }

        card.innerHTML = `
          <div class="plan-card-header">
            <span class="plan-pillar-tag">${r.category}</span>
            <div class="plan-badges-wrap">
              <span class="rec-badge-pill ${r.urgency}">${r.urgency} Priority</span>
              ${r.timeline ? `<span class="plan-timeline">${r.timeline}</span>` : ''}
            </div>
          </div>
          <div class="plan-title-main">${r.action}</div>
          <div class="plan-desc-text">${r.detail}</div>
          ${stepsHtml}
        `;
        fullRecsWrap.appendChild(card);
      });
    }
  }

  const driversWrap = document.getElementById('dash-risk-drivers');
  const protWrap = document.getElementById('dash-protective-factors');

  if (driversWrap && protWrap) {
    driversWrap.innerHTML = '';
    protWrap.innerHTML = '';

    const drivers = contributions.risk_drivers || [];
    const protective = contributions.protective_factors || [];

    if (drivers.length === 0) {
      driversWrap.innerHTML = '<span class="factor-none">No acute risk factors detected</span>';
    } else {
      drivers.forEach(d => {
        const pill = document.createElement('div');
        pill.className = 'factor-pill red';
        pill.innerHTML = `
          <span class="factor-name">${d.name}</span>
          <span class="factor-desc">${d.description}</span>
          <span class="factor-weight">+${d.weight}%</span>
        `;
        driversWrap.appendChild(pill);
      });
    }

    if (protective.length === 0) {
      protWrap.innerHTML = '<span class="factor-none">No significant protective buffers</span>';
    } else {
      protective.forEach(p => {
        const pill = document.createElement('div');
        pill.className = 'factor-pill green';
        pill.innerHTML = `
          <span class="factor-name">${p.name}</span>
          <span class="factor-desc">${p.description}</span>
          <span class="factor-weight">-${p.weight}%</span>
        `;
        protWrap.appendChild(pill);
      });
    }
  }
}

function toggleStepCheckbox(el) {
  el.classList.toggle('completed');
  const box = el.querySelector('.step-box');
  if (box) {
    box.textContent = el.classList.contains('completed') ? 'Done' : '';
  }
}

const PERSONAS = {
  high_risk: {
    G1: 6, failures: 2, absences: 18, age: 18,
    health: 2, freetime: 4, Walc: 4, goout: 4,
    Medu: 1, famrel: 2, label: 'High Risk Profile'
  },
  borderline: {
    G1: 10, failures: 1, absences: 8, age: 17,
    health: 3, freetime: 3, Walc: 2, goout: 3,
    Medu: 2, famrel: 3, label: 'Moderate Risk Profile'
  },
  thriving: {
    G1: 16, failures: 0, absences: 1, age: 16,
    health: 5, freetime: 2, Walc: 1, goout: 2,
    Medu: 4, famrel: 5, label: 'Low Risk Profile'
  },
  social_drift: {
    G1: 11, failures: 0, absences: 14, age: 17,
    health: 4, freetime: 5, Walc: 4, goout: 5,
    Medu: 3, famrel: 4, label: 'Attendance Slippage'
  }
};

function loadPersona(key) {
  const profile = PERSONAS[key];
  if (!profile) return;

  // Highlight active chip
  document.querySelectorAll('.arch-chip').forEach(c => c.classList.remove('active'));
  const chipBtn = document.querySelector(`.arch-chip[onclick*="${key}"]`);
  if (chipBtn) chipBtn.classList.add('active');

  Object.entries(profile).forEach(([feat, val]) => {
    if (feat === 'label') return;
    const inputEl = document.getElementById(`inp-${feat}`);
    if (inputEl) {
      inputEl.value = val;
      updateInput(feat, val);
    }
  });

  // If search open, close it
  clearGlobalSearch();
}

async function handleGlobalSearch(query) {
  const dropdown = document.getElementById('search-dropdown-menu');
  const clearBtn = document.getElementById('search-clear-btn');
  if (!dropdown) return;

  const q = (query || '').toLowerCase().trim();
  if (clearBtn) clearBtn.style.display = q ? 'block' : 'none';

  dropdown.style.display = 'block';

  let html = '';

  // 1. Search Active Enrolled Students (Local Roster + API Fallback)
  let matchingStudents = [];
  if (state.roster.all && state.roster.all.length > 0) {
    matchingStudents = state.roster.all.filter(s => {
      if (!q) return true;
      return (
        s.id.toLowerCase().includes(q) ||
        s.name.toLowerCase().includes(q) ||
        s.predicted_class.toLowerCase().includes(q) ||
        (q === 'high' && s.predicted_class === 'High') ||
        (q === 'fail' && s.failures > 0) ||
        (q === 'absent' && s.absences >= 8)
      );
    }).slice(0, 6);
  }

  if (matchingStudents.length === 0 && q) {
    try {
      const res = await fetch(`/api/students?q=${encodeURIComponent(q)}&limit=6`);
      if (res.ok) {
        const data = await res.json();
        matchingStudents = data.students || [];
      }
    } catch (err) {
      console.error('Error fetching students:', err);
    }
  }

  if (matchingStudents.length > 0) {
    html += '<div class="search-category-title">Enrolled Students &amp; Profiles</div>';
    matchingStudents.forEach(s => {
      const idTag = s.id.replace('STU-', '').slice(0, 4);
      const displayName = (s.name && s.name !== s.id) ? `${s.name} <span style="font-size:11px; font-weight:normal; color:var(--text-muted);">(${s.id})</span>` : s.id;
      html += `
        <div class="search-dropdown-item" onclick="selectRosterStudent('${s.id}'); clearGlobalSearch();">
          <div class="search-item-left">
            <div class="search-item-icon" style="background:var(--purple-light); color:var(--purple-brand); font-weight:700; font-size:10px;">${idTag}</div>
            <div class="search-item-info">
              <span class="search-item-name">${displayName}</span>
              <span class="search-item-desc">G1: ${s.G1}/20 | Absences: ${s.absences}d | Failures: ${s.failures}</span>
            </div>
          </div>
          <span class="search-student-badge ${s.predicted_class}">${s.predicted_class} Risk</span>
        </div>
      `;
    });
  }

  // 2. Preset Personas
  const personas = [
    { key: 'high_risk', name: 'High Risk Preset', desc: 'G1: 6, Failures: 2, Absences: 18' },
    { key: 'borderline', name: 'Moderate Risk Preset', desc: 'G1: 10, Failures: 1, Absences: 8' },
    { key: 'thriving', name: 'Low Risk Preset', desc: 'G1: 16, Failures: 0, Absences: 1' },
    { key: 'social_drift', name: 'Attendance Slippage Preset', desc: 'G1: 11, Failures: 0, Absences: 14' }
  ];

  const filteredPersonas = personas.filter(p => !q || p.name.toLowerCase().includes(q) || p.desc.toLowerCase().includes(q));
  if (filteredPersonas.length > 0) {
    html += '<div class="search-category-title">Preset Personas</div>';
    filteredPersonas.forEach(p => {
      html += `
        <div class="search-dropdown-item" onclick="loadPersona('${p.key}'); switchToTab('dashboard'); clearGlobalSearch();">
          <div class="search-item-left">
            <div class="search-item-icon" style="background:var(--bg-card-alt);">&#9679;</div>
            <div class="search-item-info">
              <span class="search-item-name">${p.name}</span>
              <span class="search-item-desc">${p.desc}</span>
            </div>
          </div>
        </div>
      `;
    });
  }

  // 3. Navigation Shortcuts
  const navTabs = [
    { tab: 'dashboard', name: 'Dashboard & Risk Gauges', desc: 'Live student risk evaluation and feature sliders' },
    { tab: 'recommendations', name: 'Intervention Plan', desc: '4-Pillar prescriptive action plan and checklist' },
    { tab: 'whatif', name: 'What-If Scenario Simulator', desc: 'Model trajectory reduction from student improvements' },
    { tab: 'cohort', name: 'Cohort Batch Triage', desc: 'Upload CSV dataset and triage entire cohort' },
    { tab: 'history', name: 'Session History Log', desc: 'View and export logged student assessments' }
  ];

  const filteredTabs = navTabs.filter(t => !q || t.name.toLowerCase().includes(q) || t.desc.toLowerCase().includes(q));
  if (filteredTabs.length > 0) {
    html += '<div class="search-category-title">Navigation Shortcuts</div>';
    filteredTabs.forEach(t => {
      html += `
        <div class="search-dropdown-item" onclick="switchToTab('${t.tab}'); clearGlobalSearch();">
          <div class="search-item-left">
            <div class="search-item-icon" style="background:var(--purple-light); color:var(--purple-brand);">&#8680;</div>
            <div class="search-item-info">
              <span class="search-item-name">${t.name}</span>
              <span class="search-item-desc">${t.desc}</span>
            </div>
          </div>
        </div>
      `;
    });
  }

  if (!html) {
    html = '<div style="padding:12px; font-size:12px; color:var(--text-muted); text-align:center;">No matching students or tabs found.</div>';
  }

  dropdown.innerHTML = html;
}

function handleGlobalSearchEnter() {
  const input = document.getElementById('global-search');
  if (!input) return;
  const q = input.value.toLowerCase().trim();
  if (!q) return;

  if (state.roster.all && state.roster.all.length > 0) {
    const match = state.roster.all.find(s =>
      s.id.toLowerCase().includes(q) ||
      s.name.toLowerCase().includes(q) ||
      s.predicted_class.toLowerCase() === q
    );
    if (match) {
      selectRosterStudent(match.id);
      clearGlobalSearch();
      switchToTab('dashboard');
    }
  }
}

window.handleGlobalSearchEnter = handleGlobalSearchEnter;
window.handleGlobalSearch = handleGlobalSearch;

async function initRoster() {
  try {
    // 1. Check if a cohort batch was previously loaded/uploaded
    const savedCohortRaw = localStorage.getItem('smartech_saved_cohort_batch');
    if (savedCohortRaw) {
      try {
        const savedCohort = JSON.parse(savedCohortRaw);
        if (savedCohort && savedCohort.data && savedCohort.data.length > 0) {
          displayBatchResults(savedCohort, false);
        }
      } catch (e) {
        console.warn('Failed parsing saved cohort:', e);
      }
    }

    // 2. If no cohort was loaded, fetch the default 649 enrolled database
    if (!state.roster.all || state.roster.all.length === 0) {
      const res = await fetch('/api/students?limit=649');
      if (res.ok) {
        const data = await res.json();
        state.roster.all = data.students || [];
        updateRosterFilterCounts();
        applyRosterFilters();
      }
    }

    // 3. Restore previously selected student if saved
    const savedStudentId = localStorage.getItem('smartech_saved_selected_student_id');
    if (savedStudentId) {
      await loadStudentProfile(savedStudentId);
    } else if (!state.lastPrediction) {
      await runPrediction();
    }
  } catch (err) {
    console.error('Error initializing student roster:', err);
  }
}

function updateRosterFilterCounts() {
  const total = state.roster.all.length;
  const high = state.roster.all.filter(s => s.predicted_class === 'High').length;
  const med = state.roster.all.filter(s => s.predicted_class === 'Medium').length;
  const low = state.roster.all.filter(s => s.predicted_class === 'Low').length;

  const totalEl = document.getElementById('roster-total-count');
  const allEl = document.getElementById('count-filter-all');
  const highEl = document.getElementById('count-filter-high');
  const medEl = document.getElementById('count-filter-med');
  const lowEl = document.getElementById('count-filter-low');

  if (totalEl) totalEl.textContent = `${total} Enrolled`;
  if (allEl) allEl.textContent = total;
  if (highEl) highEl.textContent = high;
  if (medEl) medEl.textContent = med;
  if (lowEl) lowEl.textContent = low;
}

function setRosterFilter(filterType) {
  state.roster.filter = filterType;
  state.roster.page = 1;

  document.querySelectorAll('.roster-filter-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.filter === filterType);
  });

  applyRosterFilters();
}

function handleRosterSearch(query) {
  state.roster.search = (query || '').toLowerCase().trim();
  state.roster.page = 1;
  applyRosterFilters();
}

function applyRosterFilters() {
  const f = state.roster.filter;
  const q = state.roster.search;

  state.roster.filtered = state.roster.all.filter(s => {
    const matchFilter = (f === 'all' || s.predicted_class === f);
    const matchSearch = (!q || s.id.toLowerCase().includes(q) || s.name.toLowerCase().includes(q));
    return matchFilter && matchSearch;
  });

  renderRosterGrid();
}

function renderRosterGrid() {
  const container = document.getElementById('roster-grid-container');
  const pageInfo = document.getElementById('roster-page-info');
  const prevBtn = document.getElementById('roster-prev-btn');
  const nextBtn = document.getElementById('roster-next-btn');

  if (!container) return;

  const total = state.roster.filtered.length;
  const pageSize = state.roster.pageSize;
  const totalPages = Math.ceil(total / pageSize) || 1;

  if (state.roster.page > totalPages) state.roster.page = totalPages;
  if (state.roster.page < 1) state.roster.page = 1;

  const page = state.roster.page;
  const start = (page - 1) * pageSize;
  const end = Math.min(start + pageSize, total);

  const studentsToShow = state.roster.filtered.slice(start, end);

  if (studentsToShow.length === 0) {
    container.innerHTML = `<div style="grid-column:1/-1; padding:20px; text-align:center; color:var(--text-muted); font-size:12.5px;">No students match the current filter or search criteria.</div>`;
  } else {
    container.innerHTML = studentsToShow.map(s => {
      const isSelected = state.roster.selectedId === s.id;
      const idTag = s.id.replace('STU-', '').slice(0, 4);
      const displayName = (s.name && s.name !== s.id) ? s.name : s.id;
      return `
        <div class="roster-student-card ${isSelected ? 'selected' : ''}" onclick="selectRosterStudent('${s.id}')">
          <div class="roster-card-top">
            <div class="roster-card-avatar-group">
              <div class="roster-card-avatar">${idTag}</div>
              <div class="roster-card-name-box">
                <span class="roster-card-name" title="${displayName}">${displayName}</span>
                <span class="roster-card-id">${s.id}</span>
              </div>
            </div>
            <span class="roster-card-pill ${s.predicted_class}">${s.predicted_class} Risk</span>
          </div>
          <div class="roster-card-stats">
            <span>G1: <strong>${s.G1}/20</strong></span>
            <span>Abs: <strong>${s.absences}d</strong></span>
            <span>Fail: <strong>${s.failures}</strong></span>
          </div>
        </div>
      `;
    }).join('');
  }

  if (pageInfo) {
    pageInfo.textContent = total === 0 ? 'Showing 0 of 0 students' : `Showing ${start + 1}-${end} of ${total} students (Page ${page}/${totalPages})`;
  }

  if (prevBtn) prevBtn.disabled = page <= 1;
  if (nextBtn) nextBtn.disabled = page >= totalPages;
}

function nextRosterPage() {
  const totalPages = Math.ceil(state.roster.filtered.length / state.roster.pageSize);
  if (state.roster.page < totalPages) {
    state.roster.page++;
    renderRosterGrid();
  }
}

function prevRosterPage() {
  if (state.roster.page > 1) {
    state.roster.page--;
    renderRosterGrid();
  }
}

async function pickRandomRosterStudent() {
  if (!state.roster.all || state.roster.all.length === 0) {
    await initRoster();
  }
  const pool = (state.roster.filtered && state.roster.filtered.length > 0) ? state.roster.filtered : state.roster.all;
  if (!pool || pool.length === 0) return;
  
  const randomIndex = Math.floor(Math.random() * pool.length);
  const student = pool[randomIndex];
  await selectRosterStudent(student.id);
}

async function selectRosterStudent(studentId) {
  state.roster.selectedId = studentId;
  try {
    localStorage.setItem('smartech_saved_selected_student_id', studentId);
  } catch (e) {}
  await loadStudentProfile(studentId);
  renderRosterGrid();
}

function clearSelectedStudent() {
  state.roster.selectedId = null;
  try {
    localStorage.removeItem('smartech_saved_selected_student_id');
  } catch (e) {}
  clearActiveStudent();
  const banner = document.getElementById('active-student-banner');
  if (banner) banner.style.display = 'none';
  renderRosterGrid();
  resetForm();
}

async function loadStudentProfile(studentId) {
  try {
    let student = state.roster.all.find(s => s.id === studentId);
    
    // Fetch full student record from API
    const res = await fetch(`/api/students/${studentId}`);
    if (res.ok) {
      student = await res.json();
    }
    
    if (!student || !student.inputs) {
      console.error('Student inputs not found for', studentId);
      return;
    }

    state.activeStudent = student;
    state.roster.selectedId = student.id;

    // 1. Immediately apply all 10 feature values to state.currentInputs
    state.currentInputs = { ...student.inputs };

    // 2. Immediately update all slider positions and display text badges
    Object.entries(student.inputs).forEach(([feat, val]) => {
      const numVal = parseFloat(val);
      const inputEl = document.getElementById(`inp-${feat}`);
      if (inputEl) {
        inputEl.value = numVal;
      }
      
      const disp = document.getElementById(`val-${feat}`);
      if (disp) {
        if (feat === 'Medu') {
          disp.textContent = MEDU_NAMES[Math.min(parseInt(numVal), 4)];
        } else {
          disp.textContent = `${numVal}${METADATA[feat]?.suffix || ''}`;
        }
      }
    });

    // 3. Update Top-Nav Active Student Pill
    const pill = document.getElementById('active-student-pill');
    const pillText = document.getElementById('active-student-text');
    const saveBtn = document.getElementById('btn-save-student');
    if (pill && pillText) {
      pillText.textContent = `Active: ${student.id}`;
      pill.style.display = 'flex';
    }
    if (saveBtn) saveBtn.style.display = 'block';

    // 4. Update Active Student Inspection Banner on Dashboard
    const banner = document.getElementById('active-student-banner');
    const bAvatar = document.getElementById('banner-avatar');
    const bName = document.getElementById('banner-student-name');
    const bId = document.getElementById('banner-student-id');
    const bRisk = document.getElementById('banner-risk-tag');
    const bMeta = document.getElementById('banner-student-meta');

    if (banner) {
      const idTag = student.id.replace('STU-', '').slice(0, 4);
      const displayName = (student.name && student.name !== student.id) ? student.name : `Student ${student.id}`;
      const pClass = (student.prediction && student.prediction.predicted_class) || student.predicted_class || 'Medium';
      const conf = (student.prediction && student.prediction.confidence) || student.confidence || 85;

      if (bAvatar) bAvatar.textContent = idTag;
      if (bName) bName.textContent = displayName;
      if (bId) bId.textContent = student.id;
      if (bRisk) {
        bRisk.textContent = `${pClass} Risk (${conf}% Certainty)`;
        bRisk.className = `status-pill ${pClass === 'High' ? 'red' : (pClass === 'Low' ? 'green' : '')}`;
      }
      if (bMeta) {
        bMeta.textContent = `School: ${student.school || 'GP'} · Age: ${student.inputs.age} · Baseline G1: ${student.inputs.G1}/20 · Absences: ${student.inputs.absences} days · Failures: ${student.inputs.failures}`;
      }
      banner.style.display = 'flex';
    }

    // 5. Run prediction immediately and update gauges, XAI, and recommendations
    if (student.prediction) {
      state.lastPrediction = student.prediction;
      renderPredictionResults(student.prediction);
    } else {
      await runPrediction();
    }

    // Clear preset chips active state
    document.querySelectorAll('.arch-chip').forEach(c => c.classList.remove('active'));

    clearGlobalSearch();
    renderRosterGrid();
  } catch (err) {
    console.error('Error loading student profile:', err);
  }
}

// Bind to window for guaranteed inline onclick execution
window.selectRosterStudent = selectRosterStudent;
window.pickRandomRosterStudent = pickRandomRosterStudent;
window.clearSelectedStudent = clearSelectedStudent;
window.setRosterFilter = setRosterFilter;
window.handleRosterSearch = handleRosterSearch;
window.nextRosterPage = nextRosterPage;
window.prevRosterPage = prevRosterPage;
window.loadStudentProfile = loadStudentProfile;

function clearActiveStudent() {
  state.activeStudent = null;
  const pill = document.getElementById('active-student-pill');
  const saveBtn = document.getElementById('btn-save-student');
  if (pill) pill.style.display = 'none';
  if (saveBtn) saveBtn.style.display = 'none';
}

async function saveActiveStudentUpdates() {
  if (!state.activeStudent) return;
  const studentId = state.activeStudent.id;
  const btn = document.getElementById('btn-save-student');

  try {
    const res = await fetch(`/api/students/${studentId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(state.currentInputs)
    });

    if (res.ok) {
      const data = await res.json();
      state.activeStudent = data.student;

      if (btn) {
        const orig = btn.innerHTML;
        btn.innerHTML = 'Saved to Registry!';
        btn.style.background = '#27AE60';
        btn.style.color = '#FFFFFF';
        setTimeout(() => {
          btn.innerHTML = orig;
          btn.style.background = '';
          btn.style.color = '';
        }, 1200);
      }
    }
  } catch (err) {
    console.error('Error saving student updates:', err);
  }
}

function clearGlobalSearch() {
  const input = document.getElementById('global-search');
  const dropdown = document.getElementById('search-dropdown-menu');
  const clearBtn = document.getElementById('search-clear-btn');
  if (input) input.value = '';
  if (dropdown) dropdown.style.display = 'none';
  if (clearBtn) clearBtn.style.display = 'none';
}

// Close search dropdown on outside click
document.addEventListener('click', (e) => {
  const searchContainer = document.querySelector('.search-container');
  if (searchContainer && !searchContainer.contains(e.target)) {
    const dropdown = document.getElementById('search-dropdown-menu');
    if (dropdown) dropdown.style.display = 'none';
  }
});

function resetForm() {
  loadPersona('borderline');
}

function syncWhatIfWithBaseline() {
  state.whatIfBaseline = { ...state.currentInputs };
  const baseScore = state.lastPrediction ? state.lastPrediction.risk_score : 50;
  const baseRisk = state.lastPrediction ? state.lastPrediction.predicted_class : 'Medium';

  const baseTag = document.getElementById('wi-base-tag');
  baseTag.textContent = `${baseRisk} Risk`;
  baseTag.className = `status-pill ${baseRisk === 'High' ? 'red' : (baseRisk === 'Low' ? 'green' : '')}`;

  document.getElementById('wi-base-score').textContent = baseScore.toFixed(1);

  const summaryWrap = document.getElementById('wi-base-summary');
  summaryWrap.innerHTML = `
    <div class="wi-detail-row"><span>G1 Score:</span><strong>${state.whatIfBaseline.G1}/20</strong></div>
    <div class="wi-detail-row"><span>Term Absences:</span><strong>${state.whatIfBaseline.absences} days</strong></div>
    <div class="wi-detail-row"><span>Past Failures:</span><strong>${state.whatIfBaseline.failures}</strong></div>
    <div class="wi-detail-row"><span>Weekend Alcohol:</span><strong>${state.whatIfBaseline.Walc}/5</strong></div>
    <div class="wi-detail-row"><span>Going Out:</span><strong>${state.whatIfBaseline.goout}/5</strong></div>
  `;

  const targetG1 = Math.min(20, state.whatIfBaseline.G1 + 3);
  const targetAbs = Math.max(0, Math.round(state.whatIfBaseline.absences * 0.4));
  const targetWalc = Math.max(1, state.whatIfBaseline.Walc - 1);
  const targetGoout = Math.max(1, state.whatIfBaseline.goout - 1);

  document.getElementById('wi-inp-G1').value = targetG1;
  document.getElementById('wi-val-G1').textContent = `${targetG1} / 20`;

  document.getElementById('wi-inp-absences').value = targetAbs;
  document.getElementById('wi-val-absences').textContent = `${targetAbs} days`;

  document.getElementById('wi-inp-Walc').value = targetWalc;
  document.getElementById('wi-val-Walc').textContent = `${targetWalc} / 5`;

  document.getElementById('wi-inp-goout').value = targetGoout;
  document.getElementById('wi-val-goout').textContent = `${targetGoout} / 5`;

  runWhatIfSimulation();
}

async function runWhatIfSimulation() {
  const targetG1 = parseFloat(document.getElementById('wi-inp-G1').value);
  const targetAbs = parseFloat(document.getElementById('wi-inp-absences').value);
  const targetWalc = parseFloat(document.getElementById('wi-inp-Walc').value);
  const targetGoout = parseFloat(document.getElementById('wi-inp-goout').value);

  document.getElementById('wi-val-G1').textContent = `${targetG1} / 20`;
  document.getElementById('wi-val-absences').textContent = `${targetAbs} days`;
  document.getElementById('wi-val-Walc').textContent = `${targetWalc} / 5`;
  document.getElementById('wi-val-goout').textContent = `${targetGoout} / 5`;

  const modifiedInputs = {
    ...state.whatIfBaseline,
    G1: targetG1,
    absences: targetAbs,
    Walc: targetWalc,
    goout: targetGoout
  };

  try {
    const res = await fetch('/api/what-if', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        baseline: state.whatIfBaseline,
        modified: modifiedInputs
      })
    });
    
    if (!res.ok) throw new Error('What-If API error');
    const data = await res.json();
    renderWhatIfOutcome(data);
  } catch (err) {
    console.error('What-If calculation failed:', err);
  }
}

function renderWhatIfOutcome(data) {
  const { baseline, modified, deltas } = data;

  const modTag = document.getElementById('wi-mod-tag');
  modTag.textContent = `${modified.predicted_class} Risk`;
  modTag.className = `status-pill ${modified.predicted_class === 'Low' ? 'green' : ''}`;

  document.getElementById('wi-shift-badge').textContent = `${baseline.predicted_class} Risk to ${modified.predicted_class} Risk`;

  const scoreDiffEl = document.getElementById('wi-risk-delta');
  scoreDiffEl.textContent = `${deltas.risk_score_diff > 0 ? '+' : ''}${deltas.risk_score_diff}`;
  scoreDiffEl.className = `wi-big-num ${deltas.risk_score_diff <= 0 ? 'green-txt' : 'red-txt'}`;

  const highPDiffEl = document.getElementById('wi-high-p-delta');
  highPDiffEl.textContent = `${deltas.high_p_diff > 0 ? '+' : ''}${deltas.high_p_diff}%`;
  highPDiffEl.className = `wi-big-num ${deltas.high_p_diff <= 0 ? 'green-txt' : 'red-txt'}`;

  const adviceBox = document.getElementById('wi-outcome-advice');
  if (deltas.improved) {
    adviceBox.innerHTML = `
      <p><strong>Advisor Summary:</strong> Under these simulated interventions, the student's risk profile drops by 
      <strong>${Math.abs(deltas.risk_score_diff)} points</strong>, reducing the probability of course failure from 
      <strong>${baseline.probabilities.High}%</strong> down to <strong>${modified.probabilities.High}%</strong>.</p>
    `;
    adviceBox.style.background = '#E8F8F0';
    adviceBox.style.borderColor = '#A7F3D0';
    adviceBox.style.color = '#0E6251';
  } else {
    adviceBox.innerHTML = `
      <p><strong>Advisor Summary:</strong> The proposed parameter changes elevate academic risk. Prioritize attendance retention and academic tutoring.</p>
    `;
    adviceBox.style.background = '#FEE8E8';
    adviceBox.style.borderColor = '#FCA5A5';
    adviceBox.style.color = '#991B1B';
  }
}

function setupDropzone() {
  const dropZone = document.getElementById('drop-zone');
  if (!dropZone) return;

  ['dragenter', 'dragover'].forEach(name => {
    dropZone.addEventListener(name, (e) => {
      e.preventDefault();
      dropZone.style.borderColor = '#6C5CE7';
      dropZone.style.background = '#F2EFF9';
    });
  });

  ['dragleave', 'drop'].forEach(name => {
    dropZone.addEventListener(name, (e) => {
      e.preventDefault();
      dropZone.style.borderColor = '#DCD5CC';
      dropZone.style.background = '#FAF8F5';
    });
  });

  dropZone.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) handleCSVUpload(files);
  });
}

async function loadSampleCohort() {
  try {
    const res = await fetch('/api/sample-cohort');
    if (!res.ok) throw new Error('Failed to load sample cohort');
    const data = await res.json();
    displayBatchResults(data);
  } catch (err) {
    console.error('Error loading sample cohort:', err);
  }
}

function handleCSVUpload(files) {
  if (!files || files.length === 0) return;
  const file = files[0];
  const reader = new FileReader();

  reader.onload = async (e) => {
    const text = e.target.result;
    try {
      const res = await fetch('/api/batch-csv', {
        method: 'POST',
        headers: { 'Content-Type': 'text/plain' },
        body: text
      });
      if (!res.ok) throw new Error('Batch processing failed');
      const data = await res.json();
      displayBatchResults(data);
    } catch (err) {
      console.error('Error in batch upload:', err);
    }
  };
  reader.readAsText(file);
}

function displayBatchResults(data, shouldPersist = true) {
  state.batchData = data.data || [];
  if (shouldPersist) {
    try {
      localStorage.setItem('smartech_saved_cohort_batch', JSON.stringify(data));
    } catch (e) {}
  }
  
  const kpis = document.getElementById('batch-kpis');
  const tableWrap = document.getElementById('batch-table-wrap');
  const exportBtn = document.getElementById('btn-export-batch');
  const resetBtn = document.getElementById('btn-reset-cohort');

  if (kpis) kpis.style.display = 'grid';
  if (tableWrap) tableWrap.style.display = 'block';
  if (exportBtn) exportBtn.removeAttribute('disabled');
  if (resetBtn) resetBtn.style.display = 'inline-flex';

  const kTotal = document.getElementById('kpi-total');
  const kHigh = document.getElementById('kpi-high');
  const kMed = document.getElementById('kpi-med');
  const kLow = document.getElementById('kpi-low');

  if (kTotal) kTotal.textContent = data.total_students;
  if (kHigh) kHigh.textContent = `${data.counts.High} (${data.percentages.High}%)`;
  if (kMed) kMed.textContent = `${data.counts.Medium} (${data.percentages.Medium}%)`;
  if (kLow) kLow.textContent = `${data.counts.Low} (${data.percentages.Low}%)`;

  renderBatchTable(state.batchData);

  // Sync uploaded batch into the Dashboard Student Roster
  if (state.batchData.length > 0) {
    state.roster.all = state.batchData.map(r => {
      const existing = state.roster.all.find(s => s.id === r['Student ID']);
      const studentName = r['Name'] || (existing ? existing.name : `Student ${r['Student ID']}`);
      return {
        id: r['Student ID'],
        name: studentName,
        predicted_class: r['Predicted Risk'],
        confidence: parseFloat(r['Confidence']) || 85,
        risk_score: r['Risk Score'] || 50,
        G1: r['G1 Grade'],
        absences: r['Absences'],
        failures: r['Failures'],
        inputs: {
          G1: r['G1 Grade'],
          failures: r['Failures'],
          absences: r['Absences'],
          age: r['Age'] || 17,
          health: r['Health'] || 4,
          freetime: 3,
          Walc: 1,
          goout: 3,
          Medu: 2,
          famrel: 4
        }
      };
    });
    updateRosterFilterCounts();
    applyRosterFilters();
  }
}

async function resetToFullRoster() {
  try {
    localStorage.removeItem('smartech_saved_cohort_batch');
  } catch (e) {}
  state.batchData = [];
  const kpis = document.getElementById('batch-kpis');
  const tableWrap = document.getElementById('batch-table-wrap');
  const exportBtn = document.getElementById('btn-export-batch');
  const resetBtn = document.getElementById('btn-reset-cohort');

  if (kpis) kpis.style.display = 'none';
  if (tableWrap) tableWrap.style.display = 'none';
  if (exportBtn) exportBtn.setAttribute('disabled', 'true');
  if (resetBtn) resetBtn.style.display = 'none';

  state.roster.all = [];
  await initRoster();
}
window.resetToFullRoster = resetToFullRoster;

function renderBatchTable(rows) {
  const tbody = document.getElementById('batch-tbody');
  tbody.innerHTML = '';

  if (rows.length === 0) {
    tbody.innerHTML = '<tr><td colspan="9" class="empty-state">No matching students found in this filter view.</td></tr>';
    return;
  }

  rows.forEach(r => {
    const tr = document.createElement('tr');
    const nameSub = r['Name'] ? `<div style="font-size:11px; color:var(--text-muted); font-weight:normal;">${r['Name']}</div>` : '';
    tr.innerHTML = `
      <td><strong>${r['Student ID']}</strong>${nameSub}</td>
      <td><span class="risk-tag ${r['Predicted Risk']}">${r['Predicted Risk']}</span></td>
      <td>${r['Confidence']}</td>
      <td><strong>${r['Risk Score']}</strong></td>
      <td>${r['G1 Grade']}/20</td>
      <td>${r['Failures']}</td>
      <td>${r['Absences']}</td>
      <td>${r['Primary Concern']}</td>
      <td><span style="font-size:11.5px; color:#584B68;">${r['Urgent Action']}</span></td>
    `;
    tbody.appendChild(tr);
  });
}

function setTableFilter(risk, btn) {
  state.batchFilter = risk;
  document.querySelectorAll('.filter-chip').forEach(p => p.classList.remove('active'));
  btn.classList.add('active');
  filterTable();
}

function filterTable() {
  const query = (document.getElementById('table-search-input').value || '').toLowerCase();
  const filter = state.batchFilter;

  const filtered = state.batchData.filter(r => {
    const matchesRisk = filter === 'all' || r['Predicted Risk'] === filter;
    const matchesQuery = !query || 
      r['Student ID'].toLowerCase().includes(query) ||
      r['Primary Concern'].toLowerCase().includes(query) ||
      r['Urgent Action'].toLowerCase().includes(query);
    return matchesRisk && matchesQuery;
  });

  renderBatchTable(filtered);
}

function exportBatchCSV() {
  if (!state.batchData || state.batchData.length === 0) return;
  const headers = Object.keys(state.batchData[0]);
  const rows = state.batchData.map(r => headers.map(h => `"${r[h]}"`).join(','));
  const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows].join('\n');
  
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement('a');
  link.setAttribute('href', encodedUri);
  link.setAttribute('download', `cohort_triage_report_${new Date().toISOString().slice(0,10)}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

function loadFeatureImportance() {
  const wrap = document.getElementById('feature-importance-bars');
  if (!wrap) return;

  const features = [
    { name: 'First Period Grade (G1)', score: 0.4468 },
    { name: 'Past Class Failures', score: 0.1695 },
    { name: 'Term Absences', score: 0.1082 },
    { name: 'Student Age', score: 0.0573 },
    { name: 'Health Status', score: 0.0456 },
    { name: 'Free Time After School', score: 0.0441 },
    { name: 'Weekend Alcohol Consumption', score: 0.0384 },
    { name: 'Going Out with Friends', score: 0.0352 },
    { name: "Mother's Education (Medu)", score: 0.0306 },
    { name: 'Family Relationship Quality', score: 0.0243 }
  ];

  wrap.innerHTML = '';
  features.forEach(f => {
    const pct = (f.score * 100).toFixed(1);
    const row = document.createElement('div');
    row.className = 'fb-row';
    row.innerHTML = `
      <div class="fb-meta">
        <span>${f.name}</span>
        <span>${(f.score).toFixed(4)} (${pct}%)</span>
      </div>
      <div class="fb-track">
        <div class="fb-fill" style="width: ${pct * 2.1}%"></div>
      </div>
    `;
    wrap.appendChild(row);
  });
}

function logToHistory() {
  if (!state.lastPrediction) return;

  const pred = state.lastPrediction;
  const actionText = pred.recommendations && pred.recommendations.length > 0 
    ? pred.recommendations[0].action 
    : 'Monitor Academic Standing';

  const entry = {
    id: `LOG-${Date.now().toString().slice(-4)}`,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    risk: pred.predicted_class,
    confidence: `${pred.confidence}%`,
    G1: pred.raw_inputs.G1,
    failures: pred.raw_inputs.failures,
    absences: pred.raw_inputs.absences,
    health: pred.raw_inputs.health,
    driver: pred.contributions.risk_drivers[0]?.name || 'Normal',
    action: actionText
  };

  state.history.unshift(entry);
  if (state.history.length > 50) state.history.pop();

  localStorage.setItem('student_risk_history_v3', JSON.stringify(state.history));
  updateHistoryCount();
  renderHistoryTable();

  const btn = event.currentTarget;
  const orig = btn.innerHTML;
  btn.innerHTML = 'Profile Logged';
  btn.style.background = '#27AE60';
  setTimeout(() => {
    btn.innerHTML = orig;
    btn.style.background = '';
  }, 1100);
}

function updateHistoryCount() {
  const el = document.getElementById('history-count');
  if (el) el.textContent = state.history.length;
}

function renderHistoryTable() {
  const tbody = document.getElementById('history-tbody');
  if (!tbody) return;

  if (state.history.length === 0) {
    tbody.innerHTML = '<tr><td colspan="10" class="empty-state">No assessments logged yet. Use the Dashboard tab and click "Log to Session History".</td></tr>';
    return;
  }

  tbody.innerHTML = '';
  state.history.forEach((h, i) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${i + 1}</td>
      <td><span style="font-family:var(--font-mono); font-size:11.5px;">${h.timestamp}</span></td>
      <td><span class="risk-tag ${h.risk}">${h.risk}</span></td>
      <td>${h.confidence}</td>
      <td>${h.G1}/20</td>
      <td>${h.failures}</td>
      <td>${h.absences}</td>
      <td>${h.health}/5</td>
      <td>${h.driver}</td>
      <td><span style="font-size:11.5px; color:#584B68;">${h.action}</span></td>
    `;
    tbody.appendChild(tr);
  });
}

function clearHistory() {
  if (confirm('Clear all session history records?')) {
    state.history = [];
    localStorage.removeItem('student_risk_history_v3');
    updateHistoryCount();
    renderHistoryTable();
  }
}

function exportHistoryCSV() {
  if (state.history.length === 0) {
    alert('No assessment history to export.');
    return;
  }

  const headers = ['id', 'timestamp', 'risk', 'confidence', 'G1', 'failures', 'absences', 'health', 'driver', 'action'];
  const rows = state.history.map(r => headers.map(h => `"${r[h]}"`).join(','));
  const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows].join('\n');
  
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement('a');
  link.setAttribute('href', encodedUri);
  link.setAttribute('download', `session_history_${new Date().toISOString().slice(0,10)}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
