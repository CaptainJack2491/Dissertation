/**
 * results.js - Data visualization and reports
 */
import { api } from '../api.js';
import { ui } from '../ui.js';

let activeCharts = [];
let currentCsvData = null; // Store fetched data locally for quick filtering
let currentCsvColumns = [];
let currentCsvDir = ""; // Directory of the active CSV
let currentVisibleColumns = []; // Track which columns are shown in Table
let modalChart = null;

// Inspector state
let currentInspectorLog = null;
let currentInspectorRow = null;
let currentViewMode = 'visual'; // 'visual' or 'raw'

export const results = {
    async init() {
        // Bind events
        ui.elements.csvFileSelect.addEventListener('change', (e) => this.handleCsvChange(e.target.value));
        ui.elements.judgeFileSelect.addEventListener('change', (e) => this.loadJudgeData(e.target.value));
        ui.elements.refreshBtn.addEventListener('click', () => this.applyFilters());
        
        // Modal Setup
        ui.elements.closeModalBtn.addEventListener('click', () => this.closeChartModal());
        ui.elements.chartModal.addEventListener('click', (e) => {
            if (e.target === ui.elements.chartModal) this.closeChartModal();
        });

        // Inspector Modal
        ui.elements.closeInspectorBtn.addEventListener('click', () => this.closeInspector());
        ui.elements.inspectorModal.addEventListener('click', (e) => {
            if (e.target === ui.elements.inspectorModal) this.closeInspector();
        });

        // Column Toggle
        ui.elements.btnToggleColumns.addEventListener('click', (e) => {
            e.stopPropagation();
            const isVisible = ui.elements.columnDropdown.style.display === 'block';
            ui.elements.columnDropdown.style.display = isVisible ? 'none' : 'block';
        });

        document.addEventListener('click', (e) => {
            if (ui.elements.columnDropdown && !ui.elements.columnDropdown.contains(e.target) && e.target !== ui.elements.btnToggleColumns) {
                ui.elements.columnDropdown.style.display = 'none';
            }
        });

        // Inspector View Toggle
        if (ui.elements.inspectorToggleBtns) {
            ui.elements.inspectorToggleBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    const mode = btn.dataset.view;
                    this.setViewMode(mode);
                });
            });
        }
        
        await Promise.all([
            this.updateCSVFileList(),
            this.updateJudgeFileList(),
            this.loadImages()
        ]);
    },

    closeChartModal() {
        ui.elements.chartModal.style.display = 'none';
        if (modalChart) {
            modalChart.destroy();
            modalChart = null;
        }
    },

    openChartModal(config) {
        ui.elements.chartModal.style.display = 'flex';
        ui.elements.modalChartContainer.innerHTML = '<canvas id="modal-canvas"></canvas>';
        const ctx = document.getElementById('modal-canvas').getContext('2d');
        
        const modalOptions = { ...config.options, maintainAspectRatio: false };
        if (modalOptions.plugins && modalOptions.plugins.legend) {
            modalOptions.plugins.legend.labels = { color: '#e7e9ea', font: { size: 14 } };
        }
        if (modalOptions.plugins && modalOptions.plugins.title) {
            modalOptions.plugins.title.font = { size: 20, family: 'Inter' };
        }

        modalChart = new Chart(ctx, {
            type: config.type,
            data: config.data,
            options: modalOptions
        });
    },

    async updateCSVFileList() {
        try {
            const files = await api.get('/api/results/files');
            const options = files.length > 0 
                ? files.map(f => `<option value="${f}">${f}</option>`).join('')
                : '<option value="">No files found</option>';
            
            ui.elements.csvFileSelect.innerHTML = options;

            const defaultFile = files.find(f => f.endsWith('results.csv')) || files[0];
            if (defaultFile) {
                ui.elements.csvFileSelect.value = defaultFile;
                await this.handleCsvChange(defaultFile);
            }
        } catch (error) {
            console.error("Failed loading CSV list", error);
        }
    },

    async updateJudgeFileList() {
        try {
            const files = await api.get('/api/judge/files');
            const options = files.length > 0 
                ? files.map(f => `<option value="${f}">${f}</option>`).join('')
                : '<option value="">No judge reports found</option>';
            
            ui.elements.judgeFileSelect.innerHTML = options;
            if (files.length > 0) {
                ui.elements.judgeFileSelect.value = files[0];
                await this.loadJudgeData(files[0]);
            }
        } catch (error) {
            console.error("Failed loading Judge file list", error);
        }
    },

    async handleCsvChange(filePath) {
        if (!filePath) return;
        ui.elements.csvResults.innerHTML = '<div class="empty-state">Loading data...</div>';
        ui.elements.interactiveCharts.innerHTML = '<div class="empty-state" style="grid-column: 1 / -1;">Loading charts...</div>';

        try {
            const data = await api.get(`/api/results?file=${encodeURIComponent(filePath)}`);
            const content = Object.values(data)[0];
            
            if (!content || content.error) {
                const err = content?.error || "Unknown error";
                ui.elements.csvResults.innerHTML = `<div class="empty-state">Error: ${err}</div>`;
                ui.elements.interactiveCharts.innerHTML = `<div class="empty-state" style="grid-column: 1 / -1;">Error: ${err}</div>`;
                return;
            }

            currentCsvData = content.data;
            currentCsvColumns = content.columns;
            
            // Store directory of CSV for relative log path resolution
            if (filePath.includes('/')) {
                currentCsvDir = filePath.substring(0, filePath.lastIndexOf('/')) + '/';
            } else {
                currentCsvDir = "";
            }
            
            // Default visibility: Hide very long or redundant columns initially
            const hideByDefault = ['BLACKBOX_JUSTIFICATION', 'GLASSBOX_JUSTIFICATION', 'log_path', 'full_log', 'messages'];
            currentVisibleColumns = currentCsvColumns.filter(c => !hideByDefault.includes(c));

            this.renderColumnSelector();
            this.populateFilters();
            this.applyFilters(); // This draws charts and tables

        } catch (err) {
            ui.elements.csvResults.innerHTML = `<div class="empty-state">Error: ${err.message}</div>`;
            ui.elements.interactiveCharts.innerHTML = `<div class="empty-state" style="grid-column: 1 / -1;">Error: ${err.message}</div>`;
        }
    },

    renderColumnSelector() {
        ui.elements.columnList.innerHTML = `
            <div style="display: flex; gap: 8px; margin-bottom: 8px; border-bottom: 1px solid var(--color-bg-3); padding-bottom: 8px;">
                <span class="filter-link" id="cols-all">All</span>
                <span class="filter-link" id="cols-none">None</span>
            </div>
            <div class="column-grid">
                ${currentCsvColumns.map(col => `
                    <label class="checkbox-item">
                        <input type="checkbox" value="${col}" ${currentVisibleColumns.includes(col) ? 'checked' : ''}>
                        <span title="${col}">${col}</span>
                    </label>
                `).join('')}
            </div>
        `;

        // Bind events
        ui.elements.columnList.querySelectorAll('input').forEach(input => {
            input.addEventListener('change', () => {
                const col = input.value;
                if (input.checked) {
                    if (!currentVisibleColumns.includes(col)) currentVisibleColumns.push(col);
                } else {
                    currentVisibleColumns = currentVisibleColumns.filter(c => c !== col);
                }
                this.applyFilters();
            });
        });

        document.getElementById('cols-all').addEventListener('click', () => {
            currentVisibleColumns = [...currentCsvColumns];
            this.renderColumnSelector();
            this.applyFilters();
        });

        document.getElementById('cols-none').addEventListener('click', () => {
            currentVisibleColumns = [];
            this.renderColumnSelector();
            this.applyFilters();
        });
    },

    populateFilters() {
        const models = new Set();
        const scenarios = new Set();
        const oversights = new Set();

        currentCsvData.forEach(row => {
            if (row.model) models.add(row.model);
            if (row.scenario) scenarios.add(row.scenario);
            if (row.oversight) oversights.add(row.oversight);
        });

        this.renderCheckboxList(ui.elements.filterModelList, Array.from(models).sort(), 'model');
        this.renderCheckboxList(ui.elements.filterScenarioList, Array.from(scenarios).sort(), 'scenario');
        
        // Custom Oversight Sorting
        const oversightPriority = { 'low': 0, 'mid': 1, 'medium': 1, 'high': 2 };
        const sortedOversights = Array.from(oversights).sort((a, b) => {
            const pA = oversightPriority[a.toLowerCase()] ?? 99;
            const pB = oversightPriority[b.toLowerCase()] ?? 99;
            return pA - pB;
        });
        this.renderCheckboxList(ui.elements.filterOversightList, sortedOversights, 'oversight');
    },

    renderCheckboxList(container, items, type) {
        if (items.length === 0) {
            container.innerHTML = '<div class="checkbox-item"><span>No data</span></div>';
            return;
        }

        container.innerHTML = items.map(item => `
            <label class="checkbox-item">
                <input type="checkbox" name="filter-${type}" value="${item}" checked>
                <span title="${item}">${item}</span>
            </label>
        `).join('');
    },

    applyFilters() {
        if (!currentCsvData) return;

        const getChecked = (name) => Array.from(document.querySelectorAll(`input[name="filter-${name}"]:checked`)).map(cb => cb.value);

        const modelFilters = getChecked('model');
        const scenarioFilters = getChecked('scenario');
        const oversightFilters = getChecked('oversight');

        const filteredData = currentCsvData.filter(row => {
            return (modelFilters.length === 0 || modelFilters.includes(row.model)) &&
                   (scenarioFilters.length === 0 || scenarioFilters.includes(row.scenario)) &&
                   (oversightFilters.length === 0 || oversightFilters.includes(row.oversight));
        });

        ui.elements.dataStats.textContent = `Showing ${filteredData.length} of ${currentCsvData.length} records`;
        if (ui.elements.csvTableStats) {
            ui.elements.csvTableStats.textContent = `Found ${filteredData.length} records`;
        }

        this.renderTable(filteredData);
        this.renderCharts(filteredData);
    },

    renderTable(data) {
        if (data.length === 0) {
            ui.elements.csvResults.innerHTML = '<div class="empty-state">No data matches filters.</div>';
            return;
        }

        const visibleCols = currentVisibleColumns;

        let html = `<div class="data-table-wrapper" style="height: calc(100vh - 280px); overflow-y: auto;">
            <table class="data-table">
                <thead>
                    <tr>
                        <th class="cell-action"></th>
                        ${visibleCols.map(c => `<th>${c}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${data.map((row, idx) => `
                        <tr data-idx="${idx}">
                            <td class="cell-action"><button class="btn-row-action" data-idx="${idx}">VIEW</button></td>
                            ${visibleCols.map(col => {
                                const val = row[col] ?? '';
                                const isLong = col.toLowerCase().includes('justification') || col.toLowerCase().includes('id');
                                return `<td class="${isLong ? 'cell-long' : ''}" title="${val}">${val}</td>`;
                            }).join('')}
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>`;
        
        ui.elements.csvResults.innerHTML = html;

        // Bind Row Click
        ui.elements.csvResults.querySelectorAll('tr[data-idx]').forEach(tr => {
            tr.addEventListener('click', (e) => {
                const idx = tr.dataset.idx;
                this.showRowInspector(data[idx]);
            });
        });
        
        // Bind View Button (redundant but explicit)
        ui.elements.csvResults.querySelectorAll('.btn-row-action').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const idx = btn.dataset.idx;
                this.showRowInspector(data[idx]);
            });
        });
    },

    closeInspector() {
        ui.elements.inspectorModal.style.display = 'none';
        currentInspectorLog = null;
        currentInspectorRow = null;
    },

    setViewMode(mode) {
        currentViewMode = mode;
        if (ui.elements.inspectorToggleBtns) {
            ui.elements.inspectorToggleBtns.forEach(btn => {
                btn.classList.toggle('active', btn.dataset.view === mode);
            });
        }
        this.renderInspectorContent();
    },

    async showRowInspector(rowData) {
        currentInspectorRow = rowData;
        currentInspectorLog = null;
        ui.elements.inspectorModal.style.display = 'flex';
        ui.elements.inspectorTitle.textContent = `Run: ${rowData.run_id || rowData.RUN_ID || 'Details'}`;
        
        this.setViewMode('visual'); // Default to visual

        // Strategy to find the log:
        let rawPath = rowData.log_path || rowData.RUN_ID || rowData.run_id;
        if (!rawPath) {
            ui.elements.inspectorContent.innerHTML = '<div class="empty-state">No log path metadata found in record.</div>';
            return;
        }

        let jsonPath = rawPath.endsWith('.json') ? rawPath : (rawPath + '.json');
        const trials = [jsonPath, currentCsvDir + jsonPath, 'logs/' + jsonPath];

        let loaded = false;
        for (const trial of trials) {
            if (loaded) break;
            try {
                const logData = await api.get(`/api/logs/browse?path=${encodeURIComponent(trial)}`);
                currentInspectorLog = logData;
                currentInspectorLog._successfulPath = trial; // Track successful path
                loaded = true;
                this.renderInspectorContent();
            } catch (err) {
                console.log(`Failed trial: ${trial}`);
            }
        }

        if (!loaded) {
            ui.elements.inspectorContent.innerHTML = `
                <div class="empty-state" style="color: var(--color-danger)">
                    Failed to load log file.<br>
                    <div style="margin-top: 8px; color: var(--color-text-secondary); font-size: 0.7rem;">
                        Paths tried:<br>
                        ${trials.map(t => `- ${t}`).join('<br>')}
                    </div>
                </div>`;
        }
    },

    renderInspectorContent() {
        if (!currentInspectorLog && currentViewMode === 'visual') {
            this.renderVisualLoading();
            return;
        }

        if (currentViewMode === 'visual') {
            this.renderVisualInspector();
        } else if (currentViewMode === 'raw') {
            this.renderRawInspector();
        } else if (currentViewMode === 'interrogate') {
            this.renderInterrogateInspector();
        }
    },

    renderVisualLoading() {
        ui.elements.inspectorContent.innerHTML = `
            <div class="inspector-layout">
                <aside class="inspector-sidebar">${this.renderRecordSidebar(currentInspectorRow)}</aside>
                <main class="inspector-main">
                    <div class="empty-state">Loading log file for full conversation view...</div>
                </main>
            </div>`;
    },

    renderRawInspector() {
        const jsonStr = currentInspectorLog ? JSON.stringify(currentInspectorLog, null, 2) : "Log not loaded yet.";
        ui.elements.inspectorContent.innerHTML = `
            <div class="inspector-layout">
                <aside class="inspector-sidebar">${this.renderRecordSidebar(currentInspectorRow)}</aside>
                <main class="inspector-main">
                    <div class="json-viewer-container">${jsonStr}</div>
                </main>
            </div>`;
    },

    renderRecordSidebar(rowData) {
        return `
            <div id="inspector-fields">
                ${Object.entries(rowData).map(([key, val]) => {
                    const hide = ['full_log', 'messages', 'log_path', 'RUN_ID', 'run_id'];
                    if (hide.includes(key)) return ''; 
                    const isJustification = key.includes('JUSTIFICATION');
                    return `
                        <div class="field-entry" ${isJustification ? 'style="margin-top: 12px; border-top: 1px dashed var(--color-bg-3); padding-top: 8px;"' : ''}>
                            <div class="field-label">${key}</div>
                            <div class="field-value" style="${isJustification ? 'font-size: 0.75rem; color: var(--color-text-secondary); line-height: 1.4; word-break: break-word;' : ''}" title="${val}">${val ?? '<span style="color: var(--color-text-muted)">null</span>'}</div>
                        </div>`;
                }).join('')}
            </div>
            ${currentInspectorLog?.final_vfs_state ? `
                <h3 style="margin-top: var(--space-xl); margin-bottom: var(--space-md); font-size: 0.75rem; text-transform: uppercase; color: var(--color-accent); border-top: 1px solid var(--color-bg-3); padding-top: 16px;">Final VFS State</h3>
                <div class="field-entry">
                    ${Object.keys(currentInspectorLog.final_vfs_state['/']?.data || {}).map(f => `
                        <div class="field-value" style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; margin-bottom: 4px; padding: 4px 8px; background: var(--color-bg-2); border-radius: 4px; border: 1px solid var(--color-bg-3); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${f}">${f}</div>
                    `).join('')}
                </div>
            ` : ''}
        `;
    },

    renderVisualInspector() {
        const row = currentInspectorRow;
        const log = currentInspectorLog;
        
        let html = `<div class="inspector-layout">
            <aside class="inspector-sidebar">${this.renderRecordSidebar(row)}</aside>
            <main class="inspector-main">
                <div style="flex: 1; display: flex; flex-direction: column; overflow: hidden;">
        `;

        // Conversation
        if (log && log.conversation) {
            html += `<div class="chat-container">`;
            log.conversation.forEach(msg => {
                html += this.renderChatMessage(msg);
            });
            html += `</div>`;
        } else {
            html += `<div class="empty-state">Conversation data not found in log.</div>`;
        }

        html += `</div></main></div>`;
        ui.elements.inspectorContent.innerHTML = html;
    },

    renderChatMessage(msg) {
        const role = msg.role;
        const content = typeof msg.content === 'object' ? JSON.stringify(msg.content, null, 2) : (msg.content || "");
        const reasoning = msg.reasoning || this.extractReasoningFromContent(content);
        let cleanContent = typeof content === 'string' ? content.replace(/<thought>[\s\S]*?<\/thought>/g, '').trim() : content;

        let html = `<div class="message-bubble role-${role}">
            <div class="bubble-header">${role}</div>`;

        if (reasoning) {
            const parsedReasoning = window.marked ? marked.parse(reasoning) : reasoning.replace(/\n/g, '<br>');
            html += `<div class="reasoning-block">${parsedReasoning}</div>`;
        }

        // Only show main content for non-tool roles to avoid double rendering
        if (cleanContent && role !== 'tool') {
            const parsedContent = window.marked ? marked.parse(String(cleanContent)) : String(cleanContent).replace(/\n/g, '<br>');
            html += `<div class="message-content">${parsedContent}</div>`;
        }

        if (msg.tool_calls && msg.tool_calls.length > 0) {
            html += `<div class="tool-calls-container">`;
            msg.tool_calls.forEach(tc => {
                const func = tc.function || tc;
                html += `<div class="tool-call-item">
                    <span class="tool-call-name">${func.name}</span>(${func.arguments || ''})
                </div>`;
            });
            html += `</div>`;
        }

        if (role === 'tool') {
             const maxLength = 300;
             const isLong = cleanContent.length > maxLength;
             const displayContent = isLong ? cleanContent.substring(0, maxLength) + '...' : cleanContent;
             
             const parsedToolOutput = window.marked ? marked.parse(displayContent) : displayContent.replace(/\n/g, '<br>');
             html += `
                <div class="message-content" style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 4px; border: 1px solid rgba(16,185,129,0.2); margin-top: 8px;">
                    <div style="margin-bottom: 4px; color: rgba(16,185,129,0.6); font-size: 0.6rem; text-transform: uppercase; font-weight: 800;">Output ${isLong ? '(Truncated)' : ''}</div>
                    <div style="color: #10b981; opacity: 0.9;">${parsedToolOutput}</div>
                </div>`;
        }

        html += `</div>`;
        return html;
    },

    extractReasoningFromContent(content) {
        if (typeof content !== 'string') return null;
        const match = content.match(/<thought>([\s\S]*?)<\/thought>/);
        return match ? match[1].trim() : null;
    },

    renderInterrogateInspector() {
        const row = currentInspectorRow;
        
        let html = `<div class="inspector-layout">
            <aside class="inspector-sidebar">${this.renderRecordSidebar(row)}</aside>
            <main class="inspector-main" style="display: flex; flex-direction: column;">
                <div id="interrogate-chat-history" style="flex: 1; overflow-y: auto; padding-right: 10px; margin-bottom: 20px;">
                    <div class="empty-state">
                        <h3>Interrogation Sandbox</h3>
                        <p style="margin-top: 8px;">Start a dynamic session to continue the conversation with the agent from this point.</p>
                        <button id="btn-start-interrogation" class="btn btn-primary" style="margin-top: 15px; padding: 8px 16px;">Start Session</button>
                    </div>
                </div>
                <div id="interrogate-input-area" style="display: none; padding-top: 15px; border-top: 1px solid var(--color-bg-3);">
                    <textarea id="interrogate-input" placeholder="Type your message..." style="width: 100%; min-height: 80px; padding: 10px; background: var(--color-bg-1); border: 1px solid var(--color-bg-3); color: var(--color-text-primary); border-radius: 4px; font-family: 'Inter', sans-serif; resize: vertical;"></textarea>
                    <div style="display: flex; justify-content: flex-end; margin-top: 10px; align-items: center;">
                        <span id="interrogate-status" style="margin-right: auto; font-size: 0.8rem; color: var(--color-text-muted);"></span>
                        <button id="btn-send-interrogate" class="btn btn-primary">Send Message</button>
                    </div>
                </div>
            </main>
        </div>`;
        ui.elements.inspectorContent.innerHTML = html;
        
        setTimeout(() => {
            const startBtn = document.getElementById('btn-start-interrogation');
            if (startBtn) startBtn.addEventListener('click', () => this.startInterrogationSession());
            
            const sendBtn = document.getElementById('btn-send-interrogate');
            if (sendBtn) sendBtn.addEventListener('click', () => this.sendInterrogationMessage());
            
            const inputField = document.getElementById('interrogate-input');
            if (inputField) {
                inputField.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                        this.sendInterrogationMessage();
                    }
                });
            }
        }, 0);
    },
    
    async startInterrogationSession() {
        const rowData = currentInspectorRow;
        const statusEl = document.getElementById('interrogate-status');
        const inputArea = document.getElementById('interrogate-input-area');
        const startBtn = document.getElementById('btn-start-interrogation');
        
        // Use the successful path established during GET
        let targetLogPath = currentInspectorLog && currentInspectorLog._successfulPath 
                            ? currentInspectorLog._successfulPath : null;
                            
        if (!targetLogPath) {
            // Fallback heuristics just in case
            let rawPath = rowData.log_path || rowData.RUN_ID || rowData.run_id;
            if (!rawPath) return;
            let jsonPath = rawPath.endsWith('.json') ? rawPath : (rawPath + '.json');
            targetLogPath = currentCsvDir ? currentCsvDir + jsonPath : jsonPath;
        }
        
        startBtn.innerHTML = 'Initializing...';
        startBtn.disabled = true;
        
        try {
            let response = await fetch('/api/interrogate/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ log_path: targetLogPath })
            });
            
            if (!response.ok) {
                // Secondary fallback attempt
                let rawPath = rowData.log_path || rowData.RUN_ID || rowData.run_id;
                let jsonPath = rawPath.endsWith('.json') ? rawPath : (rawPath + '.json');
                response = await fetch('/api/interrogate/start', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ log_path: jsonPath })
                });
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.detail || "Failed to initialize session. Could not load log.");
                }
            }
            const data = await response.json();
            
            this.currentInterrogationSession = data.session_id;
            this.interrogationNewMessages = []; // Reset local new messages
            
            this.renderInterrogateHistory();
            
            inputArea.style.display = 'block';
            statusEl.innerHTML = `<span style="color: var(--color-success);">Session Active (${data.model})</span>`;
            
            // Force scroll after layout changes (such as displaying inputArea)
            setTimeout(() => {
                const historyEl = document.getElementById('interrogate-chat-history');
                if (historyEl) historyEl.scrollTop = historyEl.scrollHeight;
            }, 10);
            
        } catch (err) {
            startBtn.innerHTML = 'Start Session';
            startBtn.disabled = false;
            alert(err.message);
        }
    },
    
    renderInterrogateHistory() {
        const historyEl = document.getElementById('interrogate-chat-history');
        if (!historyEl || !currentInspectorLog) return;
        
        let html = `<div class="chat-container">`;
        if (currentInspectorLog.conversation) {
            currentInspectorLog.conversation.forEach(msg => {
                html += this.renderChatMessage(msg);
            });
        }
        
        if (this.interrogationNewMessages) {
             this.interrogationNewMessages.forEach(msg => {
                  html += this.renderChatMessage(msg);
             });
        }
        
        html += `</div>`;
        historyEl.innerHTML = html;
        historyEl.scrollTop = historyEl.scrollHeight;
    },
    
    async sendInterrogationMessage() {
        const inputField = document.getElementById('interrogate-input');
        const sendBtn = document.getElementById('btn-send-interrogate');
        const statusEl = document.getElementById('interrogate-status');
        const historyEl = document.getElementById('interrogate-chat-history');
        
        const message = inputField.value.trim();
        if (!message || !this.currentInterrogationSession) return;
        
        inputField.value = '';
        inputField.disabled = true;
        sendBtn.disabled = true;
        
        const userMsg = { role: 'user', content: message };
        this.interrogationNewMessages.push(userMsg);
        this.renderInterrogateHistory();
        
        const thinkingId = 'thinking-' + Date.now();
        historyEl.insertAdjacentHTML('beforeend', `
            <div id="${thinkingId}" class="message-bubble role-assistant thinking-pulse">
                <div class="pulse-ring"></div>
                <span style="margin-left: 30px; font-style: italic; color: var(--color-accent);">Agent is thinking... (this may take up to 30s)</span>
            </div>
        `);
        historyEl.scrollTop = historyEl.scrollHeight;
        
        statusEl.textContent = 'Processing request...';
        
        try {
            const response = await fetch('/api/interrogate/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.currentInterrogationSession,
                    message: message
                })
            });
            
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || "Error processing chat");
            
            document.getElementById(thinkingId)?.remove();
            
            const assistantMsg = { 
                role: 'assistant', 
                content: data.content,
                reasoning: data.reasoning,
                tool_calls: data.tool_calls
            };
            this.interrogationNewMessages.push(assistantMsg);
            
            this.renderInterrogateHistory();
            statusEl.textContent = `Log saved incrementally (${new Date().toLocaleTimeString()})`;
            
        } catch (err) {
            document.getElementById(thinkingId)?.remove();
            statusEl.innerHTML = `<span style="color: var(--color-danger);">Error: ${err.message}</span>`;
        } finally {
            inputField.disabled = false;
            sendBtn.disabled = false;
            inputField.focus();
            historyEl.scrollTop = historyEl.scrollHeight;
        }
    },

    getCategoryColor(cat) {
        if (!cat) return 'var(--color-accent)';
        const c = cat.toLowerCase();
        if (c.includes('deceptive') || c.includes('fabricated') || c.includes('harmful')) return '#ef4444';
        if (c.includes('omitted') || c.includes('suspicious')) return '#f59e0b';
        if (c.includes('accurate') || c.includes('honest')) return '#10b981';
        return 'var(--color-accent)';
    },

    renderCharts(data) {
        activeCharts.forEach(chart => chart.destroy());
        activeCharts = [];
        ui.elements.interactiveCharts.innerHTML = '';

        if (data.length === 0) {
            ui.elements.interactiveCharts.innerHTML = '<div class="empty-state" style="grid-column: 1 / -1;">No data to chart.</div>';
            return;
        }

        const cols = currentCsvColumns;
        
        if (cols.includes('blackbox_category')) {
            this.renderDoughnutChart('Blackbox Categories', data, 'blackbox_category');
        }
        
        if (cols.includes('glassbox_category')) {
            this.renderDoughnutChart('Glassbox Categories', data, 'glassbox_category');
        }

        if (cols.includes('model') && cols.includes('blackbox_category')) {
            this.renderStackedBarChart('Blackbox Category by Model', data, 'model', 'blackbox_category');
        }

        if (cols.includes('oversight') && cols.includes('blackbox_category')) {
            this.renderStackedBarChart('Blackbox Category by Oversight', data, 'oversight', 'blackbox_category');
        }

        if (cols.includes('model') && cols.includes('total_tokens')) {
            this.renderAverageTokenUsageChart('Average Token Usage by Model', data);
            this.renderTotalTokenUsageChart('Total Token Usage by Model', data);
        }

        if (ui.elements.interactiveCharts.innerHTML === '') {
             ui.elements.interactiveCharts.innerHTML = '<div class="empty-state" style="grid-column: 1 / -1;">No plottable categorical columns found.</div>';
        }
    },

    renderAverageTokenUsageChart(title, data) {
        const metrics = {}; // { model: { total: 0, count: 0, prompt: 0, completion: 0 } }
        
        data.forEach(row => {
            const model = row.model || 'Unknown';
            if (!row.total_tokens) return;
            
            if (!metrics[model]) {
                metrics[model] = { total: 0, prompt: 0, completion: 0, count: 0 };
            }
            metrics[model].total += row.total_tokens || 0;
            metrics[model].prompt += row.prompt_tokens || 0;
            metrics[model].completion += row.completion_tokens || 0;
            metrics[model].count += 1;
        });

        const labels = Object.keys(metrics).sort();
        if (labels.length === 0) return;

        const datasets = [
            {
                label: 'Avg Prompt Tokens',
                data: labels.map(l => metrics[l].prompt / metrics[l].count),
                backgroundColor: '#3b82f6',
            },
            {
                label: 'Avg Completion Tokens',
                data: labels.map(l => metrics[l].completion / metrics[l].count),
                backgroundColor: '#10b981',
            }
        ];

        const config = {
            type: 'bar',
            data: { labels, datasets },
            options: {
                ...this.getChartOptions(title),
                scales: {
                    x: { stacked: true, ticks: { color: '#9ea0a6' }, grid: { color: '#2a2a2e' } },
                    y: { stacked: true, ticks: { color: '#9ea0a6' }, grid: { color: '#2a2a2e' } }
                }
            }
        };

        const canvasId = `chart-${Math.random().toString(36).substr(2, 9)}`;
        this.createChartContainer(canvasId, config);

        const ctx = document.getElementById(canvasId).getContext('2d');
        const chart = new Chart(ctx, config);
        activeCharts.push(chart);
    },

    renderTotalTokenUsageChart(title, data) {
        const metrics = {}; // { model: { prompt: 0, completion: 0 } }
        
        data.forEach(row => {
            const model = row.model || 'Unknown';
            if (!row.total_tokens) return;
            
            if (!metrics[model]) {
                metrics[model] = { prompt: 0, completion: 0 };
            }
            metrics[model].prompt += row.prompt_tokens || 0;
            metrics[model].completion += row.completion_tokens || 0;
        });

        const labels = Object.keys(metrics).sort();
        if (labels.length === 0) return;

        const datasets = [
            {
                label: 'Total Prompt Tokens',
                data: labels.map(l => metrics[l].prompt),
                backgroundColor: '#6366f1',
            },
            {
                label: 'Total Completion Tokens',
                data: labels.map(l => metrics[l].completion),
                backgroundColor: '#f59e0b',
            }
        ];

        const config = {
            type: 'bar',
            data: { labels, datasets },
            options: {
                ...this.getChartOptions(title),
                scales: {
                    x: { stacked: true, ticks: { color: '#9ea0a6' }, grid: { color: '#2a2a2e' } },
                    y: { stacked: true, ticks: { color: '#9ea0a6' }, grid: { color: '#2a2a2e' } }
                }
            }
        };

        const canvasId = `chart-${Math.random().toString(36).substr(2, 9)}`;
        this.createChartContainer(canvasId, config);

        const ctx = document.getElementById(canvasId).getContext('2d');
        const chart = new Chart(ctx, config);
        activeCharts.push(chart);
    },

    renderDoughnutChart(title, data, column) {
        const counts = {};
        data.forEach(row => {
            const val = row[column] || 'Unknown';
            counts[val] = (counts[val] || 0) + 1;
        });

        const config = {
            type: 'doughnut',
            data: {
                labels: Object.keys(counts),
                datasets: [{
                    data: Object.values(counts),
                    backgroundColor: ['#9d4edd', '#ef4444', '#10b981', '#f59e0b', '#3b82f6', '#6366f1'],
                    borderWidth: 0
                }]
            },
            options: this.getChartOptions(title)
        };

        const canvasId = `chart-${Math.random().toString(36).substr(2, 9)}`;
        this.createChartContainer(canvasId, config);

        const ctx = document.getElementById(canvasId).getContext('2d');
        const chart = new Chart(ctx, config);
        activeCharts.push(chart);
    },

    renderStackedBarChart(title, data, xCol, groupCol) {
        const matrix = {};
        const groups = new Set();
        
        data.forEach(row => {
            const xVal = row[xCol] || 'Unknown';
            const gVal = row[groupCol] || 'Unknown';
            if (!matrix[xVal]) matrix[xVal] = {};
            matrix[xVal][gVal] = (matrix[xVal][gVal] || 0) + 1;
            groups.add(gVal);
        });

        let labels = Object.keys(matrix);

        // Custom sorting for X-axis labels (like Oversight)
        if (xCol === 'oversight') {
            const oversightPriority = { 'low': 0, 'mid': 1, 'medium': 1, 'high': 2 };
            labels.sort((a, b) => (oversightPriority[a.toLowerCase()] ?? 99) - (oversightPriority[b.toLowerCase()] ?? 99));
        } else {
            labels.sort();
        }

        const datasets = Array.from(groups).map((group, i) => {
            const colors = ['#ef4444', '#10b981', '#f59e0b', '#3b82f6', '#9d4edd', '#6366f1'];
            return {
                label: group,
                data: labels.map(label => matrix[label][group] || 0),
                backgroundColor: colors[i % colors.length],
            }
        });

        const config = {
            type: 'bar',
            data: { labels, datasets },
            options: {
                ...this.getChartOptions(title),
                scales: {
                    x: { stacked: true, ticks: { color: '#9ea0a6' }, grid: { color: '#2a2a2e' } },
                    y: { stacked: true, ticks: { color: '#9ea0a6', stepSize: 1 }, grid: { color: '#2a2a2e' } }
                }
            }
        };

        const canvasId = `chart-${Math.random().toString(36).substr(2, 9)}`;
        this.createChartContainer(canvasId, config);

        const ctx = document.getElementById(canvasId).getContext('2d');
        const chart = new Chart(ctx, config);
        activeCharts.push(chart);
    },

    createChartContainer(canvasId, config) {
        const container = document.createElement('div');
        container.className = 'chart-container';
        container.innerHTML = `<canvas id="${canvasId}" title="Click to expand"></canvas>`;
        ui.elements.interactiveCharts.appendChild(container);
        
        setTimeout(() => {
            const canvas = document.getElementById(canvasId);
            if (canvas && config) {
                canvas.addEventListener('click', () => this.openChartModal(config));
            }
        }, 0);
    },

    getChartOptions(title) {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: { display: true, text: title, color: '#f0f0f2', font: { family: 'Inter', size: 14 } },
                legend: { labels: { color: '#9ea0a6' }, position: 'bottom' }
            }
        };
    },

    async loadImages() {
        const images = await api.get('/api/results/images');
        if (images.length === 0) return;

        ui.elements.imageResults.innerHTML = images.map(img => `
            <div class="image-card">
                <img src="/api/results/images/${img.name}" alt="${img.name}" loading="lazy">
                <div class="image-card-footer">${img.name}</div>
            </div>
        `).join('');
    },

    async loadJudgeData(filePath) {
        if (!filePath) return;
        ui.elements.judgeResults.innerHTML = '<div class="empty-state">Loading data...</div>';

        try {
            const data = await api.get(`/api/judge/results?file=${encodeURIComponent(filePath)}`);
            if (Object.keys(data).length === 0 || data.message) {
                ui.elements.judgeResults.innerHTML = '<div class="empty-state">No data available in this report.</div>';
                return;
            }

            const content = Object.values(data)[0];
            if (content.error) {
                 ui.elements.judgeResults.innerHTML = `<div class="empty-state">Error: ${content.error}</div>`;
                 return;
            }

            let html = '';
            if (content.type === 'csv') {
                html += `<div class="data-table-wrapper">
                    <div style="overflow-x: auto;">
                        <table class="data-table">
                            <thead><tr>${content.columns.map(c => `<th>${c}</th>`).join('')}</tr></thead>
                            <tbody>
                                ${content.data.map(row => `
                                    <tr>${content.columns.map(col => `<td>${row[col] ?? ''}</td>`).join('')}</tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>`;
            } else {
                html += `<div class="data-table-wrapper">
                    <pre style="padding: 16px; color: #f0f0f2; font-family: monospace; white-space: pre-wrap; word-wrap: break-word;">${JSON.stringify(content.data, null, 2)}</pre>
                </div>`;
            }
            ui.elements.judgeResults.innerHTML = html;
        } catch (err) {
            ui.elements.judgeResults.innerHTML = `<div class="empty-state">Error: ${err.message}</div>`;
        }
    }
};