import { fetchFoods, sendFeedback } from './api.js';
import { translations, getCurrentLang } from './i18n.js';

// Global State for Module
let foodDatabase = [];
let currentFood = null;
let activeCategory = 'all';

// DOM Elements
// DOM Elements
let gridContainer, modal, closeModalBtn, gramsInput, searchInput, categoryTabsContainer;
let mImg, mName, valProtein, valSugar, valFat, valPotassium, valPhosphorus, valSalt, valCalcium;

// Feedback Elements
let feedbackBtn, feedbackModal, closeFeedbackBtn, cancelFeedbackBtn, sendFeedbackBtn, feedbackText;

function setupDOM() {
    gridContainer = document.getElementById('food-grid');
    modal = document.getElementById('food-modal');
    // Select close button specifically within the modal to avoid conflicts
    closeModalBtn = modal ? modal.querySelector('.close-modal') : null;
    gramsInput = document.getElementById('grams-input');
    searchInput = document.getElementById('search-input');
    categoryTabsContainer = document.getElementById('category-tabs');

    if (modal) {
        mImg = modal.querySelector('#modal-img');
        mName = modal.querySelector('#modal-name');
        valProtein = modal.querySelector('#val-protein');
        valSugar = modal.querySelector('#val-sugar');
        valFat = modal.querySelector('#val-fat');
        valPotassium = modal.querySelector('#val-potassium');
        valPhosphorus = modal.querySelector('#val-phosphorus');
        valSalt = modal.querySelector('#val-salt');
        valCalcium = modal.querySelector('#val-calcium');
    }

    // Feedback Elements
    feedbackBtn = document.getElementById('feedback-btn');
    feedbackModal = document.getElementById('feedback-modal');
    closeFeedbackBtn = document.getElementById('close-feedback');
    cancelFeedbackBtn = document.getElementById('cancel-feedback');
    sendFeedbackBtn = document.getElementById('send-feedback');
    feedbackText = document.getElementById('feedback-text');
}

// Configuration
const categories = [
    { id: 'all', key: 'catAll', label: 'Todo' },
    { id: 'dairy', key: 'catDairy', label: 'Leche y derivados' },
    { id: 'proteins', key: 'catProteins', label: 'Carnes, pescados y huevos' },
    { id: 'legumes_nuts_group', key: 'catLegumesNutsGroup', label: 'Legumbres y frutos secos' },
    { id: 'vegetables', key: 'catVeg', label: 'Verduras y hortalizas' },
    { id: 'fruits', key: 'catFruits', label: 'Frutas' },
    { id: 'carbs', key: 'catCarbs', label: 'Cereales, pasta, pan' },
    { id: 'fats', key: 'catFats', label: 'Grasas y aceites' },
    { id: 'sweets', key: 'catSweets', label: 'Azúcares y dulces' },
    { id: 'legumes_spec', key: 'catLegumesSpec', label: 'Legumbres (específico)' },
    { id: 'nuts_spec', key: 'catNutsSpec', label: 'Frutos secos (específico)' },
    { id: 'tubers_spec', key: 'catTubersSpec', label: 'Tubérculos (específico)' },
    { id: 'drinks', key: 'catDrinks', label: 'Bebidas' }
];

