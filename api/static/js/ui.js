/**
 * ui.js - Global UI Utilities
 */

export const ui = {
    get elements() {
        return {
            scenarioSelect: document.getElementById('scenario-select'),
            modelSelect: document.getElementById('model-select'),
            oversightSelect: document.getElementById('oversight-select'),
            runsInput: document.getElementById('runs-input'),
            runBtn: document.getElementById('run-btn'),
            cancelBtn: document.getElementById('cancel-btn'),
            statusBadge: document.getElementById('status-badge'),
            statusTime: document.getElementById('status-time'),
            logsContainer: document.getElementById('logs-container'),
            
            csvResults: document.getElementById('csv-results'),
            imageResults: document.getElementById('image-results'),
            judgeResults: document.getElementById('judge-results'),
            interactiveCharts: document.getElementById('interactive-charts'),
            
            csvFileSelect: document.getElementById('csv-file-select'),
            chartFileSelect: document.getElementById('chart-file-select'),
            judgeFileSelect: document.getElementById('judge-file-select'),
            
            tabTriggers: document.querySelectorAll('.tab-trigger'),
            tabPanels: document.querySelectorAll('.tab-panel'),
            clearLogsBtn: document.getElementById('clear-logs-btn'),
            scrollLockBtn: document.getElementById('scroll-lock-btn')
        };
    },

    updateStatus(status, time = null) {
        const { statusBadge, statusTime } = this.elements;
        statusBadge.className = `badge badge-${status}`;
        statusBadge.textContent = status.toUpperCase();
        
        if (time) {
            const date = new Date(time);
            statusTime.textContent = date.toLocaleTimeString();
        } else if (status === 'idle') {
            statusTime.textContent = '';
        }
    },

    initTabs(onTabChange) {
        this.elements.tabTriggers.forEach(trigger => {
            trigger.addEventListener('click', () => {
                const tabId = trigger.dataset.tab;
                
                this.elements.tabTriggers.forEach(t => t.classList.remove('active'));
                this.elements.tabPanels.forEach(p => p.classList.remove('active'));
                
                trigger.classList.add('active');
                document.getElementById(`tab-${tabId}`).classList.add('active');
                
                if (onTabChange) onTabChange(tabId);
            });
        });
    }
};
