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
let menusListContainer, newMenuBtn, creationForm, menuNameInput, menuPublicToggle, privacyStatusText, menuCreatorInfo, menuItemsContainer, menuTotalsContainer, saveMenuBtn, cancelMenuBtn;
let foodSearchInput, foodSearchResults, toastContainer, menuListSearch;

function setupDOM() {
    menusListContainer = document.getElementById('menus-list');
    newMenuBtn = document.getElementById('new-menu-btn');
    creationForm = document.getElementById('menu-creation-form');
    menuNameInput = document.getElementById('menu-name-meta');
    menuPublicToggle = document.getElementById('menu-public-toggle');
    privacyStatusText = document.getElementById('privacy-status-text');
    menuCreatorInfo = document.getElementById('menu-creator-info');
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
        if (menuCreatorInfo) menuCreatorInfo.classList.add('hidden');
        renderCurrentMenuItems();
        toggleCreation(true);
    });
    if (cancelMenuBtn) cancelMenuBtn.addEventListener('click', () => toggleCreation(false));
    if (saveMenuBtn) saveMenuBtn.addEventListener('click', handleSaveMenu);
    const builderDiscovery = document.getElementById('builder-discovery');
    const resultsContainer = document.getElementById('food-results-container-menu');
    const backBtn = document.getElementById('back-to-discovery');

    if (foodSearchInput) {
        foodSearchInput.addEventListener('input', handleFoodSearch);
    }

    if (backBtn) {
        backBtn.addEventListener('click', () => {
            if (foodSearchInput) foodSearchInput.value = '';
            if (foodSearchResults) foodSearchResults.innerHTML = '';
            if (resultsContainer) resultsContainer.classList.add('hidden');
            if (builderDiscovery) builderDiscovery.classList.remove('hidden');
        });
    }

    // Quick Category listeners
    const quickCatBtns = document.querySelectorAll('.quick-cat-btn');
    quickCatBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const cat = btn.getAttribute('data-cat');
            const label = btn.querySelector('label')?.textContent || cat;
            handleCategorySearch(cat, label);
        });
    });
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
            <div class="menu-card-meta">
                <div class="meta-row main-meta">
                    <div class="meta-item">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"></path>
                            <path d="M3 6h18"></path>
                            <path d="M16 10a4 4 0 0 1-8 0"></path>
                        </svg>
                        <span>${menu.items.length} ${t.ingredients || 'alimentos'}</span>
                    </div>
                    <div class="meta-item like-btn ${menu.user_liked ? 'liked' : ''}" data-id="${menu.id}">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="${menu.user_liked ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"></path>
                        </svg>
                        <span class="like-count">${menu.likes_count || 0}</span>
                    </div>
                </div>
                <div class="meta-row second-meta">
                    <div class="meta-item creator">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path>
                            <circle cx="12" cy="7" r="4"></circle>
                        </svg>
                        <span>${menu.creator_name || 'Desconocido'}</span>
                    </div>
                </div>
            </div>
            <div class="menu-actions">
                ${isOwner ? `
                    <button class="btn-delete-icon delete-menu" data-id="${menu.id}" title="${t.deleteMenu || 'Eliminar'}">
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M3 6h18"></path>
                            <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
                            <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
                        </svg>
                    </button>
                ` : `<span class="read-only-badge">${t.readOnly || 'Solo lectura'}</span>`}
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

        const likeBtn = card.querySelector('.like-btn');
        if (likeBtn) {
            likeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                handleToggleLike(menu.id);
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
        user_id: menu.user_id,
        items: menu.items.map(it => {
            const foodName = it.names ? (it.names[lang] || it.names['es'] || it.name) : it.name;
            return {
                food_id: it.food_id,
                food_data: {
                    id: it.food_id,
                    name: foodName,
                    names: it.names,
                    image: it.image,
                    unit: it.unit || 'g',
                    category: it.category || '',
                    nutrients: it.nutrients || {},
                    vitamins: it.vitamins || {}
                },
                quantity: it.quantity,
                meal_type: it.meal_type
            };
        })
    };

    toggleCreation(true);

    menuNameInput.value = menu.name;
    menuNameInput.readOnly = !isOwner; // Disable editing name

    if (menuPublicToggle) {
        menuPublicToggle.checked = menu.is_public === 1;
        menuPublicToggle.disabled = !isOwner; // Disable toggle
        updatePrivacyText();
    }

    // Display creator info
    if (menuCreatorInfo) {
        if (menu.creator_name) {
            menuCreatorInfo.textContent = translations[lang].createdBy.replace('{name}', menu.creator_name);
            menuCreatorInfo.classList.remove('hidden');
        } else {
            menuCreatorInfo.classList.add('hidden');
        }
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
    const builderDiscovery = document.getElementById('builder-discovery');
    const resultsContainer = document.getElementById('food-results-container-menu');
    const resultsTitle = document.getElementById('results-title');

    if (query.length < 2) {
        foodSearchResults.innerHTML = '';
        if (resultsContainer) resultsContainer.classList.add('hidden');
        if (builderDiscovery) builderDiscovery.classList.remove('hidden');
        return;
    }

    // Hide discovery when searching
    if (builderDiscovery) builderDiscovery.classList.add('hidden');
    if (resultsContainer) {
        resultsContainer.classList.remove('hidden');
        if (resultsTitle) resultsTitle.textContent = translations[getCurrentLang()].results || 'Resultados';
    }

    const lang = getCurrentLang();
    const normalizedQuery = normalizeText(query);
    const matches = foodDatabase.filter(food => {
        const name = food.names[lang] || food.name;
        return normalizeText(name).includes(normalizedQuery);
    }).slice(0, 15);

    renderSearchResults(matches);
}

