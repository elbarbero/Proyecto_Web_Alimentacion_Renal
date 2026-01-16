// Datos de ejemplo de alimentos (valores por 100g)
const foodDatabase = [
    {
        id: 1,
        name: "Manzana",
        image: "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60",
        nutrients: {
            protein: 0.3,   // g
            sugar: 10.4,    // g
            fat: 0.2,       // g
            potassium: 107, // mg
            phosphorus: 11, // mg
            salt: 0.001     // g
        }
    },
    {
        id: 2,
        name: "Pollo (Pechuga)",
        image: "https://images.unsplash.com/photo-1604503468506-a8da13d82791?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60",
        nutrients: {
            protein: 31,
            sugar: 0,
            fat: 3.6,
            potassium: 256,
            phosphorus: 228,
            salt: 0.1
        }
    },
    {
        id: 3,
        name: "Arroz Blanco",
        image: "https://images.unsplash.com/photo-1586201375761-83865001e31c?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60",
        nutrients: {
            protein: 2.7,
            sugar: 0.1,
            fat: 0.3,
            potassium: 35,
            phosphorus: 43,
            salt: 0.01
        }
    },
    {
        id: 4,
        name: "Salmón",
        image: "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60",
        nutrients: {
            protein: 20,
            sugar: 0,
            fat: 13,
            potassium: 363,
            phosphorus: 200,
            salt: 0.05
        }
    },
    {
        id: 5,
        name: "Huevo",
        image: "https://images.unsplash.com/photo-1506976785307-8732e854ad03?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60",
        nutrients: {
            protein: 13,
            sugar: 1.1,
            fat: 11,
            potassium: 126,
            phosphorus: 198,
            salt: 0.12
        }
    },
    {
        id: 6,
        name: "Espinacas",
        image: "https://images.unsplash.com/photo-1576045057995-568f588f82fb?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60",
        nutrients: {
            protein: 2.9,
            sugar: 0.4,
            fat: 0.4,
            potassium: 558,
            phosphorus: 49,
            salt: 0.07
        }
    }
];

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

// Inicialización
function init() {
    renderGrid();
    setupEventListeners();
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
