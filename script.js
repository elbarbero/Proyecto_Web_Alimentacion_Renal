const translations = {
    es: {
        title: "Alimentación Renal Inteligente",
        subtitle: "Tu compañera digital para el control nutricional avanzado",
        description: "Bienvenido a la herramienta definitiva para pacientes renales. Consulta al instante los valores críticos de tus alimentos (Potasio, Fósforo, Proteínas) y toma decisiones informadas para cuidar tu salud renal con precisión milimétrica.",
        searchPlaceholder: "¿Qué vas a comer hoy? (Ej: Manzana, Pollo...)",
        amountLabel: "Cantidad (gramos)",
        nutritionalInfo: "Información Nutricional",
        protein: "Proteínas",
        sugar: "Azúcares",
        fat: "Grasas",
        potassium: "Potasio",
        phosphorus: "Fósforo",
        salt: "Sal",
        calcium: "Calcio"
    },
    en: {
        title: "Smart Renal Diet",
        subtitle: "Your digital companion for advanced nutritional control",
        description: "Welcome to the ultimate tool for kidney patients. Instantly check critical food values (Potassium, Phosphorus, Protein) and make informed decisions to care for your renal health with millimetric precision.",
        searchPlaceholder: "What are you eating today? (e.g., Apple, Chicken...)",
        amountLabel: "Amount (grams)",
        nutritionalInfo: "Nutritional Information",
        protein: "Protein",
        sugar: "Sugars",
        fat: "Fat",
        potassium: "Potassium",
        phosphorus: "Phosphorus",
        salt: "Salt",
        calcium: "Calcium"
    },
    de: {
        title: "Intelligente Nierendiät",
        subtitle: "Ihr digitaler Begleiter für fortgeschrittene Ernährungskontrolle",
        description: "Willkommen beim ultimativen Werkzeug für Nierenpatienten. Überprüfen Sie sofort kritische Lebensmittelwerte (Kalium, Phosphor, Protein) und treffen Sie fundierte Entscheidungen für Ihre Nierengesundheit.",
        searchPlaceholder: "Was essen Sie heute? (z.B. Apfel, Hühnchen...)",
        amountLabel: "Menge (Gramm)",
        nutritionalInfo: "Nährwertinformationen",
        protein: "Protein",
        sugar: "Zucker",
        fat: "Fett",
        potassium: "Kalium",
        phosphorus: "Phosphor",
        salt: "Salz",
        calcium: "Kalzium"
    },
    fr: {
        title: "Alimentation Rénale Intelligente",
        subtitle: "Votre compagnon numérique pour un contrôle nutritionnel avancé",
        description: "Bienvenue sur l'outil ultime pour les patients rénaux. Consultez instantanément les valeurs critiques (Potassium, Phosphore, Protéines) et prenez des décisions éclairées pour votre santé rénale.",
        searchPlaceholder: "Que mangez-vous aujourd'hui ? (ex: Pomme, Poulet...)",
        amountLabel: "Quantité (grammes)",
        nutritionalInfo: "Information Nutritionnelle",
        protein: "Protéines",
        sugar: "Sucres",
        fat: "Graisses",
        potassium: "Potassium",
        phosphorus: "Phosphore",
        salt: "Sel",
        calcium: "Calcium"
    },
    pt: {
        title: "Dieta Renal Inteligente",
        subtitle: "Seu companheiro digital para controle nutricional avançado",
        description: "Bem-vindo à ferramenta definitiva para pacientes renais. Verifique instantaneamente valores críticos (Potássio, Fósforo, Proteína) e tome decisões informadas para sua saúde renal.",
        searchPlaceholder: "O que você vai comer hoje? (ex: Maçã, Frango...)",
        amountLabel: "Quantidade (gramas)",
        nutritionalInfo: "Informação Nutricional",
        protein: "Proteínas",
        sugar: "Açúcares",
        fat: "Gorduras",
        potassium: "Potássio",
        phosphorus: "Fósforo",
        salt: "Sal",
        calcium: "Cálcio"
    },
    ja: {
        title: "スマート腎臓食",
        subtitle: "高度な栄養管理のためのデジタルパートナー",
        description: "腎臓病患者のための究極のツールへようこそ。食品の重要な値（カリウム、リン、タンパク質）を即座に確認し、腎臓の健康を正確に管理するための情報に基づいた決定を下します。",
        searchPlaceholder: "今日は何を食べますか？ (例: リンゴ, 鶏肉...)",
        amountLabel: "量 (グラム)",
        nutritionalInfo: "栄養情報",
        protein: "タンパク質",
        sugar: "糖質",
        fat: "脂質",
        potassium: "カリウム",
        phosphorus: "リン",
        salt: "塩分",
        calcium: "カルシウム"
    }
};

// Global State
let currentFood = null;
let foodDatabase = [];
let currentLang = 'es';