export class Nephrologist {
    static getTrafficColor(nutrient, value, userProfile) {
        if (!userProfile) return '';

        const v = parseFloat(value);
        if (isNaN(v)) return '';

        const hasInsufficiency = userProfile.has_insufficiency === '1' || userProfile.has_insufficiency === 1 || userProfile.has_insufficiency === true || userProfile.has_insufficiency === 'true';

        if (!hasInsufficiency) {
            const healthyLimits = {
                potassium: { green: 1000, yellow: 2000 },
                phosphorus: { green: 500, yellow: 1000 },
                protein: { green: 40, yellow: 80 },
                salt: { green: 1.5, yellow: 3.0 },
                calcium: { green: 400, yellow: 800 }
            };
            if (v <= healthyLimits[nutrient].green) return 'traffic-green';
            if (v <= healthyLimits[nutrient].yellow) return 'traffic-yellow';
            return 'traffic-red';
        }

        let limits = {
            potassium: { green: 200, yellow: 400 },
            phosphorus: { green: 150, yellow: 300 },
            protein: { green: 10, yellow: 25 },
            salt: { green: 0.5, yellow: 1.2 },
            calcium: { green: 100, yellow: 300 }
        };

        const stage = userProfile.kidney_stage;
        const treatment = userProfile.treatment_type;

        if (['1', '2', '3a'].includes(stage)) {
            limits.potassium = { green: 400, yellow: 800 };
            limits.phosphorus = { green: 300, yellow: 600 };
            limits.protein = { green: 20, yellow: 40 };
        }

        if (['3b', '4'].includes(stage) && treatment !== 'dialysis') {
            limits.potassium = { green: 200, yellow: 400 };
            limits.phosphorus = { green: 150, yellow: 300 };
            limits.protein = { green: 10, yellow: 25 };
            limits.salt = { green: 0.5, yellow: 1.0 };
        }

        if (stage === '5' && treatment !== 'dialysis') {
            limits.potassium = { green: 150, yellow: 350 };
            limits.phosphorus = { green: 120, yellow: 250 };
            limits.protein = { green: 8, yellow: 20 };
            limits.salt = { green: 0.4, yellow: 0.8 };
        }

        if (treatment === 'dialysis') {
            limits.potassium = { green: 100, yellow: 250 };
            limits.phosphorus = { green: 100, yellow: 250 };
            limits.protein = { green: 60, yellow: 100 };
        }

        if (treatment === 'transplant' && ['1', '2', '3a'].includes(stage)) {
            limits.potassium = { green: 800, yellow: 1500 };
            limits.phosphorus = { green: 400, yellow: 800 };
            limits.protein = { green: 30, yellow: 60 };
        }

        if (v <= limits[nutrient].green) return 'traffic-green';
        if (v <= limits[nutrient].yellow) return 'traffic-yellow';
        return 'traffic-red';
    }
}

export async function initFoods() {
    try {
        setupDOM(); // Initialize DOM references after injection
        foodDatabase = await fetchFoods();

        // Setup Listeners
        if (closeModalBtn) closeModalBtn.addEventListener('click', closeModal);
        window.addEventListener('click', (e) => {
            if (e.target === modal) closeModal();
            if (e.target === feedbackModal) closeFeedback();
        });

        if (gramsInput) {
            gramsInput.addEventListener('input', (e) => {
                updateNutrients(parseFloat(e.target.value) || 0);
            });
        }

        if (searchInput) {
            searchInput.addEventListener('input', () => filterAndRender());
        }

        if (feedbackBtn) feedbackBtn.addEventListener('click', openFeedback);
        if (closeFeedbackBtn) closeFeedbackBtn.addEventListener('click', closeFeedback);
        if (cancelFeedbackBtn) cancelFeedbackBtn.addEventListener('click', closeFeedback);
        if (sendFeedbackBtn) sendFeedbackBtn.addEventListener('click', handleSendFeedback);

        renderTabs();
        filterAndRender();

    } catch (error) {
        console.error("Error init foods:", error);
    }
}

function renderTabs() {
    if (!categoryTabsContainer) return;
    categoryTabsContainer.innerHTML = '';
    categories.forEach(cat => {
        const btn = document.createElement('button');
        btn.className = `category-tab ${cat.id === activeCategory ? 'active' : ''}`;
        const currentLang = getCurrentLang();
        const t = translations[currentLang] || translations['es'];
        btn.textContent = t[cat.key] || cat.label;
        btn.setAttribute('data-i18n', cat.key);
        btn.setAttribute('data-cat', cat.id);

        btn.addEventListener('click', () => {
            activeCategory = cat.id;
            document.querySelectorAll('.category-tab').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            filterAndRender();
        });

        categoryTabsContainer.appendChild(btn);
    });
}

function normalizeText(text) {
    if (!text) return "";
    return text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}

function getFoodName(food) {
    const lang = getCurrentLang();
    if (food.names && food.names[lang]) {
        return food.names[lang];
    }
    return food.name;
}

export function filterAndRender() {
    if (!gridContainer) return;
    const searchTerm = normalizeText(searchInput ? searchInput.value.trim() : '');

    const filtered = foodDatabase.filter(food => {
        const name = getFoodName(food);
        const matchesText = normalizeText(name).includes(searchTerm);
        const matchesCategory = activeCategory === 'all' ||
            food.category === activeCategory ||
            (food.category && food.category.split(',').map(c => c.trim()).includes(activeCategory));
        return matchesText && matchesCategory;
    });

    renderGrid(filtered);
}