function handleCategorySearch(category, label) {
    const builderDiscovery = document.getElementById('builder-discovery');
    const resultsContainer = document.getElementById('food-results-container-menu');
    const resultsTitle = document.getElementById('results-title');

    if (builderDiscovery) builderDiscovery.classList.add('hidden');
    if (resultsContainer) {
        resultsContainer.classList.remove('hidden');
        if (resultsTitle) resultsTitle.textContent = label;
    }

    foodSearchInput.value = ''; // Clear search text

    // Use .includes because food.category can be a comma-separated list
    const matches = foodDatabase.filter(food => {
        if (!food.category) return false;
        const cats = food.category.split(',');
        return cats.includes(category);
    }).slice(0, 15);

    renderSearchResults(matches);
}

function renderSearchResults(matches) {
    const lang = getCurrentLang();
    foodSearchResults.innerHTML = '';

    if (matches.length === 0) {
        foodSearchResults.innerHTML = `<p class="no-results-mini">${translations[lang].noMatches || 'No hay resultados'}</p>`;
        return;
    }

    matches.forEach(food => {
        const card = document.createElement('div');
        card.className = 'food-builder-card';
        const icon = getCategoryIcon(food.category);

        card.innerHTML = `
            <span class="food-icon">${icon}</span>
            <span class="food-name">${food.names[lang] || food.name}</span>
        `;
        card.addEventListener('click', () => addFoodToMenu(food));
        foodSearchResults.appendChild(card);
    });
}

function getCategoryIcon(category) {
    if (!category) return '🥗';
    const cats = category.split(',').map(c => c.trim().toLowerCase());

    const icons = {
        'fruits': '🍎',
        'fruits_spec': '🍎',
        'veg': '🥦',
        'vegetables': '🥦',
        'dairy': '🥛',
        'proteins': '🍗',
        'legumes_nuts_group': '🫘',
        'legumes_spec': '🫘',
        'nuts_spec': '🥜',
        'carbs': '🍞',
        'fats': '🧈',
        'sweets': '🍩',
        'drinks': '🥤',
        'tubers_spec': '🥔'
    };

    // Find first matching category
    for (let c of cats) {
        if (icons[c]) return icons[c];
    }
    return '🥗';
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

    // Check if food already exists in menu to increment quantity instead of duplicating row
    const existingItem = currentMenu.items.find(it => it.food_id === food.id);

    if (existingItem) {
        existingItem.quantity = (parseFloat(existingItem.quantity) || 0) + 100;
        const unit = food.unit || 'g';
        showToast(`${translations[getCurrentLang()].foodAdded || "Alimento añadido"} (+100${unit})`, "success");
    } else {
        currentMenu.items.push({
            food_id: food.id,
            food_data: food,
            quantity: 100,
            meal_type: 'generic'
        });
        showToast(translations[getCurrentLang()].foodAdded || "Alimento añadido", "success");
    }

    renderCurrentMenuItems();
}

