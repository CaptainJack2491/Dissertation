/* ==========================================================================
   AI Agent Reasoning Experiment Framework - Web GUI App
   ========================================================================== */

const API_BASE = '';

// State
let eventSource = null;
let isRunning = false;

// ==========================================================================
// DOM Elements
// ==========================================================================

const elements = {
    // Configuration
    scenarioSelect: document.getElementById('scenario-select'),
    modelSelect: document.getElementById('model-select'),
    oversightSelect: document.getElementById('oversight-select'),
    runsInput: document.getElementById('runs-input'),
    
    // Buttons
    runBtn: document.getElementById('run-btn'),
    cancelBtn: document.getElementById('cancel-btn'),
    clearLogsBtn: document.getElementById('clear-logs-btn'),
    
    // Status
    statusBadge: document.getElementById('status-badge'),
    statusTime: document.getElementById('status-time'),
    
    // Logs
    logsContainer: document.getElementById('logs-container'),
    
    // Results
    csvResults: document.getElementById('csv-results'),
    imageResults: document.getElementById('image-results'),
    judgeResults: document.getElementById('judge-results'),
    
    // Tabs
    tabBtns: document.querySelectorAll('.tab-btn'),
    tabContents: document.querySelectorAll('.tab-content'),
};

// ==========================================================================
// Initialization
// ==========================================================================

document.addEventListener('DOMContentLoaded', async () => {
    await loadConfig();
    await loadScenarios();
    await loadModels();
    setupEventListeners();
    startStatusPolling();
});

// ==========================================================================
// API Functions
// ==========================================================================

async function loadConfig() {
    try {
        const response = await fetch(`${API_BASE}/api/config`);
        const config = await response.json();
        
        // Set default values from config
        if (config.defaults?.oversight) {
            elements.oversightSelect.value = config.defaults.oversight;
        }
    } catch (error) {
        console.error('Failed to load config:', error);
    }
}

async function loadScenarios() {
    try {
        const response = await fetch(`${API_BASE}/api/scenarios`);
        const scenarios = await response.json();
        
        elements.scenarioSelect.innerHTML = scenarios.map(s => 
            `<option value="${s.name}">${s.name}</option>`
        ).join('');
        
        // If only one scenario, auto-select it and load oversight levels
        if (scenarios.length === 1) {
            elements.scenarioSelect.value = scenarios[0].name;
            updateOversightLevels(scenarios[0]);
        }
    } catch (error) {
        console.error('Failed to load scenarios:', error);
        elements.scenarioSelect.innerHTML = '<option value="">Error loading scenarios</option>';
    }
}

async function loadModels() {
    try {
        const response = await fetch(`${API_BASE}/api/models`);
        const models = await response.json();
        
        elements.modelSelect.innerHTML = models.map(m => 
            `<option value="${m.id}">${m.id} (${m.provider})</option>`
        ).join('');
    } catch (error) {
        console.error('Failed to load models:', error);
        elements.modelSelect.innerHTML = '<option value="">Error loading models</option>';
    }
}

async function startRun() {
    const scenario = elements.scenarioSelect.value;
    const model = elements.modelSelect.value;
    const oversight = elements.oversightSelect.value;
    const runs = elements.runsInput.value;
    
    if (!scenario || !model) {
        alert('Please select a scenario and model');
        return;
    }
    
    // Show loading state
    elements.runBtn.classList.add('loading');
    elements.runBtn.disabled = true;
    elements.cancelBtn.disabled = false;
    isRunning = true;
    
    // Clear logs
    elements.logsContainer.innerHTML = '';
    appendLog('info', `Starting experiment: ${scenario} with ${model} (oversight: ${oversight}, runs: ${runs})`);
    
    try {
        // TODO: For now, we just trigger the run with current config
        // In the future, we could modify config via API
        const response = await fetch(`${API_BASE}/api/run`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ scenario, model, oversight, runs })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        // Start log streaming
        startLogStream();
        updateStatus('running');
        
    } catch (error) {
        console.error('Failed to start run:', error);
        appendLog('error', `Failed to start: ${error.message}`);
        resetRunState();
    }
}

