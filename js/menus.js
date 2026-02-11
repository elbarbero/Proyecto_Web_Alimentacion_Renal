import { getCurrentLang, translations } from './i18n.js';
import { fetchFoods } from './api.js';
import { Nephrologist, normalizeText } from './foods.js';
import { showView, showConfirm } from './ui.js';

let menus = [];
let foodDatabase = [];
let currentMenu = {
    name: '',
    items: []
};
let isCreating = false;
let editingMenuId = null;

// DOM Elements
let menusListContainer, newMenuBtn, creationForm, menuNameInput, menuPublicToggle, privacyStatusText, menuItemsContainer, menuTotalsContainer, saveMenuBtn, cancelMenuBtn;
let foodSearchInput, foodSearchResults, toastContainer, menuListSearch;

function setupDOM() {
    menusListContainer = document.getElementById('menus-list');
    newMenuBtn = document.getElementById('new-menu-btn');
    creationForm = document.getElementById('menu-creation-form');
    menuNameInput = document.getElementById('menu-name-meta');
    menuPublicToggle = document.getElementById('menu-public-toggle');
    privacyStatusText = document.getElementById('privacy-status-text');
    menuItemsContainer = document.getElementById('selected-items');
    menuTotalsContainer = document.getElementById('menu-totals');
    saveMenuBtn = document.getElementById('save-menu-btn');
    cancelMenuBtn = document.getElementById('cancel-menu-btn');
    foodSearchInput = document.getElementById('food-search-menu');
    foodSearchResults = document.getElementById('food-results-menu');
    toastContainer = document.getElementById('toast-container');
    menuListSearch = document.getElementById('menu-list-search');
}

export async function initMenus() {
    setupDOM();

    // Attach listeners immediately to avoid race conditions if fetch is slow
    if (newMenuBtn) newMenuBtn.addEventListener('click', () => {
        editingMenuId = null;
        currentMenu = { name: '', items: [] };
        menuNameInput.value = '';
        renderCurrentMenuItems();
        toggleCreation(true);
    });
    if (cancelMenuBtn) cancelMenuBtn.addEventListener('click', () => toggleCreation(false));
    if (saveMenuBtn) saveMenuBtn.addEventListener('click', handleSaveMenu);
    if (foodSearchInput) foodSearchInput.addEventListener('input', handleFoodSearch);
    if (menuPublicToggle) {
        menuPublicToggle.addEventListener('change', updatePrivacyText);
    }
    if (menuListSearch) {
        menuListSearch.addEventListener('input', () => renderMenus());
    }

    // Load data in background
    foodDatabase = await fetchFoods();
    await loadMenus();

    // Listen for language changes to update UI without reload
    document.addEventListener('languageChanged', () => {
        renderMenus();
        if (isCreating) {
            renderCurrentMenuItems();
        }
    });

    // Listen for view changes to handle internal sub-views
    document.addEventListener('viewChanged', (e) => {
        const { viewId } = e.detail;
        if (viewId === 'view-menus') {
            isCreating = false;
            if (creationForm) creationForm.classList.add('hidden');
            if (newMenuBtn) newMenuBtn.classList.remove('hidden');
            if (menusListContainer) menusListContainer.classList.remove('hidden');
            editingMenuId = null;
            if (menuNameInput) menuNameInput.readOnly = false;
            if (menuPublicToggle) menuPublicToggle.disabled = false;
            if (saveMenuBtn) saveMenuBtn.style.display = 'block';
            const searchCol = document.querySelector('.search-column');
            if (searchCol) searchCol.style.display = 'block';
            const searchListContainer = document.getElementById('menus-search-container');
            if (searchListContainer) searchListContainer.classList.remove('hidden');
        } else if (viewId === 'view-menus-form') {
            isCreating = true;
            if (creationForm) creationForm.classList.remove('hidden');
            if (newMenuBtn) newMenuBtn.classList.add('hidden');
            if (menusListContainer) menusListContainer.classList.add('hidden');
            const searchListContainer = document.getElementById('menus-search-container');
            if (searchListContainer) searchListContainer.classList.add('hidden');
            updatePrivacyText();
        }
    });
}

async function loadMenus() {
    const user = JSON.parse(localStorage.getItem('user'));
    if (!user) return;
    const userId = user.userId || user.id;
    if (!userId) return;

    try {
        const res = await fetch(`/api/menus?user_id=${userId}`);
        menus = await res.json();
        renderMenus();
    } catch (e) {
        console.error("Error loading menus:", e);
    }
}

