export const ui = {
    get elements() {
        return {
            csvFileSelect: document.getElementById('csv-file-select'),
            judgeFileSelect: document.getElementById('judge-file-select'),
            
            filterModelList: document.getElementById('filter-model-list'),
            filterScenarioList: document.getElementById('filter-scenario-list'),
            filterOversightList: document.getElementById('filter-oversight-list'),
            
            refreshBtn: document.getElementById('refresh-btn'),
            
            csvResults: document.getElementById('csv-results'),
            imageResults: document.getElementById('image-results'),
            judgeResults: document.getElementById('judge-results'),
            interactiveCharts: document.getElementById('interactive-charts'),
            dataStats: document.getElementById('data-stats'),
            
            chartModal: document.getElementById('chart-modal'),
            closeModalBtn: document.getElementById('close-modal-btn'),
            modalChartContainer: document.getElementById('modal-chart-container'),
            
            tabTriggers: document.querySelectorAll('.tab-trigger'),
            tabPanels: document.querySelectorAll('.tab-panel'),

            // New CSV Table Elements
            csvTableStats: document.getElementById('csv-table-stats'),
            btnToggleColumns: document.getElementById('btn-toggle-columns'),
            columnDropdown: document.getElementById('column-dropdown'),
            columnList: document.getElementById('column-list'),

            // Inspector Modal
            inspectorModal: document.getElementById('inspector-modal'),
            closeInspectorBtn: document.getElementById('close-inspector-btn'),
            inspectorContent: document.getElementById('inspector-content')
        };
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