/**
 * api.js - Core API communication
 */

const API_BASE = '';

export const api = {
    async get(endpoint) {
        const response = await fetch(`${API_BASE}${endpoint}`);
        if (!response.ok) throw new Error(`API Error: ${response.status}`);
        return await response.json();
    },

    async post(endpoint, data) {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error(`API Error: ${response.status}`);
        return await response.json();
    },

    async delete(endpoint) {
        const response = await fetch(`${API_BASE}${endpoint}`, { method: 'DELETE' });
        if (!response.ok) throw new Error(`API Error: ${response.status}`);
        return await response.json();
    },

    streamLogs(onLog, onDone, onError) {
        const eventSource = new EventSource(`${API_BASE}/api/logs/stream`);
        
        eventSource.onmessage = (e) => onLog(e.data);
        eventSource.addEventListener('log', (e) => onLog(e.data));
        eventSource.addEventListener('done', () => {
            eventSource.close();
            onDone();
        });
        eventSource.onerror = (e) => {
            console.error('SSE Error:', e);
            if (onError) onError(e);
        };

        return eventSource;
    }
};