function renderCurrentMenuItems() {
    if (!menuItemsContainer) return;

    menuItemsContainer.innerHTML = '';

    const lang = getCurrentLang();
    const t = translations[lang] || translations['es'];

    if (currentMenu.items.length === 0) {
        menuItemsContainer.innerHTML = `
            <div class="empty-selection-placeholder">
                <div class="placeholder-icon">🍲</div>
                <p>${t.emptySelection || 'Añade alimentos para empezar a calcular'}</p>
            </div>
        `;
        calculateTotals();
        return;
    }

    const user = JSON.parse(localStorage.getItem('user'));
    const userId = user ? (user.userId || user.id) : null;
    const isOwner = !editingMenuId || currentMenu.user_id === userId;

    currentMenu.items.forEach((item, index) => {
        const food = item.food_data;
        const icon = getCategoryIcon(food.category);

        const row = document.createElement('div');
        row.className = 'builder-item-row';
        row.innerHTML = `
            <span class="item-row-icon">${icon}</span>
            <span class="item-row-name">${food.names ? (food.names[lang] || food.name) : food.name}</span>
            <div class="item-row-controls">
                <input type="number" data-index="${index}" 
                       value="${item.quantity}" min="1" step="1" ${isOwner ? '' : 'readonly'}>
                <span>${food.unit || 'g'}</span>
            </div>
            ${isOwner ? `<button class="btn-remove-item" data-index="${index}">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>` : ''}
        `;

        const qInput = row.querySelector('input');
        if (qInput && isOwner) {
            qInput.addEventListener('input', (e) => {
                const val = parseFloat(e.target.value) || 0;
                currentMenu.items[index].quantity = val;
                calculateTotals();
            });
        }

        const rmBtn = row.querySelector('.btn-remove-item');
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
    let totals = {
        // Macros & Minerals
        protein: 0, sugar: 0, fat: 0, potassium: 0, phosphorus: 0, salt: 0, calcium: 0,
        magnesium: 0, iron: 0, copper: 0, sulfur: 0, chlorine: 0,
        // Vitamins
        vitamin_k: 0, vitamin_a: 0, vitamin_c: 0, vitamin_e: 0,
        vitamin_b1: 0, vitamin_b3: 0, vitamin_b5: 0, vitamin_b6: 0, vitamin_b9: 0
    };

    currentMenu.items.forEach(item => {
        const food = item.food_data;
        const ratio = item.quantity / 100;

        // Nutrients level 1
        const n = food.nutrients || {};
        const nutrientsKeys = ['protein', 'sugar', 'fat', 'potassium', 'phosphorus', 'salt', 'calcium', 'magnesium', 'iron', 'copper', 'sulfur', 'chlorine'];
        nutrientsKeys.forEach(k => {
            if (n[k] !== undefined) totals[k] += n[k] * ratio;
        });

        // Vitamins level
        const v = food.vitamins || {};
        const vitaminsKeys = ['vitamin_k', 'vitamin_a', 'vitamin_c', 'vitamin_e', 'vitamin_b1', 'vitamin_b3', 'vitamin_b5', 'vitamin_b6', 'vitamin_b9'];
        vitaminsKeys.forEach(k => {
            if (v[k] !== undefined) totals[k] += v[k] * ratio;
        });
    });
    updateTotalsUI(totals);
}

function updateTotalsUI(totals) {
    const user = JSON.parse(localStorage.getItem('user'));
    const lang = getCurrentLang();
    const t = translations[lang] || translations['es'];

    if (!menuTotalsContainer) return;

    menuTotalsContainer.innerHTML = '';

    // Category 1: Info Nutricional
    const mainSection = document.createElement('div');
    mainSection.className = 'nutritional-info';
    mainSection.innerHTML = `
        <h3 onclick="toggleSection('builder-nutrients-grid', this)" style="cursor: pointer; display: flex; justify-content: space-between; align-items: center;">
            <span data-i18n="nutritionalInfo">${t.nutritionalInfo || 'Información Nutricional'}</span>
            <span class="toggle-icon">▼</span>
        </h3>
        <div id="builder-nutrients-grid" class="info-grid"></div>
    `;
    const mainGrid = mainSection.querySelector('.info-grid');
    const mainKeys = ['protein', 'sugar', 'fat', 'potassium', 'phosphorus', 'salt', 'calcium', 'magnesium', 'iron', 'copper', 'sulfur', 'chlorine'];

    mainKeys.forEach(key => {
        const val = totals[key] || 0;
        let formattedVal;
        if (['salt', 'protein', 'sugar', 'fat'].includes(key)) formattedVal = val.toFixed(2);
        else if (['iron', 'copper'].includes(key)) formattedVal = val.toFixed(1);
        else formattedVal = val.toFixed(0);

        let unit = 'mg';
        if (['protein', 'sugar', 'fat', 'salt'].includes(key)) unit = 'g';

        const colorClass = user && ['protein', 'potassium', 'phosphorus', 'salt', 'calcium'].includes(key)
            ? Nephrologist.getTrafficColor(key, formattedVal, user) : '';

        const item = document.createElement('div');
        item.className = `info-item ${colorClass}`;
        item.innerHTML = `
            <span class="label">${t[key] || key.replace('_', ' ')}</span>
            <span class="value">${formattedVal}${unit}</span>
        `;
        mainGrid.appendChild(item);
    });

    // Category 2: Vitamins
    const vitSection = document.createElement('div');
    vitSection.className = 'nutritional-info';
    vitSection.innerHTML = `
        <h3 onclick="toggleSection('builder-vitamins-grid', this)" style="cursor: pointer; display: flex; justify-content: space-between; align-items: center;">
            <span data-i18n="vitamins">${t.vitamins || 'Vitaminas'}</span>
            <span class="toggle-icon">▼</span>
        </h3>
        <div id="builder-vitamins-grid" class="info-grid"></div>
    `;
    const vitGrid = vitSection.querySelector('.info-grid');
    const vitKeys = ['vitamin_k', 'vitamin_a', 'vitamin_c', 'vitamin_e', 'vitamin_b1', 'vitamin_b3', 'vitamin_b5', 'vitamin_b6', 'vitamin_b9'];

    vitKeys.forEach(key => {
        const val = totals[key] || 0;
        let formattedVal = key.includes('b') ? val.toFixed(2) : (key === 'vitamin_k' || key === 'vitamin_a' || key === 'vitamin_b9' ? val.toFixed(0) : val.toFixed(1));
        let unit = (key === 'vitamin_k' || key === 'vitamin_a' || key === 'vitamin_b9') ? 'ug' : 'mg';

        const item = document.createElement('div');
        item.className = 'info-item';
        item.innerHTML = `
            <span class="label">${t[key] || key.replace('_', ' ')}</span>
            <span class="value">${formattedVal}${unit}</span>
        `;
        vitGrid.appendChild(item);
    });

    menuTotalsContainer.appendChild(mainSection);
    menuTotalsContainer.appendChild(vitSection);

    // Update count badge
    const countBadge = document.getElementById('selected-count-badge');
    if (countBadge) {
        countBadge.textContent = currentMenu.items.length;
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

async function handleToggleLike(menuId) {
    const user = JSON.parse(localStorage.getItem('user'));
    if (!user) {
        // Redirigir o mostrar modal de login - de momento toast
        if (typeof showToast === 'function') {
            showToast('Inicia sesión para dar me gusta', 'error');
        }
        return;
    }

    try {
        const response = await fetch('/api/toggle_like', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: user.userId || user.id,
                menu_id: menuId
            })
        });

        const data = await response.json();
        if (data.status === 'success') {
            loadMenus(); // Recargar para actualizar contadores
        }
    } catch (e) {
        console.error('Like toggle error:', e);
    }
}
