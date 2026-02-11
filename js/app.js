import { updateTexts, getCurrentLang } from './i18n.js';
import { setupCustomSelects, togglePasswordVisibility, showView } from './ui.js';
import { initFoods } from './foods.js';
import { setupAuth } from './auth.js';
import { setupChat } from './chat.js';
import { initMenus } from './menus.js';

// Global Scope Exports for HTML (onclick handlers if any remain)
window.togglePasswordVisibility = togglePasswordVisibility;
window.showView = showView;

import { loadComponent } from './loader.js';

async function initApp() {
    console.log('Initializing App...');

    // 0. Load HTML Components
    await Promise.all([
        loadComponent('components/auth/auth-modal.html'),
        loadComponent('components/profile/medical-modal.html'),
        loadComponent('components/legal/terms-modal.html'),
        loadComponent('components/modals/feedback-modal.html'),
        loadComponent('components/modals/food-modal.html'),
        loadComponent('components/chat/chat-widget.html'),
        loadComponent('components/menus/menus-section.html', '#app-views')
    ]);

    // 1. I18n
    // Initial language setup
    updateTexts();

    // Listen for language changes from Custom Select
    document.addEventListener('languageChanged', (e) => {
        localStorage.setItem('language', e.detail);
        updateTexts();
    });

    // 2. UI Components
    setupCustomSelects();

    // 3. Auth
    setupAuth();

    // 4. Foods Logic (Grid, Modals)
    await initFoods();

    // 5. Chat
    setupChat();

    // 5.1 Menus
    await initMenus();

    // 6. Global Event Listeners (like specific Date inputs)
    const todayStr = new Date().toISOString().split('T')[0];
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => input.max = todayStr);

    // 7. Initial View
    showView('view-home');

    console.log('App Initialized');
}

// Run Init
document.addEventListener('DOMContentLoaded', initApp);