async function cancelRun() {
    try {
        const response = await fetch(`${API_BASE}/api/run`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        appendLog('warn', 'Run cancelled by user');
        updateStatus('cancelled');
        
    } catch (error) {
        console.error('Failed to cancel run:', error);
    } finally {
        stopLogStream();
        resetRunState();
    }
}

// ==========================================================================
// Log Streaming
// ==========================================================================

function startLogStream() {
    stopLogStream(); // Close any existing connection
    
    eventSource = new EventSource(`${API_BASE}/api/logs/stream`);
    
    eventSource.onmessage = (event) => {
        const data = event.data;
        if (data) {
            appendLog('info', data);
        }
    };
    
    eventSource.addEventListener('log', (event) => {
        const data = event.data;
        if (data) {
            appendLog('info', data);
        }
    });
    
    eventSource.addEventListener('done', (event) => {
        appendLog('info', '=== Run Complete ===');
        stopLogStream();
        isRunning = false;
        updateStatus('complete');
        resetRunState();
        loadResults();
    });
    
    eventSource.addEventListener('error', (event) => {
        console.error('SSE Error:', event);
    });
}

function stopLogStream() {
    if (eventSource) {
        eventSource.close();
        eventSource = null;
    }
}

function appendLog(level, message) {
    // Remove empty state if present
    const emptyState = elements.logsContainer.querySelector('.logs-empty');
    if (emptyState) {
        emptyState.remove();
    }
    
    const line = document.createElement('div');
    line.className = 'log-line';
    
    // Color based on content
    let logLevel = 'log-level-3';
    if (message.includes('[ERROR]') || message.includes('error') || message.includes('Error')) {
        logLevel = 'log-level-1';
    } else if (message.includes('[WARN]') || message.includes('warning') || message.includes('Warning')) {
        logLevel = 'log-level-2';
    } else if (message.includes('[DEBUG]') || message.includes('[DEBUG+]')) {
        logLevel = 'log-level-4';
    }
    
    line.classList.add(logLevel);
    line.textContent = message;
    
    elements.logsContainer.appendChild(line);
    
    // Auto-scroll to bottom
    elements.logsContainer.scrollTop = elements.logsContainer.scrollHeight;
}

function clearLogs() {
    elements.logsContainer.innerHTML = '<div class="logs-empty">Run an experiment to see logs...</div>';
}

// ==========================================================================
// Status Polling
// ==========================================================================

let statusPollingInterval = null;

function startStatusPolling() {
    statusPollingInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE}/api/run/status`);
            const status = await response.json();
            
            if (status.status !== 'idle' && !isRunning) {
                // Something is running but we don't know about it
                isRunning = true;
                elements.runBtn.classList.add('loading');
                elements.runBtn.disabled = true;
                elements.cancelBtn.disabled = false;
                startLogStream();
            }
            
            updateStatusDisplay(status.status, status.start_time);
            
        } catch (error) {
            console.error('Status poll error:', error);
        }
    }, 2000);
}

function updateStatus(status) {
    updateStatusDisplay(status);
    
    if (status === 'running') {
        elements.runBtn.classList.add('loading');
        elements.runBtn.disabled = true;
        elements.cancelBtn.disabled = false;
    }
}

function updateStatusDisplay(status, startTime = null) {
    elements.statusBadge.className = `badge badge-${status}`;
    
    const statusText = {
        'idle': 'Idle',
        'running': 'Running...',
        'complete': 'Complete',
        'error': 'Error',
        'cancelled': 'Cancelled'
    };
    
    elements.statusBadge.textContent = statusText[status] || status;
    
    if (startTime) {
        const date = new Date(startTime);
        elements.statusTime.textContent = `Started: ${date.toLocaleTimeString()}`;
    } else if (status === 'idle') {
        elements.statusTime.textContent = '';
    }
}

function resetRunState() {
    elements.runBtn.classList.remove('loading');
    elements.runBtn.disabled = false;
    elements.cancelBtn.disabled = true;
    isRunning = false;
}

// ==========================================================================
// Results Loading
// ==========================================================================

async function loadResults() {
    await Promise.all([
        loadCSVResults(),
        loadImageResults(),
        loadJudgeResults()
    ]);
}

async function loadCSVResults() {
    try {
        const response = await fetch(`${API_BASE}/api/results`);
        const results = await response.json();
        
        if (Object.keys(results).length === 0) {
            elements.csvResults.innerHTML = '<div class="empty-state">No results yet</div>';
            return;
        }
        
        let html = '';
        
        for (const [filename, data] of Object.entries(results)) {
            if (data.error) {
                html += `<h3>${filename}</h3><p>Error: ${data.error}</p>`;
                continue;
            }
            
            html += `<h3>${filename}.csv</h3>`;
            html += '<div style="overflow-x: auto;"><table class="data-table">';
            
            // Header
            html += '<thead><tr>';
            for (const col of data.columns) {
                html += `<th>${col}</th>`;
            }
            html += '</tr></thead>';
            
            // Body
            html += '<tbody>';
            for (const row of data.data) {
                html += '<tr>';
                for (const col of data.columns) {
                    html += `<td>${row[col] ?? ''}</td>`;
                }
                html += '</tr>';
            }
            html += '</tbody></table></div>';
        }
        
        elements.csvResults.innerHTML = html || '<div class="empty-state">No results yet</div>';
        
    } catch (error) {
        console.error('Failed to load CSV results:', error);
    }
}

async function loadImageResults() {
    try {
        const response = await fetch(`${API_BASE}/api/results/images`);
        const images = await response.json();
        
        if (images.length === 0) {
            elements.imageResults.innerHTML = '<div class="empty-state">No visualizations yet</div>';
            return;
        }
        
        elements.imageResults.innerHTML = images.map(img => `
            <div class="image-card">
                <img src="${API_BASE}/api/results/images/${img.name}" alt="${img.name}">
                <div class="image-title">${img.name}</div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Failed to load images:', error);
    }
}