// DOM Elements
const gridContainer = document.getElementById('food-grid');
const modal = document.getElementById('food-modal');
const closeModalBtn = document.querySelector('.close-modal');
const gramsInput = document.getElementById('grams-input');
const searchInput = document.getElementById('search-input');

// Modal Elements
const mImg = document.getElementById('modal-img');
const mName = document.getElementById('modal-name');
const valProtein = document.getElementById('val-protein');
const valSugar = document.getElementById('val-sugar');
const valFat = document.getElementById('val-fat');
const valPotassium = document.getElementById('val-potassium');
const valPhosphorus = document.getElementById('val-phosphorus');
const valSalt = document.getElementById('val-salt');
const valCalcium = document.getElementById('val-calcium');

// Language Functions
function updateLanguage(lang) {
    currentLang = lang;
    const t = translations[lang];
    if (!t) return;

    // Update Text Elements
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (t[key]) el.textContent = t[key];
    });

    // Update Placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (t[key]) el.placeholder = t[key];
    });

    // Update Grid if loaded
    if (foodDatabase.length > 0) {
        // preserve filter if any
        const searchTerm = searchInput.value.toLowerCase().trim();
        const filteredFoods = foodDatabase.filter(food =>
            getFoodName(food).toLowerCase().includes(searchTerm)
        );
        renderGrid(filteredFoods);
    }
}

function getFoodName(food) {
    if (food.names && food.names[currentLang]) {
        return food.names[currentLang];
    }
    return food.name;
}

// Custom Select Logic
function setupCustomSelect() {
    const selected = document.querySelector('.select-selected');
    const items = document.querySelector('.select-items');
    const options = document.querySelectorAll('.select-items div');

    // Toggle dropdown
    selected.addEventListener('click', function (e) {
        e.stopPropagation();
        this.classList.toggle('select-arrow-active');
        items.classList.toggle('select-hide');
    });

    // Handle option click
    options.forEach(option => {
        option.addEventListener('click', function (e) {
            e.stopPropagation();
            const lang = this.getAttribute('data-value');

            // Update UI (Uses innerHTML to keep the flag image)
            selected.innerHTML = this.innerHTML;

            // Close dropdown
            items.classList.add('select-hide');
            selected.classList.remove('select-arrow-active');

            // Update app
            updateLanguage(lang);
        });
    });

    // Close when clicking outside
    document.addEventListener('click', function (e) {
        if (!selected.contains(e.target) && !items.contains(e.target)) {
            items.classList.add('select-hide');
            selected.classList.remove('select-arrow-active');
        }
    });
}

// Initialization
async function init() {
    try {
        const response = await fetch('/api/foods');
        if (!response.ok) throw new Error('Error al cargar datos');
        foodDatabase = await response.json();

        // Setup Logic
        setupEventListeners();
        setupCustomSelect();

        // Default render
        renderGrid(foodDatabase);

        // Initial Lang
        updateLanguage('es');

    } catch (error) {
        console.error("Error cargando alimentos:", error);
        if (gridContainer) {
            gridContainer.innerHTML = '<p>Error al cargar los alimentos. Asegúrate de que el servidor (server.py) esté corriendo.</p>';
        }
    }
}

// Render Logic
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

function openModal(food) {
    currentFood = food;
    gramsInput.value = '';
    mImg.src = food.image;
    mName.textContent = getFoodName(food);
    updateNutrients(0);
    modal.classList.add('active');
    gramsInput.focus();
}

function closeModal() {
    modal.classList.remove('active');
    currentFood = null;
}

function setupEventListeners() {
    closeModalBtn.addEventListener('click', closeModal);
    window.addEventListener('click', (e) => { if (e.target === modal) closeModal(); });

    gramsInput.addEventListener('input', (e) => {
        updateNutrients(parseFloat(e.target.value) || 0);
    });

    searchInput.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase().trim();
        const filteredFoods = foodDatabase.filter(food =>
            getFoodName(food).toLowerCase().includes(searchTerm)
        );
        renderGrid(filteredFoods);
    });
}

function updateNutrients(grams) {
    if (!currentFood) return;
    const ratio = grams / 100;
    const n = currentFood.nutrients;
    valProtein.textContent = (n.protein * ratio).toFixed(1) + 'g';
    valSugar.textContent = (n.sugar * ratio).toFixed(1) + 'g';
    valFat.textContent = (n.fat * ratio).toFixed(1) + 'g';
    valPotassium.textContent = (n.potassium * ratio).toFixed(0) + 'mg';
    valPhosphorus.textContent = (n.phosphorus * ratio).toFixed(0) + 'mg';
    valSalt.textContent = (n.salt * ratio).toFixed(2) + 'g';
    valCalcium.textContent = (n.calcium * ratio).toFixed(0) + 'mg';
}

init();
