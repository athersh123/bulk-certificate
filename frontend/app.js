/**
 * BulkCert Studio — Frontend Application Engine
 * High-performance UI connected to FastAPI backend.
 */

(function () {
  'use strict';

  // =========================================================================
  // State Management
  // =========================================================================

  function resolveApiBaseUrl() {
    let saved = localStorage.getItem('bulkcert_api_base');
    if (saved && (saved.includes(':3000') || saved.includes(':8000'))) {
      localStorage.removeItem('bulkcert_api_base');
      saved = null;
    }
    if (saved) {
      return saved.replace(/\/+$/, '');
    }
    // If the web page is opened directly on port 8001:
    if (window.location.port === '8001') {
      return window.location.origin;
    }
    // Default to port 8001 where BulkCert backend runs:
    return 'http://127.0.0.1:8001';
  }

  const State = {
    // API Configuration - points to FastAPI backend on port 8001
    apiBaseUrl: resolveApiBaseUrl(),
    activeTab: 'generator',
    
    // Generator State
    recipients: [
      { name: 'Alice Smith', email: 'alice.smith@example.com' },
      { name: 'Bob Jones', email: 'bob.jones@example.com' },
      { name: 'Carol Danvers', email: 'carol.danvers@example.com' }
    ],
    selectedPreviewIndex: 0,
    isSubmitting: false,

    // Monitor State
    activeJobId: null,
    activeJob: null,
    jobCertificates: [],
    pollTimer: null,
    jobStartTime: null,
    elapsedTimer: null,

    // History State
    historyJobs: [],
    historySearchTerm: '',
    certFilterTerm: '',
  };

  // Sample Presets
  const Presets = {
    demo3: [
      { name: 'Alice Smith', email: 'alice.smith@example.com' },
      { name: 'Bob Jones', email: 'bob.jones@example.com' },
      { name: 'Carol Danvers', email: 'carol.danvers@example.com' }
    ],
    demo10: [
      { name: 'Alexander Wright', email: 'alex.wright@cloud.io' },
      { name: 'Sophia Chen', email: 'sophia.chen@techcorp.com' },
      { name: 'Marcus Aurelius', email: 'marcus@academy.edu' },
      { name: 'Elena Rostova', email: 'elena@cybersec.org' },
      { name: 'Liam Gallagher', email: 'liam.g@musiclab.net' },
      { name: 'Zoe Saldana', email: 'zoe@deepspace.org' },
      { name: 'David Miller', email: 'dmiller@enterprise.com' },
      { name: 'Fatima Al-Mansoor', email: 'fatima@uae-tech.ae' },
      { name: 'Hiroshi Tanaka', email: 'tanaka@robotics.jp' },
      { name: 'Olivia Bennett', email: 'olivia@designcraft.co' }
    ],
    faultDemo: [
      { name: 'Valid Recipient One', email: 'valid.one@example.com' },
      { name: 'Valid Recipient Two', email: 'valid.two@example.com' },
      { name: 'Valid Recipient Three', email: 'valid.three@example.com' }
    ]
  };

  // =========================================================================
  // DOM Elements
  // =========================================================================

  const DOM = {
    // Nav & Tabs
    tabBtnGenerator: document.getElementById('tabBtnGenerator'),
    tabBtnMonitor: document.getElementById('tabBtnMonitor'),
    tabBtnHistory: document.getElementById('tabBtnHistory'),
    paneGenerator: document.getElementById('paneGenerator'),
    paneMonitor: document.getElementById('paneMonitor'),
    paneHistory: document.getElementById('paneHistory'),
    activeJobIndicator: document.getElementById('activeJobIndicator'),

    // Health Pill
    healthPill: document.getElementById('healthPill'),
    healthDot: document.getElementById('healthDot'),
    healthLabel: document.getElementById('healthLabel'),
    healthPing: document.getElementById('healthPing'),

    // Settings Modal
    settingsBtn: document.getElementById('settingsBtn'),
    settingsModal: document.getElementById('settingsModal'),
    settingsModalCloseBtn: document.getElementById('settingsModalCloseBtn'),
    apiBaseUrlInput: document.getElementById('apiBaseUrlInput'),
    settingsSaveBtn: document.getElementById('settingsSaveBtn'),
    settingsResetBtn: document.getElementById('settingsResetBtn'),

    // Generator Form
    batchForm: document.getElementById('certificateBatchForm'),
    eventNameInput: document.getElementById('eventNameInput'),
    certificateTitleInput: document.getElementById('certificateTitleInput'),
    recipientCountBadge: document.getElementById('recipientCountBadge'),
    modeTableBtn: document.getElementById('modeTableBtn'),
    modeCsvBtn: document.getElementById('modeCsvBtn'),
    modeTableContainer: document.getElementById('modeTableContainer'),
    modeCsvContainer: document.getElementById('modeCsvContainer'),
    recipientsTableBody: document.getElementById('recipientsTableBody'),
    addRecipientRowBtn: document.getElementById('addRecipientRowBtn'),
    clearRecipientsBtn: document.getElementById('clearRecipientsBtn'),
    csvFileInput: document.getElementById('csvFileInput'),
    csvDropzone: document.getElementById('csvDropzone'),
    csvRawTextarea: document.getElementById('csvRawTextarea'),
    parseCsvBtn: document.getElementById('parseCsvBtn'),
    submitBatchBtn: document.getElementById('submitBatchBtn'),
    submitSpinner: document.getElementById('submitSpinner'),
    submitIcon: document.getElementById('submitIcon'),
    submitBtnText: document.getElementById('submitBtnText'),

    // Presets
    presetDropdownToggle: document.getElementById('presetDropdownToggle'),
    presetMenu: document.getElementById('presetMenu'),
    presetDemo3: document.getElementById('presetDemo3'),
    presetDemo10: document.getElementById('presetDemo10'),
    presetFault: document.getElementById('presetFault'),

    // Preview Card
    certPreviewTitle: document.getElementById('certPreviewTitle'),
    certPreviewName: document.getElementById('certPreviewName'),
    certPreviewEvent: document.getElementById('certPreviewEvent'),
    certPreviewDate: document.getElementById('certPreviewDate'),

    // Monitor HUD
    monitorEmptyState: document.getElementById('monitorEmptyState'),
    monitorActiveContainer: document.getElementById('monitorActiveContainer'),
    emptyStateCreateBtn: document.getElementById('emptyStateCreateBtn'),
    hudStatusBadge: document.getElementById('hudStatusBadge'),
    hudEventName: document.getElementById('hudEventName'),
    hudJobId: document.getElementById('hudJobId'),
    hudCopyJobIdBtn: document.getElementById('hudCopyJobIdBtn'),
    hudCreatedAt: document.getElementById('hudCreatedAt'),
    hudRefreshBtn: document.getElementById('hudRefreshBtn'),
    hudDownloadAllBtn: document.getElementById('hudDownloadAllBtn'),
    hudTotalCount: document.getElementById('hudTotalCount'),
    hudSuccessCount: document.getElementById('hudSuccessCount'),
    hudFailedCount: document.getElementById('hudFailedCount'),
    hudPendingCount: document.getElementById('hudPendingCount'),
    hudRadialFill: document.getElementById('hudRadialFill'),
    hudPercentText: document.getElementById('hudPercentText'),
    hudElapsedText: document.getElementById('hudElapsedText'),
    hudProgressBar: document.getElementById('hudProgressBar'),
    certFilterInput: document.getElementById('certFilterInput'),
    monitorCertTableBody: document.getElementById('monitorCertTableBody'),

    // History Pane
    historyTableBody: document.getElementById('historyTableBody'),
    historySearchInput: document.getElementById('historySearchInput'),
    historyRefreshBtn: document.getElementById('historyRefreshBtn'),

    // PDF Preview Modal
    pdfPreviewModal: document.getElementById('pdfPreviewModal'),
    pdfModalCloseBtn: document.getElementById('pdfModalCloseBtn'),
    pdfModalTitle: document.getElementById('pdfModalTitle'),
    pdfModalCertId: document.getElementById('pdfModalCertId'),
    pdfModalFrame: document.getElementById('pdfModalFrame'),
    pdfModalDownloadBtn: document.getElementById('pdfModalDownloadBtn'),

    // Toasts
    toastContainer: document.getElementById('toastContainer'),
  };

  // =========================================================================
  // API Utilities
  // =========================================================================

  function getApiUrl(endpoint) {
    const base = State.apiBaseUrl.replace(/\/+$/, '');
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : '/' + endpoint;
    return `${base}${cleanEndpoint}`;
  }

  async function apiFetch(endpoint, options = {}) {
    const url = getApiUrl(endpoint);
    try {
      const response = await fetch(url, {
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          ...(options.headers || {})
        },
        ...options
      });

      if (!response.ok) {
        let errorData = null;
        try {
          errorData = await response.json();
        } catch (_) {
          errorData = { message: response.statusText };
        }
        const err = new Error(errorData.detail?.message || errorData.detail || errorData.message || `Request failed with ${response.status}`);
        err.status = response.status;
        err.data = errorData;
        throw err;
      }

      return await response.json();
    } catch (err) {
      console.error(`API Error on [${options.method || 'GET'} ${url}]:`, err);
      throw err;
    }
  }

  // =========================================================================
  // Health Polling
  // =========================================================================

  async function checkHealth() {
    const start = performance.now();
    try {
      let res;
      try {
        res = await apiFetch('/api/v1/health');
      } catch (err) {
        if (!State.apiBaseUrl.includes(':8001')) {
          State.apiBaseUrl = 'http://127.0.0.1:8001';
          localStorage.setItem('bulkcert_api_base', State.apiBaseUrl);
          res = await apiFetch('/api/v1/health');
        } else {
          throw err;
        }
      }

      const ping = Math.round(performance.now() - start);
      DOM.healthDot.className = 'status-dot dot-healthy';
      DOM.healthLabel.textContent = 'API Online';
      DOM.healthPing.textContent = `${ping}ms`;
      DOM.healthPill.title = `Backend Healthy: ${res.app_name || 'FastAPI'} (${res.environment || 'development'})`;
    } catch (err) {
      DOM.healthDot.className = 'status-dot dot-unhealthy';
      DOM.healthLabel.textContent = 'API Offline';
      DOM.healthPing.textContent = 'err';
      DOM.healthPill.title = `Cannot connect to API at: ${State.apiBaseUrl}. Click Settings to configure.`;
    }
  }

  // =========================================================================
  // Toast Notifications
  // =========================================================================

  function showToast(title, message, type = 'info', duration = 4000) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let iconClass = 'fa-circle-info';
    if (type === 'success') iconClass = 'fa-circle-check';
    if (type === 'error') iconClass = 'fa-triangle-exclamation';

    toast.innerHTML = `
      <i class="fa-solid ${iconClass} toast-icon"></i>
      <div class="toast-content">
        <div class="toast-title">${escapeHtml(title)}</div>
        <div class="toast-msg">${escapeHtml(message)}</div>
      </div>
    `;

    DOM.toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.classList.add('toast-leave');
      setTimeout(() => toast.remove(), 250);
    }, duration);
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  // =========================================================================
  // Tab Navigation
  // =========================================================================

  function switchTab(tabName) {
    State.activeTab = tabName;

    // Buttons
    [DOM.tabBtnGenerator, DOM.tabBtnMonitor, DOM.tabBtnHistory].forEach(btn => {
      const isTarget = btn.getAttribute('data-tab') === tabName;
      btn.classList.toggle('active', isTarget);
      btn.setAttribute('aria-selected', isTarget ? 'true' : 'false');
    });

    // Panes
    [DOM.paneGenerator, DOM.paneMonitor, DOM.paneHistory].forEach(pane => {
      const isTarget = pane.id === `pane${tabName.charAt(0).toUpperCase() + tabName.slice(1)}`;
      pane.classList.toggle('active', isTarget);
    });

    if (tabName === 'history') {
      fetchJobHistory();
    }
  }

  // =========================================================================
  // Recipients Management & Live Preview Sync
  // =========================================================================

  function renderRecipientsTable() {
    DOM.recipientsTableBody.innerHTML = '';

    State.recipients.forEach((recipient, idx) => {
      const tr = document.createElement('tr');
      if (idx === State.selectedPreviewIndex) {
        tr.classList.add('selected-preview');
      }

      const emailValid = isValidEmail(recipient.email);
      const nameValid = recipient.name.trim().length > 0;

      tr.innerHTML = `
        <td class="th-num">${idx + 1}</td>
        <td>
          <input 
            type="text" 
            class="table-input ${nameValid ? '' : 'input-invalid'}" 
            value="${escapeHtml(recipient.name)}" 
            placeholder="Full Name"
            data-index="${idx}"
            data-field="name"
          >
        </td>
        <td>
          <input 
            type="email" 
            class="table-input ${emailValid ? '' : 'input-invalid'}" 
            value="${escapeHtml(recipient.email)}" 
            placeholder="recipient@example.com"
            data-index="${idx}"
            data-field="email"
          >
        </td>
        <td class="th-actions">
          <button type="button" class="btn-row-del" data-index="${idx}" title="Delete recipient">
            <i class="fa-solid fa-xmark"></i>
          </button>
        </td>
      `;

      tr.addEventListener('click', (e) => {
        if (!e.target.closest('.btn-row-del')) {
          State.selectedPreviewIndex = idx;
          updatePreview();
          document.querySelectorAll('#recipientsTableBody tr').forEach((r, i) => {
            r.classList.toggle('selected-preview', i === idx);
          });
        }
      });

      DOM.recipientsTableBody.appendChild(tr);
    });

    DOM.recipientCountBadge.textContent = `${State.recipients.length} recipient${State.recipients.length === 1 ? '' : 's'}`;
    updatePreview();
  }

  function isValidEmail(email) {
    if (!email) return false;
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
  }

  function updatePreview() {
    const eventName = DOM.eventNameInput.value.trim() || 'Certificate Event';
    const certTitle = DOM.certificateTitleInput.value.trim() || 'Certificate of Completion';

    const selectedRecipient = State.recipients[State.selectedPreviewIndex] || State.recipients[0] || {
      name: 'Sample Recipient',
      email: 'sample@example.com'
    };

    DOM.certPreviewTitle.textContent = certTitle.toUpperCase();
    DOM.certPreviewEvent.textContent = eventName;
    DOM.certPreviewName.textContent = selectedRecipient.name || 'Recipient Name';

    // Format current date
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    DOM.certPreviewDate.textContent = new Date().toLocaleDateString('en-US', options);
  }

  function addRecipientRow(name = '', email = '') {
    State.recipients.push({ name, email });
    State.selectedPreviewIndex = State.recipients.length - 1;
    renderRecipientsTable();
  }

  function removeRecipientRow(index) {
    if (State.recipients.length <= 1) {
      showToast('Minimum Required', 'At least one recipient is required.', 'info');
      return;
    }
    State.recipients.splice(index, 1);
    if (State.selectedPreviewIndex >= State.recipients.length) {
      State.selectedPreviewIndex = State.recipients.length - 1;
    }
    renderRecipientsTable();
  }

  function loadPreset(key) {
    if (Presets[key]) {
      State.recipients = JSON.parse(JSON.stringify(Presets[key]));
      State.selectedPreviewIndex = 0;
      renderRecipientsTable();
      DOM.presetMenu.classList.remove('open');
      showToast('Preset Loaded', `Loaded ${State.recipients.length} recipients into batch`, 'success');
    }
  }

  // CSV Parsing
  function parseCsvContent(text) {
    if (!text || !text.trim()) {
      showToast('Empty Data', 'Please provide CSV content to parse', 'info');
      return;
    }

    const lines = text.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
    const parsed = [];

    lines.forEach(line => {
      // Split by comma or tab or semicolon
      let parts = line.split(/[,\t;]/).map(p => p.trim().replace(/^["']|["']$/g, ''));
      if (parts.length >= 2) {
        // If first column looks like email, swap
        let name = parts[0];
        let email = parts[1];
        if (isValidEmail(name) && !isValidEmail(email)) {
          [name, email] = [email, name];
        }
        if (name && email) {
          parsed.push({ name, email });
        }
      }
    });

    if (parsed.length === 0) {
      showToast('Parse Failed', 'Could not extract valid "Name, Email" rows.', 'error');
      return;
    }

    State.recipients = parsed;
    State.selectedPreviewIndex = 0;
    renderRecipientsTable();

    // Switch to table mode
    DOM.modeTableBtn.click();
    showToast('CSV Imported', `Successfully loaded ${parsed.length} recipients.`, 'success');
  }

  // =========================================================================
  // Batch Job Submission (POST /jobs)
  // =========================================================================

  async function handleBatchSubmit(e) {
    e.preventDefault();
    if (State.isSubmitting) return;

    const eventName = DOM.eventNameInput.value.trim();
    const certTitle = DOM.certificateTitleInput.value.trim();

    if (!eventName) {
      showToast('Validation Error', 'Event name is required.', 'error');
      DOM.eventNameInput.focus();
      return;
    }

    if (!certTitle) {
      showToast('Validation Error', 'Certificate title is required.', 'error');
      DOM.certificateTitleInput.focus();
      return;
    }

    // Validate recipients
    const validRecipients = [];
    const errors = [];

    State.recipients.forEach((rec, idx) => {
      const name = rec.name.trim();
      const email = rec.email.trim();
      if (!name) {
        errors.push(`Row ${idx + 1}: Name cannot be empty`);
      } else if (!isValidEmail(email)) {
        errors.push(`Row ${idx + 1}: Invalid email address "${email}"`);
      } else {
        validRecipients.push({ name, email });
      }
    });

    if (errors.length > 0) {
      showToast('Validation Failed', errors[0], 'error');
      renderRecipientsTable();
      return;
    }

    if (validRecipients.length === 0) {
      showToast('No Recipients', 'Please add at least one recipient.', 'error');
      return;
    }

    // Submit payload
    const payload = {
      event_name: eventName,
      certificate_title: certTitle,
      recipients: validRecipients
    };

    setSubmittingState(true);

    try {
      const res = await apiFetch('/jobs', {
        method: 'POST',
        body: JSON.stringify(payload)
      });

      showToast('Batch Accepted', `Job ID: ${res.job_id.slice(0, 8)}... started processing`, 'success');

      // Switch to Live Monitor tab and start polling
      startMonitoringJob(res.job_id);
      switchTab('monitor');
    } catch (err) {
      showToast('Submission Error', err.message || 'Failed to submit batch job.', 'error');
    } finally {
      setSubmittingState(false);
    }
  }

  function setSubmittingState(loading) {
    State.isSubmitting = loading;
    DOM.submitBatchBtn.disabled = loading;
    DOM.submitSpinner.style.display = loading ? 'inline-block' : 'none';
    DOM.submitIcon.style.display = loading ? 'none' : 'inline-block';
    DOM.submitBtnText.textContent = loading ? 'Queuing Batch...' : 'Dispatch Batch Job';
  }

  // =========================================================================
  // Live Monitor HUD & Polling Engine
  // =========================================================================

  function startMonitoringJob(jobId) {
    if (State.pollTimer) {
      clearInterval(State.pollTimer);
      State.pollTimer = null;
    }
    if (State.elapsedTimer) {
      clearInterval(State.elapsedTimer);
      State.elapsedTimer = null;
    }

    State.activeJobId = jobId;
    State.jobStartTime = Date.now();
    DOM.activeJobIndicator.style.display = 'inline-block';

    DOM.monitorEmptyState.style.display = 'none';
    DOM.monitorActiveContainer.style.display = 'block';

    // Timer for elapsed seconds
    DOM.hudElapsedText.textContent = 'Elapsed: 0.0s';
    State.elapsedTimer = setInterval(() => {
      const elapsed = ((Date.now() - State.jobStartTime) / 1000).toFixed(1);
      DOM.hudElapsedText.textContent = `Elapsed: ${elapsed}s`;
    }, 100);

    // Initial poll immediate
    pollJobStatus();

    // Regular interval
    State.pollTimer = setInterval(pollJobStatus, 600);
  }

  async function pollJobStatus() {
    if (!State.activeJobId) return;

    try {
      const [jobData, certsData] = await Promise.all([
        apiFetch(`/jobs/${State.activeJobId}`),
        apiFetch(`/jobs/${State.activeJobId}/certificates`).catch(() => [])
      ]);

      State.activeJob = jobData;
      State.jobCertificates = certsData;

      updateMonitorUI(jobData, certsData);

      // Stop condition
      const isFinished = ['COMPLETED', 'COMPLETED_WITH_ERRORS', 'FAILED'].includes(jobData.status);
      if (isFinished) {
        clearInterval(State.pollTimer);
        State.pollTimer = null;
        clearInterval(State.elapsedTimer);
        State.elapsedTimer = null;

        DOM.activeJobIndicator.style.display = 'none';

        if (jobData.status === 'COMPLETED') {
          showToast('Batch Finished', `All ${jobData.successful} certificates rendered successfully!`, 'success');
        } else if (jobData.status === 'COMPLETED_WITH_ERRORS') {
          showToast('Finished with Errors', `${jobData.successful} succeeded, ${jobData.failed} failed with fault isolation.`, 'info');
        } else {
          showToast('Batch Failed', 'Generation job failed.', 'error');
        }
      }
    } catch (err) {
      console.warn('Polling error:', err);
    }
  }

  function updateMonitorUI(job, certs) {
    DOM.hudEventName.textContent = job.event_name;
    DOM.hudJobId.textContent = job.job_id;
    DOM.hudCreatedAt.textContent = new Date(job.created_at).toLocaleTimeString();

    // Status Badge
    DOM.hudStatusBadge.textContent = job.status;
    DOM.hudStatusBadge.className = `hud-badge status-${job.status.toLowerCase()}`;

    // Metrics
    DOM.hudTotalCount.textContent = job.total;
    DOM.hudSuccessCount.textContent = job.successful;
    DOM.hudFailedCount.textContent = job.failed;
    DOM.hudPendingCount.textContent = job.pending;

    // Progress Bar & Radial
    const pct = job.progress || 0;
    DOM.hudPercentText.textContent = `${Math.round(pct)}%`;
    DOM.hudProgressBar.style.width = `${pct}%`;

    // Radial SVG dasharray
    DOM.hudRadialFill.setAttribute('stroke-dasharray', `${pct}, 100`);

    // Enable/Disable Download All
    DOM.hudDownloadAllBtn.disabled = job.successful === 0;

    // Render Certificate Items Table
    renderCertificatesTable(certs);
  }

  function renderCertificatesTable(certs) {
    const filterTerm = State.certFilterTerm.toLowerCase();
    const filtered = certs.filter(c => 
      c.recipient_name.toLowerCase().includes(filterTerm) ||
      c.recipient_email.toLowerCase().includes(filterTerm) ||
      c.id.toLowerCase().includes(filterTerm)
    );

    DOM.monitorCertTableBody.innerHTML = '';

    if (filtered.length === 0) {
      DOM.monitorCertTableBody.innerHTML = `
        <tr>
          <td colspan="5" style="text-align: center; color: var(--text-dim); padding: 2rem;">
            No certificate items found.
          </td>
        </tr>
      `;
      return;
    }

    filtered.forEach(cert => {
      const tr = document.createElement('tr');

      let statusBadge = '';
      if (cert.status === 'COMPLETED') {
        statusBadge = `<span class="status-pill status-completed"><i class="fa-solid fa-check"></i> Ready</span>`;
      } else if (cert.status === 'FAILED') {
        statusBadge = `<span class="status-pill status-failed" title="${escapeHtml(cert.error_message || 'Rendering error')}"><i class="fa-solid fa-xmark"></i> Failed</span>`;
      } else if (cert.status === 'PROCESSING') {
        statusBadge = `<span class="status-pill status-processing"><i class="fa-solid fa-spinner fa-spin"></i> Rendering</span>`;
      } else {
        statusBadge = `<span class="status-pill status-pending"><i class="fa-regular fa-clock"></i> Queued</span>`;
      }

      let actionsHtml = '';
      if (cert.status === 'COMPLETED') {
        const downloadUrl = getApiUrl(`/certificates/${cert.id}`);
        actionsHtml = `
          <div class="item-action-btns">
            <button type="button" class="btn-secondary btn-xs btn-preview-pdf" data-id="${cert.id}" data-name="${escapeHtml(cert.recipient_name)}">
              <i class="fa-solid fa-eye"></i> View PDF
            </button>
            <a href="${downloadUrl}" class="btn-primary btn-xs" download="Certificate_${escapeHtml(cert.recipient_name)}.pdf">
              <i class="fa-solid fa-download"></i> Download
            </a>
          </div>
        `;
      } else if (cert.status === 'FAILED') {
        actionsHtml = `
          <span class="text-danger text-xs" title="${escapeHtml(cert.error_message || '')}">
            <i class="fa-solid fa-circle-exclamation"></i> ${escapeHtml(cert.error_message ? cert.error_message.slice(0, 45) + '...' : 'Failed')}
          </span>
        `;
      } else {
        actionsHtml = `<span class="text-muted text-xs">Waiting for worker...</span>`;
      }

      tr.innerHTML = `
        <td><strong>${escapeHtml(cert.recipient_name)}</strong></td>
        <td><span class="code-font text-muted">${escapeHtml(cert.recipient_email)}</span></td>
        <td><span class="code-font text-xs text-dim">${cert.id.slice(0, 8)}...</span></td>
        <td>${statusBadge}</td>
        <td>${actionsHtml}</td>
      `;

      DOM.monitorCertTableBody.appendChild(tr);
    });

    // Attach PDF Preview handlers
    document.querySelectorAll('.btn-preview-pdf').forEach(btn => {
      btn.addEventListener('click', () => {
        const certId = btn.getAttribute('data-id');
        const recName = btn.getAttribute('data-name');
        openPdfPreviewModal(certId, recName);
      });
    });
  }

  // =========================================================================
  // PDF Preview Modal
  // =========================================================================

  function openPdfPreviewModal(certId, recipientName) {
    const url = getApiUrl(`/certificates/${certId}`);
    DOM.pdfModalTitle.textContent = `Certificate: ${recipientName}`;
    DOM.pdfModalCertId.textContent = `UUID: ${certId}`;
    DOM.pdfModalFrame.src = url;
    DOM.pdfModalDownloadBtn.href = url;
    DOM.pdfPreviewModal.classList.add('open');
  }

  function closePdfPreviewModal() {
    DOM.pdfPreviewModal.classList.remove('open');
    DOM.pdfModalFrame.src = 'about:blank';
  }

  // =========================================================================
  // Job History (GET /jobs)
  // =========================================================================

  async function fetchJobHistory() {
    try {
      const jobs = await apiFetch('/jobs?limit=50');
      State.historyJobs = jobs;
      renderHistoryTable();
    } catch (err) {
      console.warn('Could not fetch jobs history:', err);
    }
  }

  function renderHistoryTable() {
    const term = State.historySearchTerm.toLowerCase();
    const filtered = State.historyJobs.filter(j => 
      j.event_name.toLowerCase().includes(term) ||
      j.job_id.toLowerCase().includes(term) ||
      j.certificate_title.toLowerCase().includes(term)
    );

    DOM.historyTableBody.innerHTML = '';

    if (filtered.length === 0) {
      DOM.historyTableBody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align: center; color: var(--text-dim); padding: 2rem;">
            No historical generation jobs found.
          </td>
        </tr>
      `;
      return;
    }

    filtered.forEach(job => {
      const tr = document.createElement('tr');
      const dateStr = new Date(job.created_at).toLocaleString();

      tr.innerHTML = `
        <td>
          <strong>${escapeHtml(job.event_name)}</strong>
          <small class="card-subtitle">${escapeHtml(job.certificate_title)}</small>
        </td>
        <td><span class="code-font text-xs">${job.job_id.slice(0, 8)}...</span></td>
        <td><span class="status-pill status-${job.status.toLowerCase()}">${job.status}</span></td>
        <td>
          <span class="text-success">${job.successful}</span> / <strong>${job.total}</strong>
          ${job.failed > 0 ? `<span class="text-danger">(${job.failed} failed)</span>` : ''}
        </td>
        <td><strong>${job.progress}%</strong></td>
        <td><span class="text-dim text-xs">${dateStr}</span></td>
        <td>
          <button type="button" class="btn-secondary btn-xs btn-open-job" data-id="${job.job_id}">
            <i class="fa-solid fa-chart-line"></i> Inspect
          </button>
        </td>
      `;

      DOM.historyTableBody.appendChild(tr);
    });

    document.querySelectorAll('.btn-open-job').forEach(btn => {
      btn.addEventListener('click', () => {
        const jId = btn.getAttribute('data-id');
        startMonitoringJob(jId);
        switchTab('monitor');
      });
    });
  }

  // =========================================================================
  // Settings & Event Listeners
  // =========================================================================

  function initEventListeners() {
    // Nav Tabs
    DOM.tabBtnGenerator.addEventListener('click', () => switchTab('generator'));
    DOM.tabBtnMonitor.addEventListener('click', () => switchTab('monitor'));
    DOM.tabBtnHistory.addEventListener('click', () => switchTab('history'));
    DOM.emptyStateCreateBtn.addEventListener('click', () => switchTab('generator'));

    // Presets Dropdown
    DOM.presetDropdownToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      DOM.presetMenu.classList.toggle('open');
    });

    document.addEventListener('click', () => {
      DOM.presetMenu.classList.remove('open');
    });

    DOM.presetDemo3.addEventListener('click', () => loadPreset('demo3'));
    DOM.presetDemo10.addEventListener('click', () => loadPreset('demo10'));
    DOM.presetFault.addEventListener('click', () => loadPreset('faultDemo'));

    // Inputs Live Preview
    DOM.eventNameInput.addEventListener('input', updatePreview);
    DOM.certificateTitleInput.addEventListener('input', updatePreview);

    // Table Row Input Changes
    DOM.recipientsTableBody.addEventListener('input', (e) => {
      const target = e.target;
      if (target.classList.contains('table-input')) {
        const idx = parseInt(target.getAttribute('data-index'), 10);
        const field = target.getAttribute('data-field');
        if (State.recipients[idx]) {
          State.recipients[idx][field] = target.value;
          
          if (field === 'email') {
            target.classList.toggle('input-invalid', !isValidEmail(target.value));
          } else if (field === 'name') {
            target.classList.toggle('input-invalid', target.value.trim().length === 0);
          }
          updatePreview();
        }
      }
    });

    // Delete row
    DOM.recipientsTableBody.addEventListener('click', (e) => {
      const delBtn = e.target.closest('.btn-row-del');
      if (delBtn) {
        const idx = parseInt(delBtn.getAttribute('data-index'), 10);
        removeRecipientRow(idx);
      }
    });

    // Add row
    DOM.addRecipientRowBtn.addEventListener('click', () => {
      addRecipientRow('', '');
    });

    // Clear recipients
    DOM.clearRecipientsBtn.addEventListener('click', () => {
      State.recipients = [{ name: '', email: '' }];
      State.selectedPreviewIndex = 0;
      renderRecipientsTable();
    });

    // Input Mode Toggle
    DOM.modeTableBtn.addEventListener('click', () => {
      DOM.modeTableBtn.classList.add('active');
      DOM.modeCsvBtn.classList.remove('active');
      DOM.modeTableContainer.classList.add('active');
      DOM.modeCsvContainer.classList.remove('active');
    });

    DOM.modeCsvBtn.addEventListener('click', () => {
      DOM.modeCsvBtn.classList.add('active');
      DOM.modeTableBtn.classList.remove('active');
      DOM.modeCsvContainer.classList.add('active');
      DOM.modeTableContainer.classList.remove('active');
    });

    // CSV Parse
    DOM.parseCsvBtn.addEventListener('click', () => {
      parseCsvContent(DOM.csvRawTextarea.value);
    });

    // CSV Dropzone
    DOM.csvDropzone.addEventListener('click', () => DOM.csvFileInput.click());
    DOM.csvDropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      DOM.csvDropzone.classList.add('dragover');
    });
    DOM.csvDropzone.addEventListener('dragleave', () => {
      DOM.csvDropzone.classList.remove('dragover');
    });
    DOM.csvDropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      DOM.csvDropzone.classList.remove('dragover');
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        handleFileRead(e.dataTransfer.files[0]);
      }
    });
    DOM.csvFileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        handleFileRead(e.target.files[0]);
      }
    });

    function handleFileRead(file) {
      const reader = new FileReader();
      reader.onload = (evt) => {
        DOM.csvRawTextarea.value = evt.target.result;
        parseCsvContent(evt.target.result);
      };
      reader.readAsText(file);
    }

    // Submit Batch
    DOM.batchForm.addEventListener('submit', handleBatchSubmit);

    // Copy Job ID
    DOM.hudCopyJobIdBtn.addEventListener('click', () => {
      if (State.activeJobId) {
        navigator.clipboard.writeText(State.activeJobId).then(() => {
          showToast('Copied', 'Job ID copied to clipboard', 'info');
        });
      }
    });

    // Refresh Monitor
    DOM.hudRefreshBtn.addEventListener('click', () => {
      pollJobStatus();
      showToast('Refreshed', 'Polled latest job state', 'info');
    });

    // Filter Certs in Monitor
    DOM.certFilterInput.addEventListener('input', (e) => {
      State.certFilterTerm = e.target.value;
      renderCertificatesTable(State.jobCertificates);
    });

    // Download All Completed
    DOM.hudDownloadAllBtn.addEventListener('click', () => {
      const completed = State.jobCertificates.filter(c => c.status === 'COMPLETED');
      if (completed.length === 0) return;

      completed.forEach((c, index) => {
        setTimeout(() => {
          const a = document.createElement('a');
          a.href = getApiUrl(`/certificates/${c.id}`);
          a.download = `Certificate_${c.recipient_name.replace(/\s+/g, '_')}.pdf`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
        }, index * 250);
      });

      showToast('Downloading Batch', `Started download for ${completed.length} certificates`, 'success');
    });

    // PDF Modal Close
    DOM.pdfModalCloseBtn.addEventListener('click', closePdfPreviewModal);
    DOM.pdfPreviewModal.addEventListener('click', (e) => {
      if (e.target === DOM.pdfPreviewModal) closePdfPreviewModal();
    });

    // Settings Modal
    DOM.settingsBtn.addEventListener('click', () => {
      DOM.apiBaseUrlInput.value = State.apiBaseUrl;
      DOM.settingsModal.classList.add('open');
    });

    DOM.settingsModalCloseBtn.addEventListener('click', () => {
      DOM.settingsModal.classList.remove('open');
    });

    DOM.settingsModal.addEventListener('click', (e) => {
      if (e.target === DOM.settingsModal) DOM.settingsModal.classList.remove('open');
    });

    DOM.settingsSaveBtn.addEventListener('click', () => {
      const newUrl = DOM.apiBaseUrlInput.value.trim();
      State.apiBaseUrl = newUrl || window.location.origin;
      localStorage.setItem('bulkcert_api_base', State.apiBaseUrl);
      DOM.settingsModal.classList.remove('open');
      checkHealth();
      showToast('Settings Saved', `API endpoint set to: ${State.apiBaseUrl}`, 'success');
    });

    DOM.settingsResetBtn.addEventListener('click', () => {
      localStorage.removeItem('bulkcert_api_base');
      State.apiBaseUrl = resolveApiBaseUrl();
      DOM.apiBaseUrlInput.value = State.apiBaseUrl;
      checkHealth();
      showToast('Reset Default', `API endpoint reset to: ${State.apiBaseUrl}`, 'info');
    });

    // History controls
    DOM.historyRefreshBtn.addEventListener('click', fetchJobHistory);
    DOM.historySearchInput.addEventListener('input', (e) => {
      State.historySearchTerm = e.target.value;
      renderHistoryTable();
    });

    // Health pill click -> open settings
    DOM.healthPill.addEventListener('click', () => DOM.settingsBtn.click());
  }

  // =========================================================================
  // Initialize Application
  // =========================================================================

  function init() {
    renderRecipientsTable();
    updatePreview();
    initEventListeners();

    // Check health immediately and start health ticker
    checkHealth();
    setInterval(checkHealth, 10000);

    // Initial check for existing jobs
    fetchJobHistory().then(() => {
      if (State.historyJobs && State.historyJobs.length > 0) {
        // Pre-select most recent job in monitor if not running
        const recent = State.historyJobs[0];
        startMonitoringJob(recent.job_id);
      }
    });
  }

  // Bootstrapping
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
