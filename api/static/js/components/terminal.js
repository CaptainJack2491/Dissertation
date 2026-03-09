/**
 * terminal.js - Log rendering logic
 */
import { ui } from '../ui.js';

let autoScroll = true;

export const terminal = {
    init() {
        const { clearLogsBtn, scrollLockBtn } = ui.elements;
        
        clearLogsBtn.addEventListener('click', () => this.clear());
        
        scrollLockBtn.addEventListener('click', () => {
            autoScroll = !autoScroll;
            scrollLockBtn.classList.toggle('active', autoScroll);
        });
    },

    append(message) {
        const { logsContainer } = ui.elements;
        const line = document.createElement('div');
        line.className = 'terminal-line';

        // High-speed parsing for log levels
        if (message.includes('[ERROR]')) line.classList.add('error');
        else if (message.includes('[WARN]')) line.classList.add('warning');
        else if (message.includes('[DEBUG]')) line.classList.add('muted');
        else if (message.includes('SUCCESS') || message.includes('complete')) line.classList.add('success');
        else if (message.includes('Reasoning:')) line.classList.add('reasoning');
        else line.classList.add('info');

        line.textContent = message;
        logsContainer.appendChild(line);

        if (autoScroll) {
            logsContainer.scrollTop = logsContainer.scrollHeight;
        }

        // Performance: Prune logs if they get too long (keep last 1000 lines)
        if (logsContainer.children.length > 1000) {
            logsContainer.removeChild(logsContainer.firstChild);
        }
    },

    clear() {
        ui.elements.logsContainer.innerHTML = '<div class="terminal-line muted">Logs cleared.</div>';
    }
};
