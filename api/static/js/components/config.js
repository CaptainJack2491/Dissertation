/**
 * config.js - Experiment configuration and execution
 */
import { api } from '../api.js';
import { ui } from '../ui.js';
import { terminal } from './terminal.js';
import { results } from './results.js';

let isRunning = false;

export const config = {
    async init() {
        await Promise.all([
            this.loadScenarios(),
            this.loadModels(),
            this.loadDefaults()
        ]);

        ui.elements.runBtn.addEventListener('click', () => this.startRun());
        ui.elements.cancelBtn.addEventListener('click', () => this.stopRun());
        
        // Scenario detail updates
        ui.elements.scenarioSelect.addEventListener('change', (e) => this.updateOversight(e.target.value));
    },

    async loadScenarios() {
        const scenarios = await api.get('/api/scenarios');
        ui.elements.scenarioSelect.innerHTML = scenarios.map(s => 
            `<option value="${s.name}">${s.name}</option>`
        ).join('');
        if (scenarios[0]) this.updateOversight(scenarios[0].name);
    },

    async loadModels() {
        const models = await api.get('/api/models');
        ui.elements.modelSelect.innerHTML = models.map(m => 
            `<option value="${m.id}">${m.id} (${m.provider})</option>`
        ).join('');
    },

    async loadDefaults() {
        const cfg = await api.get('/api/config');
        if (cfg.defaults?.oversight) {
            ui.elements.oversightSelect.value = cfg.defaults.oversight;
        }
    },

    async updateOversight(scenarioName) {
        if (!scenarioName) return;
        const details = await api.get(`/api/scenarios/${scenarioName}`);
        const levels = details.oversight_levels || ['low', 'mid', 'high'];
        ui.elements.oversightSelect.innerHTML = levels.map(l => 
            `<option value="${l}">${l.toUpperCase()}</option>`
        ).join('');
    },

    async startRun() {
        const data = {
            scenario: ui.elements.scenarioSelect.value,
            model: ui.elements.modelSelect.value,
            oversight: ui.elements.oversightSelect.value,
            runs: ui.elements.runsInput.value
        };

        this.setRunningState(true);
        terminal.clear();
        terminal.append(`[SYSTEM] Starting experiment: ${data.scenario} | ${data.model}`);

        try {
            await api.post('/api/run', data);
            api.streamLogs(
                (log) => terminal.append(log),
                () => {
                    this.setRunningState(false);
                    ui.updateStatus('complete');
                    terminal.append('[SYSTEM] Run completed successfully.');
                    results.loadAll();
                },
                (err) => {
                    this.setRunningState(false);
                    ui.updateStatus('error');
                    terminal.append(`[ERROR] Stream disconnected: ${err}`);
                }
            );
            ui.updateStatus('running', new Date());
        } catch (err) {
            this.setRunningState(false);
            ui.updateStatus('error');
            terminal.append(`[ERROR] Failed to start run: ${err.message}`);
        }
    },

    async stopRun() {
        try {
            await api.delete('/api/run');
            terminal.append('[SYSTEM] Cancel request sent.');
        } catch (err) {
            terminal.append(`[ERROR] Cancel failed: ${err.message}`);
        }
    },

    setRunningState(running) {
        isRunning = running;
        ui.elements.runBtn.disabled = running;
        ui.elements.cancelBtn.disabled = !running;
    }
};
