/* ── STATE ────────────────────────────────────────────── */
let credentialsSet = false;
let serviceActive  = false;
let logEntries     = 0;
let logPollTimer   = null;
let statusPollTimer = null;
let lastLogIndex   = 0;

/* ── UTILITIES ────────────────────────────────────────── */
function ts() {
  const d = new Date();
  return [d.getHours(), d.getMinutes(), d.getSeconds()]
    .map(n => String(n).padStart(2, '0')).join(':');
}

function addLog(msg, level = 'info') {
  const body = document.getElementById('logBody');
  const row  = document.createElement('div');
  row.className = 'log-entry';
  row.innerHTML = `
    <span class="log-time">${ts()}</span>
    <span class="log-level ${level}">${level.toUpperCase()}</span>
    <span class="log-msg ${level}">${msg}</span>`;
  body.appendChild(row);
  body.scrollTop = body.scrollHeight;
  logEntries++;
  document.getElementById('logCount').textContent = `${logEntries} event${logEntries !== 1 ? 's' : ''}`;
  // keep max 40 entries in DOM
  while (body.children.length > 40) body.removeChild(body.firstChild);
}

/* ── STATUS BAR ───────────────────────────────────────── */
function setStatus(state, message) {
  const bar    = document.getElementById('statusBar');
  const text   = document.getElementById('statusText');
  const badge  = document.getElementById('statusBadge');
  bar.className = 'status-bar ' + state;
  text.innerHTML = message;
  const labels = { active: 'listening', error: 'error', warn: 'connecting…', '': 'inactive' };
  badge.textContent = labels[state] || 'inactive';
}

/* ── PIPELINE HIGHLIGHT ───────────────────────────────── */
function setPipeline(steps) {
  [1,2,3,4].forEach(i => {
    const el = document.getElementById('pipe' + i);
    el.classList.toggle('active', steps.includes(i));
  });
}

/* ── FIELD VALIDATION ─────────────────────────────────── */
function validEmail(v) { return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v); }
function validPass(v)  { return v.replace(/\s/g, '').length === 16; }

function showError(id, show) {
  document.getElementById(id).style.display = show ? 'block' : 'none';
}

function onInputChange() {
  showError('emailError', false);
  if (credentialsSet) {
    credentialsSet = false;
    document.getElementById('serviceToggle').disabled = true;
    document.getElementById('serviceDesc').textContent = 'Disabled — apply credentials first to unlock';
    if (serviceActive) {
      serviceActive = false;
      document.getElementById('serviceToggle').checked = false;
      setStatus('', 'Service <strong>offline</strong> — credentials changed, re-apply to continue');
      setPipeline([]);
      addLog('credentials changed — listener stopped', 'warn');
      stopPolling();
    }
  }
}

/* ── PASS FORMAT ──────────────────────────────────────── */
function formatPass(input) {
  let raw = input.value.replace(/\s/g, '').slice(0, 16);
  const chunks = [];
  for (let i = 0; i < raw.length; i += 4) chunks.push(raw.slice(i, i + 4));
  input.value = chunks.join(' ');
  onInputChange();
  showError('passError', false);
}

/* ── SHOW/HIDE PASS ───────────────────────────────────── */
function togglePass() {
  const inp = document.getElementById('passInput');
  const btn = document.getElementById('eyeBtn');
  if (inp.type === 'password') { inp.type = 'text';     btn.textContent = 'HIDE'; }
  else                         { inp.type = 'password'; btn.textContent = 'SHOW'; }
}

/* ── API HELPERS ──────────────────────────────────────── */
async function apiPost(url, body = {}) {
  try {
    const resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return await resp.json();
  } catch (err) {
    addLog(`API error: ${err.message}`, 'error');
    return { ok: false, message: err.message };
  }
}

async function apiGet(url) {
  try {
    const resp = await fetch(url);
    return await resp.json();
  } catch (err) {
    return null;
  }
}

/* ── APPLY CREDENTIALS (REAL API CALL) ────────────────── */
async function applyCredentials() {
  const email = document.getElementById('emailInput').value.trim();
  const pass  = document.getElementById('passInput').value.trim();
  let valid = true;

  if (!email || !validEmail(email)) { showError('emailError', true); valid = false; }
  if (!pass  || !validPass(pass))   { showError('passError',  true); valid = false; }
  if (!valid) return;

  addLog('Sending credentials to backend...', 'info');
  setStatus('warn', 'Applying credentials...');

  const result = await apiPost('/api/credentials', { email, password: pass });

  if (result.ok) {
    credentialsSet = true;
    document.getElementById('serviceToggle').disabled = false;
    document.getElementById('serviceDesc').textContent = 'Ready — toggle to start IMAP IDLE monitoring';
    setStatus('', 'Credentials <strong>applied</strong> — toggle the listener to start monitoring');
    addLog(`Credentials set for ${email}`, 'success');
    addLog('GMAIL_PASS_KEY loaded — IMAP connection ready', 'info');
    addLog('Toggle the IDLE monitor switch to begin', 'info');
    document.getElementById('applyBtn').innerHTML = '&#9654;&nbsp; update credentials';
  } else {
    setStatus('error', `Failed: <strong>${result.message}</strong>`);
    addLog(`Failed to set credentials: ${result.message}`, 'error');
  }
}