async function loadJudgeResults() {
    try {
        const response = await fetch(`${API_BASE}/api/judge/results`);
        const results = await response.json();
        
        if (results.message || Object.keys(results).length === 0) {
            elements.judgeResults.innerHTML = '<div class="empty-state">No judge results yet</div>';
            return;
        }
        
        let html = '';
        
        for (const [filename, data] of Object.entries(results)) {
            if (data.type === 'csv') {
                html += `<h3>${filename}</h3>`;
                html += '<div style="overflow-x: auto;"><table class="data-table">';
                
                html += '<thead><tr>';
                for (const col of data.columns) {
                    html += `<th>${col}</th>`;
                }
                html += '</tr></thead><tbody>';
                
                for (const row of data.data) {
                    html += '<tr>';
                    for (const col of data.columns) {
                        html += `<td>${row[col] ?? ''}</td>`;
                    }
                    html += '</tr>';
                }
                html += '</tbody></table></div>';
            } else {
                html += `<h3>${filename}</h3><pre>${JSON.stringify(data.data, null, 2)}</pre>`;
            }
        }
        
        elements.judgeResults.innerHTML = html || '<div class="empty-state">No judge results</div>';
        
    } catch (error) {
        console.error('Failed to load judge results:', error);
    }
}

// ==========================================================================
// Event Listeners
// ==========================================================================

function setupEventListeners() {
    // Run button
    elements.runBtn.addEventListener('click', startRun);
    
    // Cancel button
    elements.cancelBtn.addEventListener('click', cancelRun);
    
    // Clear logs button
    elements.clearLogsBtn.addEventListener('click', clearLogs);
    
    // Scenario selection - update oversight levels
    elements.scenarioSelect.addEventListener('change', async (e) => {
        const scenarioName = e.target.value;
        if (!scenarioName) return;
        
        try {
            const response = await fetch(`${API_BASE}/api/scenarios/${scenarioName}`);
            const scenario = await response.json();
            updateOversightLevels(scenario);
        } catch (error) {
            console.error('Failed to load scenario details:', error);
        }
    });
    
    // Tab switching
    elements.tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;
            
            // Update active tab button
            elements.tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Update active tab content
            elements.tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === `tab-${tabId}`) {
                    content.classList.add('active');
                }
            });
            
            // Load results if switching to results tab
            if (tabId === 'csv' || tabId === 'images' || tabId === 'judge') {
                loadResults();
            }
        });
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + Enter to run
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && !isRunning) {
            startRun();
        }
    });
}

function updateOversightLevels(scenario) {
    const oversightSelect = elements.oversightSelect;
    const levels = scenario.oversight_levels || [];
    
    if (levels.length === 0) {
        // No scenario-specific oversight, use global levels
        oversightSelect.innerHTML = `
            <option value="low">Low</option>
            <option value="mid">Mid</option>
            <option value="high">High</option>
        `;
    } else {
        oversightSelect.innerHTML = levels.map(level => 
            `<option value="${level}">${level.charAt(0).toUpperCase() + level.slice(1)}</option>`
        ).join('');
    }
}