function renderGrid(foodsToRender) {
    gridContainer.innerHTML = '';
    if (foodsToRender.length === 0) {
        gridContainer.innerHTML = '<p style="text-align: center; width: 100%; color: #888;">No se encontraron alimentos.</p>';
        return;
    }

    foodsToRender.forEach(food => {
        const card = document.createElement('div');
        card.className = 'food-card';
        card.innerHTML = `
            <img src="${food.image}" alt="${getFoodName(food)}">
            <h3>${getFoodName(food)}</h3>
        `;
        card.addEventListener('click', () => openModal(food));
        gridContainer.appendChild(card);
    });
}

export function openModal(food) {
    currentFood = food;
    if (gramsInput) {
        gramsInput.value = '';
        gramsInput.focus();
    }
    if (mImg) mImg.src = food.image;
    if (mName) mName.textContent = getFoodName(food);
    updateNutrients(0);
    modal.classList.add('active');
    document.body.style.overflow = 'hidden'; // Lock body scroll
}

export function closeModal() {
    modal.classList.remove('active');
    document.body.style.overflow = ''; // Unlock body scroll
    currentFood = null;
}

function updateNutrients(grams) {
    if (!currentFood) return;
    const ratio = grams / 100;
    const n = currentFood.nutrients;

    const vProteins = (n.protein * ratio).toFixed(1);
    const vSugar = (n.sugar * ratio).toFixed(1);
    const vFat = (n.fat * ratio).toFixed(1);
    const vPotassium = (n.potassium * ratio).toFixed(0);
    const vPhosphorus = (n.phosphorus * ratio).toFixed(0);
    const vSalt = (n.salt * ratio).toFixed(2);
    const vCalcium = (n.calcium * ratio).toFixed(0);

    if (valProtein) valProtein.textContent = vProteins + 'g';
    if (valSugar) valSugar.textContent = vSugar + 'g';
    if (valFat) valFat.textContent = vFat + 'g';
    if (valPotassium) valPotassium.textContent = vPotassium + 'mg';
    if (valPhosphorus) valPhosphorus.textContent = vPhosphorus + 'mg';
    if (valSalt) valSalt.textContent = vSalt + 'g';
    if (valCalcium) valCalcium.textContent = vCalcium + 'mg';

    const user = localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')) : null;

    [valProtein, valPotassium, valPhosphorus, valSalt, valCalcium].forEach(el => {
        if (el) el.classList.remove('traffic-green', 'traffic-yellow', 'traffic-red');
    });

    if (user) {
        if (valProtein) valProtein.classList.add(Nephrologist.getTrafficColor('protein', vProteins, user));
        if (valPotassium) valPotassium.classList.add(Nephrologist.getTrafficColor('potassium', vPotassium, user));
        if (valPhosphorus) valPhosphorus.classList.add(Nephrologist.getTrafficColor('phosphorus', vPhosphorus, user));
        if (valSalt) valSalt.classList.add(Nephrologist.getTrafficColor('salt', vSalt, user));
        if (valCalcium) valCalcium.classList.add(Nephrologist.getTrafficColor('calcium', vCalcium, user));
    }
}

function openFeedback() {
    feedbackModal.classList.add('active');
    if (feedbackText) feedbackText.focus();
}

function closeFeedback() {
    feedbackModal.classList.remove('active');
}

async function handleSendFeedback() {
    const text = feedbackText.value.trim();
    if (!text) return;
    const lang = getCurrentLang();

    sendFeedbackBtn.textContent = "...";

    try {
        const res = await sendFeedback(text);
        if (res.ok) {
            sendFeedbackBtn.textContent = (lang === 'es' ? '¡Enviado!' : 'Sent!');
            sendFeedbackBtn.style.background = '#10b981';

            setTimeout(() => {
                feedbackText.value = '';
                closeFeedback();
                setTimeout(() => {
                    sendFeedbackBtn.textContent = translations[lang].send;
                    sendFeedbackBtn.style.background = '';
                }, 500);
            }, 1000);
        } else {
            throw new Error('Server error');
        }
    } catch (error) {
        console.error("Error enviando feedback:", error);
        sendFeedbackBtn.textContent = "Error";
        setTimeout(() => {
            sendFeedbackBtn.textContent = translations[lang].send;
        }, 2000);
    }
}