/* ── POLLING: LOGS + STATUS ───────────────────────────── */
function startPolling() {
  lastLogIndex = 0;

  // Poll logs every 1.5 seconds
  logPollTimer = setInterval(async () => {
    const data = await apiGet(`/api/logs?since=${lastLogIndex}`);
    if (data && data.logs) {
      data.logs.forEach(entry => {
        addLog(entry.message, entry.level);
      });
      lastLogIndex = data.total;
    }
  }, 1500);

  // Poll status every 3 seconds
  statusPollTimer = setInterval(async () => {
    const data = await apiGet('/api/status');
    if (!data) return;

    if (data.status === 'listening') {
      setStatus('active', 'Service <strong>active</strong> — monitoring INBOX via IMAP IDLE');
      setPipeline([1, 2, 3, 4]);
      document.getElementById('serviceDesc').textContent = 'Active — IMAP IDLE connection live';
    } else if (data.status === 'connecting') {
      setStatus('warn', 'Connecting to <strong>imap.gmail.com</strong> — establishing IMAP IDLE session…');
      setPipeline([1]);
    } else if (data.status === 'error') {
      setStatus('error', `Error: <strong>${data.error || 'Unknown'}</strong>`);
      setPipeline([]);
      serviceActive = false;
      document.getElementById('serviceToggle').checked = false;
      document.getElementById('serviceDesc').textContent = 'Error — check logs for details';
      stopPolling();
    } else if (data.status === 'stopped' || data.status === 'idle') {
      // Only update if we think we're still active (backend stopped unexpectedly)
      if (serviceActive) {
        setStatus('', 'Service <strong>stopped</strong> — IMAP connection closed');
        setPipeline([]);
        serviceActive = false;
        document.getElementById('serviceToggle').checked = false;
        document.getElementById('serviceDesc').textContent = 'Stopped — toggle to resume monitoring';
        stopPolling();
      }
    }
  }, 3000);
}

function stopPolling() {
  if (logPollTimer)    { clearInterval(logPollTimer);    logPollTimer = null; }
  if (statusPollTimer) { clearInterval(statusPollTimer); statusPollTimer = null; }
}

/* ── SERVICE TOGGLE (REAL API CALL) ───────────────────── */
async function handleToggle(checked) {
  if (!credentialsSet) {
    document.getElementById('serviceToggle').checked = false;
    addLog('Apply credentials before starting service', 'warn');
    return;
  }

  if (checked) {
    // Start the listener
    setStatus('warn', 'Connecting to <strong>imap.gmail.com</strong> — establishing IMAP IDLE session…');
    setPipeline([1]);
    addLog('Requesting backend to start IMAP listener...', 'info');

    const result = await apiPost('/api/start');

    if (result.ok) {
      serviceActive = true;
      addLog('Listener thread started — waiting for connection...', 'info');
      setPipeline([1, 2]);
      startPolling();
    } else {
      setStatus('error', `Failed: <strong>${result.message}</strong>`);
      addLog(`Failed to start: ${result.message}`, 'error');
      document.getElementById('serviceToggle').checked = false;
    }

  } else {
    // Stop the listener
    addLog('Requesting backend to stop listener...', 'info');
    const result = await apiPost('/api/stop');

    serviceActive = false;
    stopPolling();
    setStatus('', 'Service <strong>stopped</strong> — IMAP connection closed');
    setPipeline([]);
    document.getElementById('serviceDesc').textContent = 'Stopped — toggle to resume monitoring';
    addLog('IMAP connection closed', 'info');
  }
}

/* ── CLEAR ────────────────────────────────────────────── */
async function clearAll() {
  // Stop listener if running
  if (serviceActive) {
    await apiPost('/api/stop');
    stopPolling();
  }

  document.getElementById('emailInput').value = '';
  document.getElementById('passInput').value  = '';
  document.getElementById('passInput').type   = 'password';
  document.getElementById('eyeBtn').textContent = 'SHOW';
  document.getElementById('serviceToggle').checked  = false;
  document.getElementById('serviceToggle').disabled = true;
  showError('emailError', false);
  showError('passError',  false);
  credentialsSet = false;
  serviceActive  = false;
  setStatus('', 'Service <strong>offline</strong> — enter credentials and apply to begin');
  setPipeline([]);
  document.getElementById('serviceDesc').textContent = 'Disabled — apply credentials first to unlock';
  document.getElementById('applyBtn').innerHTML = '&#9654;&nbsp; apply credentials';
  addLog('All credentials cleared — service stopped', 'warn');
}

/* ── BOOT LOG ─────────────────────────────────────────── */
setTimeout(() => addLog('[SYSTEM] Phishing Detection UI initialized', 'info'),  200);
setTimeout(() => addLog('Connected to backend API server', 'info'),            600);
setTimeout(() => addLog('Awaiting credentials…', 'info'),                     1000);
