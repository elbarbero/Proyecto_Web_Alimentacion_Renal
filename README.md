# 🍎 Alimentación Renal Inteligente (Smart Renal Diet)

> **Tu compañera digital para el control nutricional avanzado en pacientes renales.**

![Preview del Proyecto](https://via.placeholder.com/800x400?text=Web+Alimentaci%C3%B3n+Renal)

## 📋 Descripción

Esta aplicación web progresiva (PWA) está diseñada para ayudar a personas con enfermedad renal crónica (ERC) a gestionar su dieta de manera precisa. Permite consultar valores nutricionales críticos (**Potasio**, **Fósforo**, **Proteínas**) y ofrece un asistente inteligente (Chatbot) personalizado basado en el perfil médico del usuario.

La interfaz sigue principios de **Glassmorphism** y diseño moderno, asegurando accesibilidad y una experiencia visual premium.

## ✨ Características Principales

*   **🔍 Buscador y Filtros**: Búsqueda instantánea de alimentos clasificados por idoneidad renal.
*   **📊 Semáforo Nutricional**: Indicadores visuales (Verde/Amarillo/Rojo) para Potasio y Fósforo.
*   **👤 Perfil Médico Personalizado**: Ajusta las recomendaciones según tu estadio (1-5), si estás en diálisis o trasplante.
*   **🤖 Smart Chatbot**: Asistente con IA (Gemini) que responde dudas nutricionales con contexto médico ("¿Puedo comer plátano si estoy en estadio 4?").
*   **🌍 Multi-idioma**: Soporte completo para Español, Inglés, Alemán, Francés, Portugués y Japonés.
*   **🔐 Autenticación Completa**: Registro, Login, Recuperación de contraseña y gestión de perfil.
*   **📱 Diseño Responsive**: Optimizado para móviles, tablets y escritorio.

## 🛠️ Arquitectura y Tecnologías

El proyecto ha sido refactorizado a una arquitectura modular para facilitar la mantenibilidad:

### Frontend
*   **Core**: HTML5, CSS3 (Variables, Animations, Glassmorphism), Vanilla JS (ES6 Modules).
*   **Estructura**:
    *   `js/api.js`: Capa de comunicación con el backend.
    *   `js/i18n.js`: Motor de internacionalización.
    *   `js/auth.js`: Gestión de usuarios y sesiones.
    *   `js/chat.js`: Lógica del asistente IA.
    *   `components/`: HTML dinámico inyectado (Modales, Widgets).

### Backend
*   **Servidor**: Python puro (`http.server` extendido).
*   **Módulos (`backend/handlers/`)**:
    *   `auth.py`: Endpoints de autenticación (JWT/Sessions).
    *   `chat.py`: Integración con Google Gemini API.
    *   `foods.py`: API de alimentos y búsqueda.
*   **Base de Datos**: SQLite3 (`renal_diet.db`).

## 🚀 Instalación y Uso

1.  **Clonar el repositorio**:
    ```bash
    git clone https://github.com/elbarbero/Proyecto_Web_Alimentacion_Renal.git
    cd Proyecto_Web_Alimentacion_Renal
    ```

2.  **Configuración**:
    Crea un archivo `.env` en la raíz del proyecto con tu API Key de Gemini:
    ```env
    GEMINI_API_KEY=tu_api_key_aqui
    ```

3.  **Ejecutar el servidor**:
    Asegúrate de tener Python 3.x instalado.
    ```bash
    python server.py
    ```

4.  **Acceder a la web**:
    Abre tu navegador y visita:
    [http://localhost:8000](http://localhost:8000)

## 📄 Licencia y Legal

Esta aplicación es una herramienta informativa y educativa. **No sustituye el consejo médico profesional.**

*   **Términos y Condiciones**: Disponibles en el pie de página de la aplicación.
*   **Privacidad**: Los datos médicos se utilizan únicamente para personalizar la experiencia dentro de la app.

---
Desarrollado con ❤️ para mejorar la calidad de vida renal.
