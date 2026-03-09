/**
 * results.js - Data visualization and reports
 */
import { api } from '../api.js';
import { ui } from '../ui.js';

let activeCharts = [];
let currentCsvData = null; // Store fetched data locally for quick filtering
let currentCsvColumns = [];
let modalChart = null;

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
            
            this.populateFilters();
            this.applyFilters(); // This draws charts and tables

        } catch (err) {
            ui.elements.csvResults.innerHTML = `<div class="empty-state">Error: ${err.message}</div>`;
            ui.elements.interactiveCharts.innerHTML = `<div class="empty-state" style="grid-column: 1 / -1;">Error: ${err.message}</div>`;
        }
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

        this.renderTable(filteredData);
        this.renderCharts(filteredData);
    },

    renderTable(data) {
        if (data.length === 0) {
            ui.elements.csvResults.innerHTML = '<div class="empty-state">No data matches filters.</div>';
            return;
        }

        let html = `<div class="data-table-wrapper">
            <div style="overflow-x: auto;">
                <table class="data-table">
                    <thead><tr>${currentCsvColumns.map(c => `<th>${c}</th>`).join('')}</tr></thead>
                    <tbody>
                        ${data.map(row => `
                            <tr>${currentCsvColumns.map(col => `<td>${row[col] ?? ''}</td>`).join('')}</tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>`;
        
        ui.elements.csvResults.innerHTML = html;
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