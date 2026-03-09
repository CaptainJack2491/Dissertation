import { ui } from './ui.js';
import { results } from './components/results.js';

async function init() {
    console.log('Initializing AI Reasoning Dashboard...');
    
    await results.init();
    
    // Init UI behaviors
    ui.initTabs((tabId) => {
        // We could lazy load data here, but for now everything triggers on file/filter change
    });
}

function start() {
    init().catch(err => {
        console.error("Initialization error:", err);
        alert(`Dashboard Failed to Load: ${err.message}`);
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
} else {
    start();
}