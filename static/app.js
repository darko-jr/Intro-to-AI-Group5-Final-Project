/**
 * Smartech Student Risk Early-Warning Dashboard — Client Logic
 */

// Global State
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
  batchData: [],
  batchFilter: 'all',
  history: JSON.parse(localStorage.getItem('student_risk_history_v3') || '[]'),
  debounceTimer: null
};

// Feature Metadata for labels
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

// Initialize on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  setupSidebarNavigation();
  setupDropzone();
  updateHistoryCount();
  renderHistoryTable();
  runPrediction(); // Initial prediction
  loadFeatureImportance();
});

/* ==========================================================================
   Sidebar Navigation
   ========================================================================== */
function setupSidebarNavigation() {
  document.querySelectorAll('.nav-item').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTab = btn.dataset.tab;
      switchToTab(targetTab);
    });
  });
}

function switchToTab(tabName) {
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

/* ==========================================================================
   Single Student Prediction
   ========================================================================== */
function updateInput(feature, value) {
  const numVal = parseFloat(value);
  state.currentInputs[feature] = numVal;
  
  // Update value pill display
  const disp = document.getElementById(`val-${feature}`);
  if (disp) {
    if (feature === 'Medu') {
      disp.textContent = MEDU_NAMES[Math.min(parseInt(value), 4)];
    } else {
      disp.textContent = `${value}${METADATA[feature]?.suffix || ''}`;
    }
  }

  // Debounced real-time prediction
  clearTimeout(state.debounceTimer);
  state.debounceTimer = setTimeout(() => {
    runPrediction();
  }, 100);
}

async function runPrediction() {
  try {
    const res = await fetch('/api/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(state.currentInputs)
    });
    
    if (!res.ok) throw new Error('Prediction API error');
    const data = await res.json();
    state.lastPrediction = data;
    renderPredictionResult(data);
  } catch (err) {
    console.error('Prediction request failed:', err);
  }
}