function renderMenus() {
    if (!menusListContainer) return;

    const searchTerm = menuListSearch ? normalizeText(menuListSearch.value) : '';
    const filteredMenus = menus.filter(m => normalizeText(m.name).includes(searchTerm));

    menusListContainer.innerHTML = '';

    const lang = getCurrentLang();
    const t = translations[lang] || translations['es'];

    if (filteredMenus.length === 0) {
        const msg = searchTerm ? (t.noMatches || 'No se encontraron menús.') : (t.noMenus || 'No tienes menús guardados.');
        menusListContainer.innerHTML = `<p class="empty-msg">${msg}</p>`;
        return;
    }

    const user = JSON.parse(localStorage.getItem('user'));

    filteredMenus.forEach(menu => {
        const isOwner = user && menu.user_id === (user.userId || user.id);
        const card = document.createElement('div');
        card.className = `menu-summary-card glass-card ${menu.is_public ? 'is-public' : ''}`;

        const privacyText = menu.is_public ?
            (t.public || '🌍 Público') :
            (t.private || '🔒 Privado');

        card.innerHTML = `
            <div class="menu-card-header">
                <h3>${menu.name}</h3>
                <span class="privacy-badge">${privacyText}</span>
            </div>
            <p>${menu.items.length} alimentos</p>
            <div class="menu-actions">
                ${isOwner ? `<button class="btn-small delete-menu" data-id="${menu.id}">${t.deleteMenu || 'Eliminar'}</button>` : `<span class="read-only">${t.readOnly || 'Solo lectura'}</span>`}
            </div>
        `;

        card.addEventListener('click', () => openMenu(menu));

        const delBtn = card.querySelector('.delete-menu');
        if (delBtn) {
            delBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                handleDeleteMenu(menu.id);
            });
        }
        menusListContainer.appendChild(card);
    });
}

function openMenu(menu) {
    const user = JSON.parse(localStorage.getItem('user'));
    const userId = user ? (user.userId || user.id) : null;
    const isOwner = userId && menu.user_id === userId;

    editingMenuId = menu.id;
    const lang = getCurrentLang();
    currentMenu = {
        name: menu.name,
        user_id: menu.user_id, // Store owner id
        items: menu.items.map(it => ({
            food_id: it.food_id,
            food_data: {
                name: it.names[lang] || it.name,
                names: it.names,
                nutrients: it.nutrients
            },
            quantity: it.quantity,
            meal_type: it.meal_type
        }))
    };

    toggleCreation(true);

    menuNameInput.value = menu.name;
    menuNameInput.readOnly = !isOwner; // Disable editing name

    if (menuPublicToggle) {
        menuPublicToggle.checked = menu.is_public === 1;
        menuPublicToggle.disabled = !isOwner; // Disable toggle
        updatePrivacyText();
    }

    // Hide/Show Save button
    if (saveMenuBtn) {
        saveMenuBtn.style.display = isOwner ? 'block' : 'none';
    }

    // Hide search column if not owner
    const searchCol = document.querySelector('.search-column');
    if (searchCol) {
        searchCol.style.display = isOwner ? 'block' : 'none';
    }

    renderCurrentMenuItems();
}

function toggleCreation(show) {
    if (show) {
        showView('view-menus-form');
    } else {
        showView('view-menus');
    }
}

function handleFoodSearch() {
    const query = foodSearchInput.value.toLowerCase();
    if (query.length < 2) {
        foodSearchResults.innerHTML = '';
        return;
    }

    const lang = getCurrentLang();
    const normalizedQuery = normalizeText(query);
    const matches = foodDatabase.filter(food => {
        const name = food.names[lang] || food.name;
        return normalizeText(name).includes(normalizedQuery);
    }).slice(0, 20);

    foodSearchResults.innerHTML = '';
    matches.forEach(food => {
        const item = document.createElement('div');
        item.className = 'search-result-item';
        item.innerHTML = `
            <span>${food.names[lang] || food.name}</span>
            <span class="add-icon">+</span>
        `;
        item.addEventListener('click', () => addFoodToMenu(food));
        foodSearchResults.appendChild(item);
    });
}

function updatePrivacyText() {
    if (!menuPublicToggle || !privacyStatusText) return;
    const lang = getCurrentLang();
    const t = translations[lang] || translations['es'];

    if (menuPublicToggle.checked) {
        privacyStatusText.textContent = t.public ? t.public.replace('🌍 ', '') : 'Público';
    } else {
        privacyStatusText.textContent = t.private ? t.private.replace('🔒 ', '') : 'Privado';
    }
}

function addFoodToMenu(food) {
    const user = JSON.parse(localStorage.getItem('user'));
    const userId = user ? (user.userId || user.id) : null;
    if (editingMenuId && currentMenu.user_id !== userId) {
        return; // Security guard
    }

    currentMenu.items.push({
        food_id: food.id,
        food_data: food,
        quantity: 100,
        meal_type: 'generic'
    });

    foodSearchInput.value = '';
    foodSearchResults.innerHTML = '';
    renderCurrentMenuItems();
    showToast(translations[getCurrentLang()].foodAdded || "Alimento añadido", "success");
}

