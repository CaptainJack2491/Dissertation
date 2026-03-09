/**
 * results.js - Data visualization and reports
 */
import { api } from '../api.js';
import { ui } from '../ui.js';

let activeCharts = []; // Store chart instances to destroy them before redraw

export const results = {
    async init() {
        // Bind events
        ui.elements.csvFileSelect.addEventListener('change', (e) => this.loadCSVData(e.target.value));
        ui.elements.chartFileSelect.addEventListener('change', (e) => this.loadChartData(e.target.value));
        ui.elements.judgeFileSelect.addEventListener('change', (e) => this.loadJudgeData(e.target.value));
        
        // Initial lists
        await this.loadAll();
    },

    async loadAll() {
        await Promise.all([
            this.updateCSVFileList(),
            this.updateJudgeFileList(),
            this.loadImages() // Static images just load once
        ]);
    },

    async updateCSVFileList() {
        try {
            const files = await api.get('/api/results/files');
            const options = files.length > 0 
                ? files.map(f => `<option value="${f}">${f}</option>`).join('')
                : '<option value="">No files found</option>';
            
            ui.elements.csvFileSelect.innerHTML = options;
            ui.elements.chartFileSelect.innerHTML = options;

            // Prefer loading results.csv by default if it exists
            const defaultFile = files.find(f => f.endsWith('results.csv')) || files[0];
            
            if (defaultFile) {
                ui.elements.csvFileSelect.value = defaultFile;
                ui.elements.chartFileSelect.value = defaultFile;
                await this.loadCSVData(defaultFile);
                await this.loadChartData(defaultFile);
            }
        } catch (error) {
            console.error("Failed loading CSV file list", error);
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

    async loadCSVData(filePath) {
        if (!filePath) return;
        ui.elements.csvResults.innerHTML = '<div class="empty-state">Loading data...</div>';

        try {
            const data = await api.get(`/api/results?file=${encodeURIComponent(filePath)}`);
            if (Object.keys(data).length === 0 || data.error) {
                ui.elements.csvResults.innerHTML = '<div class="empty-state">Failed to load data.</div>';
                return;
            }

            // Since we asked for a specific file, it's the only key
            const content = Object.values(data)[0];
            if (content.error) {
                ui.elements.csvResults.innerHTML = `<div class="empty-state">Error: ${content.error}</div>`;
                return;
            }

            let html = `<div class="data-table-wrapper">
                <div class="data-table-title">${filePath}</div>
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
            
            ui.elements.csvResults.innerHTML = html;
        } catch (err) {
            ui.elements.csvResults.innerHTML = `<div class="empty-state">Error: ${err.message}</div>`;
        }
    },

    async loadChartData(filePath) {
        if (!filePath) return;
        
        // Clean up old charts
        activeCharts.forEach(chart => chart.destroy());
        activeCharts = [];
        ui.elements.interactiveCharts.innerHTML = '<div class="empty-state" style="grid-column: 1 / -1;">Generating charts...</div>';

        try {
            const data = await api.get(`/api/results?file=${encodeURIComponent(filePath)}`);
            const content = Object.values(data)[0];
            
            if (!content || content.error || !content.data || content.data.length === 0) {
                ui.elements.interactiveCharts.innerHTML = '<div class="empty-state" style="grid-column: 1 / -1;">Not enough data to graph.</div>';
                return;
            }

            ui.elements.interactiveCharts.innerHTML = '';
            
            // Generate charts based on available columns
            const cols = content.columns;
            
            // 1. Blackbox Categories
            if (cols.includes('blackbox_category')) {
                this.renderPieChart('Blackbox Categories', content.data, 'blackbox_category');
            }
            
            // 2. Glassbox Categories
            if (cols.includes('glassbox_category')) {
                this.renderPieChart('Glassbox Categories', content.data, 'glassbox_category');
            }

            // 3. Models vs Blackbox Category
            if (cols.includes('model') && cols.includes('blackbox_category')) {
                this.renderBarChart('Deception by Model', content.data, 'model', 'blackbox_category');
            }
            
            // 4. Fallback if no specific columns exist
            if (ui.elements.interactiveCharts.innerHTML === '') {
                 ui.elements.interactiveCharts.innerHTML = '<div class="empty-state" style="grid-column: 1 / -1;">No plottable categorical columns found in this CSV.</div>';
            }

        } catch (err) {
            ui.elements.interactiveCharts.innerHTML = `<div class="empty-state" style="grid-column: 1 / -1;">Chart Error: ${err.message}</div>`;
        }
    },

    renderPieChart(title, data, column) {
        const counts = {};
        data.forEach(row => {
            const val = row[column] || 'Unknown';
            counts[val] = (counts[val] || 0) + 1;
        });

        const canvasId = `chart-${Math.random().toString(36).substr(2, 9)}`;
        const container = document.createElement('div');
        container.className = 'chart-container';
        container.innerHTML = `<canvas id="${canvasId}"></canvas>`;
        ui.elements.interactiveCharts.appendChild(container);

        const ctx = document.getElementById(canvasId).getContext('2d');
        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(counts),
                datasets: [{
                    data: Object.values(counts),
                    backgroundColor: ['#9d4edd', '#ef4444', '#10b981', '#f59e0b', '#3b82f6', '#6366f1'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: { display: true, text: title, color: '#f0f0f2', font: { family: 'Inter', size: 14 } },
                    legend: { labels: { color: '#9ea0a6' }, position: 'right' }
                }
            }
        });
        activeCharts.push(chart);
    },

    renderBarChart(title, data, xCol, groupCol) {
        // Group by X then GroupCol
        const matrix = {};
        const groups = new Set();
        
        data.forEach(row => {
            const xVal = row[xCol] || 'Unknown';
            const gVal = row[groupCol] || 'Unknown';
            if (!matrix[xVal]) matrix[xVal] = {};
            matrix[xVal][gVal] = (matrix[xVal][gVal] || 0) + 1;
            groups.add(gVal);
        });

        const labels = Object.keys(matrix);
        const datasets = Array.from(groups).map((group, i) => {
            const colors = ['#ef4444', '#10b981', '#f59e0b', '#3b82f6', '#9d4edd'];
            return {
                label: group,
                data: labels.map(label => matrix[label][group] || 0),
                backgroundColor: colors[i % colors.length],
            }
        });

        const canvasId = `chart-${Math.random().toString(36).substr(2, 9)}`;
        const container = document.createElement('div');
        container.className = 'chart-container';
        container.innerHTML = `<canvas id="${canvasId}"></canvas>`;
        ui.elements.interactiveCharts.appendChild(container);

        const ctx = document.getElementById(canvasId).getContext('2d');
        const chart = new Chart(ctx, {
            type: 'bar',
            data: { labels, datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { stacked: true, ticks: { color: '#9ea0a6' }, grid: { color: '#2a2a2e' } },
                    y: { stacked: true, ticks: { color: '#9ea0a6', stepSize: 1 }, grid: { color: '#2a2a2e' } }
                },
                plugins: {
                    title: { display: true, text: title, color: '#f0f0f2', font: { family: 'Inter', size: 14 } },
                    legend: { labels: { color: '#9ea0a6' } }
                }
            }
        });
        activeCharts.push(chart);
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
                    <div class="data-table-title">${filePath}</div>
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
                // Render JSON as pretty block
                html += `<div class="data-table-wrapper">
                    <div class="data-table-title">${filePath}</div>
                    <pre style="padding: 16px; color: #f0f0f2; font-family: monospace; white-space: pre-wrap; word-wrap: break-word;">${JSON.stringify(content.data, null, 2)}</pre>
                </div>`;
            }
            ui.elements.judgeResults.innerHTML = html;
        } catch (err) {
            ui.elements.judgeResults.innerHTML = `<div class="empty-state">Error: ${err.message}</div>`;
        }
    }
};
