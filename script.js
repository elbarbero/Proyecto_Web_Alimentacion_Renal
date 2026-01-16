// Elementos del DOM
const gridContainer = document.getElementById('food-grid');
const modal = document.getElementById('food-modal');
const closeModalBtn = document.querySelector('.close-modal');
const gramsInput = document.getElementById('grams-input');

// Elementos del Modal para actualizar
const mImg = document.getElementById('modal-img');
const mName = document.getElementById('modal-name');
const valProtein = document.getElementById('val-protein');
const valSugar = document.getElementById('val-sugar');
const valFat = document.getElementById('val-fat');
const valPotassium = document.getElementById('val-potassium');
const valPhosphorus = document.getElementById('val-phosphorus');
const valSalt = document.getElementById('val-salt');

let currentFood = null;
let foodDatabase = []; // Ahora se llenará desde la API

// Inicialización
async function init() {
    try {
        const response = await fetch('/api/foods');
        if (!response.ok) throw new Error('Error al cargar datos');
        foodDatabase = await response.json();
        renderGrid();
        setupEventListeners();
    } catch (error) {
        console.error("Error cargando alimentos:", error);
        gridContainer.innerHTML = '<p>Error al cargar los alimentos. Asegúrate de que el servidor (server.py) esté corriendo.</p>';
    }
}

// Renderizar lista de alimentos
function renderGrid() {
    gridContainer.innerHTML = '';
    foodDatabase.forEach(food => {
        const card = document.createElement('div');
        card.className = 'food-card';
        card.innerHTML = `
            <img src="${food.image}" alt="${food.name}">
            <h3>${food.name}</h3>
        `;
        card.addEventListener('click', () => openModal(food));
        gridContainer.appendChild(card);
    });
}

// Abrir modal con alimento seleccionado
function openModal(food) {
    currentFood = food;

    // Resetear input
    gramsInput.value = '';

    // Cargar datos estáticos parte A
    mImg.src = food.image;
    mName.textContent = food.name;

    // Resetear valores parte B
    updateNutrients(0);

    modal.classList.add('active');
    gramsInput.focus();
}

// Cerrar modal
function closeModal() {
    modal.classList.remove('active');
    currentFood = null;
}

// Configurar listeners
function setupEventListeners() {
    closeModalBtn.addEventListener('click', closeModal);

    // Cerrar si clic fuera del contenido
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });

    // Calcular al escribir
    gramsInput.addEventListener('input', (e) => {
        const grams = parseFloat(e.target.value) || 0;
        updateNutrients(grams);
    });
}

// Lógica de cálculo
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
}

// Arrancar app
init();
