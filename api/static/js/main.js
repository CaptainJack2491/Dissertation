/**
 * main.js - Application Entry Point
 */
import { ui } from './ui.js';
import { api } from './api.js';
import { terminal } from './components/terminal.js';
import { config } from './components/config.js';
import { results } from './components/results.js';

async function init() {
    console.log('Initializing AI Reasoning Framework GUI...');

    // Init Core Components
    terminal.init();
    await config.init();
    await results.init();
    
    // Init UI behaviors
    ui.initTabs((tabId) => {
        // Refresh data when switching to results tabs
        if (['csv', 'images', 'judge'].includes(tabId)) {
            results.loadAll();
        }
    });

    // Initial Status Check
    try {
        const status = await api.get('/api/run/status');
        ui.updateStatus(status.status, status.start_time);
        
        if (status.status === 'running') {
            config.setRunningState(true);
            // Re-attach to stream if page reloaded
            api.streamLogs(
                (log) => terminal.append(log),
                () => {
                    config.setRunningState(false);
                    ui.updateStatus('complete');
                    results.loadAll();
                }
            );
        }
    } catch (e) {
        console.warn('Initial status check failed', e);
    }
}

// Start the app
function start() {
    init().catch(err => {
        console.error("Initialization error:", err);
        const logsContainer = document.getElementById('logs-container');
        if (logsContainer) {
            const errorLine = document.createElement('div');
            errorLine.className = 'terminal-line error';
            errorLine.textContent = `[GUI STARTUP ERROR] ${err.message}`;
            logsContainer.appendChild(errorLine);
        }
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
} else {
    start();
}