function renderCurrentMenuItems() {
    menuItemsContainer.innerHTML = '';

    const user = JSON.parse(localStorage.getItem('user'));
    const userId = user ? (user.userId || user.id) : null;
    const isOwner = !editingMenuId || currentMenu.user_id === userId;

    currentMenu.items.forEach((item, index) => {
        const food = item.food_data;
        const lang = getCurrentLang();

        const row = document.createElement('div');
        row.className = 'menu-item-row';
        row.innerHTML = `
            <div class="item-info">
                <span class="item-name">${food.names ? (food.names[lang] || food.name) : food.name}</span>
                <div class="item-quantity-wrapper">
                    <input type="number" class="item-quantity-input" data-index="${index}" 
                           value="${item.quantity}" min="1" step="1" ${isOwner ? '' : 'readonly'}>
                    <span>g</span>
                </div>
            </div>
            ${isOwner ? `<button class="btn-icon remove-item" data-index="${index}">&times;</button>` : ''}
        `;

        const qInput = row.querySelector('.item-quantity-input');
        if (qInput && isOwner) {
            qInput.addEventListener('input', (e) => {
                const val = parseFloat(e.target.value) || 0;
                currentMenu.items[index].quantity = val;
                calculateTotals();
            });
        }

        const rmBtn = row.querySelector('.remove-item');
        if (rmBtn) {
            rmBtn.addEventListener('click', () => {
                currentMenu.items.splice(index, 1);
                renderCurrentMenuItems();
            });
        }

        menuItemsContainer.appendChild(row);
    });

    calculateTotals();
}

function calculateTotals() {
    let totals = { protein: 0, potassium: 0, phosphorus: 0, salt: 0, calcium: 0 };
    currentMenu.items.forEach(item => {
        const food = item.food_data;
        const ratio = item.quantity / 100;
        for (let key in totals) {
            if (food.nutrients && food.nutrients[key]) {
                totals[key] += food.nutrients[key] * ratio;
            }
        }
    });
    updateTotalsUI(totals);
}

function updateTotalsUI(totals) {
    const user = JSON.parse(localStorage.getItem('user'));
    const lang = getCurrentLang();
    const t = translations[lang] || translations['es'];

    menuTotalsContainer.innerHTML = `<h4>${t.totalSummary || 'Resumen Nutricional Total'}</h4>`;

    for (let key in totals) {
        const val = totals[key].toFixed(key === 'salt' ? 2 : 0);
        const color = user ? Nephrologist.getTrafficColor(key, val, user) : '';
        const badge = document.createElement('div');
        badge.className = `nutrient-badge ${color}`;
        badge.innerHTML = `<strong>${key.toUpperCase()}:</strong> ${val}${key === 'salt' ? 'g' : 'mg'}`;
        menuTotalsContainer.appendChild(badge);
    }
}

async function handleSaveMenu() {
    const name = menuNameInput.value.trim();
    if (!name || currentMenu.items.length === 0) {
        showToast("Ponle un nombre y añade alimentos.", "error");
        return;
    }

    const user = JSON.parse(localStorage.getItem('user'));
    if (!user) {
        showToast("Error: No se ha podido identificar al usuario.", "error");
        return;
    }
    const userId = user.userId || user.id;

    // Security check: if editing, must be owner
    if (editingMenuId && currentMenu.user_id !== userId) {
        showToast("No tienes permiso para modificar este menú", "error");
        return;
    }
    const data = {
        user_id: userId,
        menu_id: editingMenuId,
        name: name,
        is_public: menuPublicToggle ? menuPublicToggle.checked : false,
        items: currentMenu.items.map(it => ({
            food_id: it.food_id,
            quantity: it.quantity,
            meal_type: it.meal_type
        }))
    };

    try {
        const url = editingMenuId ? '/api/update_menu' : '/api/create_menu';
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (res.ok) {
            showToast(translations[getCurrentLang()].menuSaved || "¡Menú guardado!", "success");
            if (menuPublicToggle) {
                menuPublicToggle.checked = false;
                updatePrivacyText();
            }
            menuNameInput.value = '';
            toggleCreation(false);
            loadMenus();
        } else {
            showToast("Error al guardar el menú", "error");
        }
    } catch (e) {
        console.error("Error saving menu:", e);
        showToast("Error de conexión", "error");
    }
}

async function handleDeleteMenu(id) {
    const lang = getCurrentLang();
    const t = translations[lang] || translations['es'];
    const confirmed = await showConfirm(
        t.confirmTitle || "Confirmación",
        t.deleteMenuConfirm || "¿Seguro que quieres borrar este menú?",
        "🗑️"
    );
    if (!confirmed) return;

    const user = JSON.parse(localStorage.getItem('user'));
    if (!user) return;
    const userId = user.userId || user.id;

    try {
        const res = await fetch('/api/delete_menu', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                menu_id: id,
                user_id: userId
            })
        });
        if (res.ok) {
            showToast("Menú eliminado", "success");
            loadMenus();
        } else {
            const data = await res.json();
            showToast(data.error || "Error al eliminar", "error");
        }
    } catch (e) {
        console.error("Error deleting menu:", e);
        showToast("Error de conexión", "error");
    }
}

function showToast(message, type = 'success') {
    if (!toastContainer) return;
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toastContainer.appendChild(toast);

    setTimeout(() => toast.classList.add('active'), 10);

    setTimeout(() => {
        toast.classList.remove('active');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