function renderPredictionResult(data) {
  const { predicted_class, confidence, risk_score, probabilities, contributions, recommendations } = data;
  const circumference = 301.6; // 2 * PI * 48

  // 1. Right Rail Metric Rings
  // Ring 1: Academic Risk Score
  const ringRisk = document.getElementById('ring-risk');
  const railRiskPct = document.getElementById('rail-risk-pct');
  const railRiskBadge = document.getElementById('rail-risk-badge');
  
  if (ringRisk && railRiskPct) {
    railRiskPct.textContent = `${Math.round(risk_score)}%`;
    const offsetRisk = circumference - (circumference * (risk_score / 100));
    ringRisk.style.strokeDashoffset = offsetRisk;

    if (predicted_class === 'High') {
      ringRisk.style.stroke = '#FF7675';
      railRiskBadge.textContent = 'High Academic Risk';
      railRiskBadge.style.background = 'rgba(224, 86, 86, 0.4)';
    } else if (predicted_class === 'Medium') {
      ringRisk.style.stroke = '#FDCB6E';
      railRiskBadge.textContent = 'Medium Risk (Borderline)';
      railRiskBadge.style.background = 'rgba(230, 138, 0, 0.4)';
    } else {
      ringRisk.style.stroke = '#55E6C1';
      railRiskBadge.textContent = 'Low Academic Risk';
      railRiskBadge.style.background = 'rgba(39, 174, 96, 0.4)';
    }
  }

  // Ring 2: Model Confidence
  const ringConf = document.getElementById('ring-conf');
  const railConfPct = document.getElementById('rail-conf-pct');
  if (ringConf && railConfPct) {
    railConfPct.textContent = `${Math.round(confidence)}%`;
    const offsetConf = circumference - (circumference * (confidence / 100));
    ringConf.style.strokeDashoffset = offsetConf;
  }

  // Ring 3: G1 Score Band
  const ringG1 = document.getElementById('ring-g1');
  const railG1Val = document.getElementById('rail-g1-val');
  const railG1Status = document.getElementById('rail-g1-status');
  const g1Val = state.currentInputs.G1;
  if (ringG1 && railG1Val) {
    railG1Val.textContent = `${Math.round(g1Val)}/20`;
    const g1Pct = (g1Val / 20) * 100;
    const offsetG1 = circumference - (circumference * (g1Pct / 100));
    ringG1.style.strokeDashoffset = offsetG1;
    
    if (g1Val <= 9) {
      railG1Status.textContent = `Critical (≤9) · ${Math.round(g1Pct)}%`;
      ringG1.style.stroke = '#FF7675';
    } else if (g1Val <= 14) {
      railG1Status.textContent = `Passing · ${Math.round(g1Pct)}%`;
      ringG1.style.stroke = '#FDCB6E';
    } else {
      railG1Status.textContent = `Honor Grade · ${Math.round(g1Pct)}%`;
      ringG1.style.stroke = '#55E6C1';
    }
  }

  // 2. Sidebar Badge & Recommendation Count
  const recBadge = document.getElementById('recs-count-badge');
  if (recBadge) {
    recBadge.textContent = recommendations ? recommendations.length : 0;
  }

  // 3. Dashboard Quick Recommendations Preview
  const dashRecsWrap = document.getElementById('dashboard-recs-preview');
  if (dashRecsWrap) {
    dashRecsWrap.innerHTML = '';
    if (!recommendations || recommendations.length === 0) {
      dashRecsWrap.innerHTML = '<div class="rec-preview-item"><span class="rec-preview-title">Student is on track. Continue standard monitoring.</span></div>';
    } else {
      recommendations.slice(0, 3).forEach(r => {
        const item = document.createElement('div');
        item.className = 'rec-preview-item';
        item.innerHTML = `
          <div class="rec-preview-meta">
            <span class="rec-preview-title">${r.action}</span>
            <span class="rec-preview-sub">${r.category} • ${r.timeline || 'Immediate'}</span>
          </div>
          <span class="rec-badge-pill ${r.urgency}">${r.urgency}</span>
        `;
        dashRecsWrap.appendChild(item);
      });
    }
  }

  // 4. Dedicated Recommendations Tab Full Plan
  const fullRecsWrap = document.getElementById('full-recommendations-container');
  const heroRecLabel = document.getElementById('rec-hero-risk-label');
  if (heroRecLabel) {
    heroRecLabel.textContent = `${predicted_class} Academic Risk (${confidence}% Conf)`;
  }

  if (fullRecsWrap) {
    fullRecsWrap.innerHTML = '';
    if (!recommendations || recommendations.length === 0) {
      fullRecsWrap.innerHTML = '<div class="soft-card"><p>No active intervention required. Student profile is in the Low-Risk band.</p></div>';
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
                  <span class="step-box" id="step-box-${idx}-${sIdx}">✓</span>
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
              ${r.timeline ? `<span class="plan-timeline">⏱ ${r.timeline}</span>` : ''}
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

  // 5. Dashboard XAI Factors
  const driversWrap = document.getElementById('dash-risk-drivers');
  const protWrap = document.getElementById('dash-protective-factors');

  if (driversWrap && protWrap) {
    driversWrap.innerHTML = '';
    protWrap.innerHTML = '';

    if (contributions.risk_drivers.length === 0) {
      driversWrap.innerHTML = '<div class="factor-bubble driver"><span class="factor-name">No severe risk flags</span></div>';
    } else {
      contributions.risk_drivers.forEach(d => {
        const item = document.createElement('div');
        item.className = 'factor-bubble driver';
        item.innerHTML = `
          <span class="factor-name">${d.description}</span>
          <span class="factor-impact">+${d.weight} impact</span>
        `;
        driversWrap.appendChild(item);
      });
    }

    if (contributions.protective_factors.length === 0) {
      protWrap.innerHTML = '<div class="factor-bubble protective"><span class="factor-name">No strong protective factors</span></div>';
    } else {
      contributions.protective_factors.forEach(p => {
        const item = document.createElement('div');
        item.className = 'factor-bubble protective';
        item.innerHTML = `
          <span class="factor-name">${p.description}</span>
          <span class="factor-impact">-${p.weight} protective</span>
        `;
        protWrap.appendChild(item);
      });
    }
  }
}

function toggleStepCheckbox(el) {
  const box = el.querySelector('.step-box');
  if (box) {
    box.classList.toggle('checked');
  }
}

/* ==========================================================================
   Persona Presets
   ========================================================================== */
const PERSONAS = {
  high_risk: {
    G1: 6, failures: 2, absences: 18, age: 18, health: 2,
    freetime: 4, Walc: 4, goout: 4, Medu: 1, famrel: 2
  },
  borderline: {
    G1: 10, failures: 1, absences: 8, age: 17, health: 3,
    freetime: 3, Walc: 2, goout: 3, Medu: 2, famrel: 3
  },
  thriving: {
    G1: 16, failures: 0, absences: 1, age: 16, health: 5,
    freetime: 2, Walc: 1, goout: 2, Medu: 4, famrel: 5
  },
  social_drift: {
    G1: 11, failures: 0, absences: 14, age: 17, health: 4,
    freetime: 5, Walc: 4, goout: 5, Medu: 3, famrel: 4
  }
};

let personaIndex = 0;
const personaKeys = ['high_risk', 'borderline', 'thriving', 'social_drift'];

function cyclePersona() {
  personaIndex = (personaIndex + 1) % personaKeys.length;
  loadPersona(personaKeys[personaIndex]);
}

function handleQuickSearch(query) {
  const q = query.toLowerCase().trim();
  if (q.includes('high') || q.includes('fail') || q.includes('risk')) {
    loadPersona('high_risk');
  } else if (q.includes('border') || q.includes('med')) {
    loadPersona('borderline');
  } else if (q.includes('thriv') || q.includes('good') || q.includes('low')) {
    loadPersona('thriving');
  } else if (q.includes('drift') || q.includes('social')) {
    loadPersona('social_drift');
  }
}

function loadPersona(key) {
  const vals = PERSONAS[key];
  if (!vals) return;
  
  for (const [feat, val] of Object.entries(vals)) {
    const input = document.getElementById(`inp-${feat}`);
    if (input) {
      input.value = val;
      updateInput(feat, val);
    }
  }
}

function resetForm() {
  const defaults = {
    G1: 11, failures: 0, absences: 4, age: 17, health: 4,
    freetime: 3, Walc: 1, goout: 3, Medu: 2, famrel: 4
  };
  for (const [feat, val] of Object.entries(defaults)) {
    const input = document.getElementById(`inp-${feat}`);
    if (input) {
      input.value = val;
      updateInput(feat, val);
    }
  }
}

/* ==========================================================================
   What-If Simulator (Tab 3)
   ========================================================================== */
function syncWhatIfWithBaseline() {
  state.whatIfBaseline = { ...state.currentInputs };
  
  document.getElementById('wi-base-tag').textContent = `${state.lastPrediction?.predicted_class || 'Assessing'} Risk`;
  document.getElementById('wi-base-score').textContent = state.lastPrediction?.risk_score || '0';

  const summaryWrap = document.getElementById('wi-base-summary');
  summaryWrap.innerHTML = `
    <div class="wi-detail-row"><span>First Period Grade (G1):</span><strong>${state.whatIfBaseline.G1}/20</strong></div>
    <div class="wi-detail-row"><span>Past Course Failures:</span><strong>${state.whatIfBaseline.failures}</strong></div>
    <div class="wi-detail-row"><span>Term Absences:</span><strong>${state.whatIfBaseline.absences} days</strong></div>
    <div class="wi-detail-row"><span>Weekend Alcohol:</span><strong>${state.whatIfBaseline.Walc}/5</strong></div>
    <div class="wi-detail-row"><span>Going Out:</span><strong>${state.whatIfBaseline.goout}/5</strong></div>
  `;

  // Target simulation defaults
  const targetG1 = Math.min(20, state.whatIfBaseline.G1 + 3);
  const targetAbs = Math.max(0, Math.floor(state.whatIfBaseline.absences * 0.3));
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

  document.getElementById('wi-shift-badge').textContent = deltas.category_shift;

  const scoreDiffEl = document.getElementById('wi-risk-delta');
  scoreDiffEl.textContent = `${deltas.risk_score_diff > 0 ? '+' : ''}${deltas.risk_score_diff}`;
  scoreDiffEl.className = `wi-big-num ${deltas.risk_score_diff <= 0 ? 'green-txt' : 'red-txt'}`;

  const highPDiffEl = document.getElementById('wi-high-p-delta');
  highPDiffEl.textContent = `${deltas.high_p_diff > 0 ? '+' : ''}${deltas.high_p_diff}%`;
  highPDiffEl.className = `wi-big-num ${deltas.high_p_diff <= 0 ? 'green-txt' : 'red-txt'}`;

  const adviceBox = document.getElementById('wi-outcome-advice');
  if (deltas.improved) {
    adviceBox.innerHTML = `
      <p><strong>Advisor Takeaway:</strong> Under these simulated interventions, the student's risk profile drops by 
      <strong>${Math.abs(deltas.risk_score_diff)} points</strong>, reducing the probability of course failure from 
      <strong>${baseline.probabilities.High}%</strong> down to <strong>${modified.probabilities.High}%</strong>.</p>
    `;
    adviceBox.style.background = '#E8F8F0';
    adviceBox.style.borderColor = '#A7F3D0';
    adviceBox.style.color = '#0E6251';
  } else {
    adviceBox.innerHTML = `
      <p><strong>Advisor Takeaway:</strong> The proposed parameter changes elevate academic risk. Target attendance retention and study support.</p>
    `;
    adviceBox.style.background = '#FEE8E8';
    adviceBox.style.borderColor = '#FCA5A5';
    adviceBox.style.color = '#991B1B';
  }
}

/* ==========================================================================
   Cohort Triage & Batch Upload (Tab 4)
   ========================================================================== */
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

function displayBatchResults(data) {
  state.batchData = data.data || [];
  
  document.getElementById('batch-kpis').style.display = 'grid';
  document.getElementById('batch-table-wrap').style.display = 'block';
  document.getElementById('btn-export-batch').removeAttribute('disabled');

  document.getElementById('kpi-total').textContent = data.total_students;
  document.getElementById('kpi-high').textContent = `${data.counts.High} (${data.percentages.High}%)`;
  document.getElementById('kpi-med').textContent = `${data.counts.Medium} (${data.percentages.Medium}%)`;
  document.getElementById('kpi-low').textContent = `${data.counts.Low} (${data.percentages.Low}%)`;

  renderBatchTable(state.batchData);
}

function renderBatchTable(rows) {
  const tbody = document.getElementById('batch-tbody');
  tbody.innerHTML = '';

  if (rows.length === 0) {
    tbody.innerHTML = '<tr><td colspan="9" class="empty-state">No matching students found in this filter view.</td></tr>';
    return;
  }

  rows.forEach(r => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${r['Student ID']}</strong></td>
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

/* ==========================================================================
   Model Analytics Feature Importance (Tab 5)
   ========================================================================== */
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

/* ==========================================================================
   Session History (Tab 6)
   ========================================================================== */
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

  // Button feedback
  const btn = event.currentTarget;
  const orig = btn.innerHTML;
  btn.innerHTML = '✓ Profile Logged';
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
