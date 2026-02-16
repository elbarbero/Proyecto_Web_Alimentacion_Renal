# 🍎 Alimentación Renal Inteligente (Smart Renal Diet)

> **Tu compañera digital para el control nutricional avanzado en pacientes renales.**

![Preview del Proyecto]([https://via.placeholder.com/800x400?text=Web+Alimentaci%C3%B3n+Renal](https://alimentacionrenal.com/))

## 📋 Descripción

Esta aplicación web es una herramienta diseñada para ayudar a personas con enfermedad renal crónica (ERC) a gestionar su dieta de manera precisa. Permite consultar valores nutricionales críticos (**Potasio**, **Fósforo**, **Proteínas**) y ofrece un asistente inteligente (Chatbot) personalizado basado en el perfil médico del usuario.

El proyecto destaca por su arquitectura modular, su sistema de cache-busting para entornos de producción y una interfaz moderna basada en **Glassmorphism**.

## ✨ Características Principales

*   **🔍 Buscador y Filtros**: Búsqueda instantánea de alimentos clasificados por idoneidad renal.
*   **📊 Semáforo Nutricional**: Indicadores visuales claros para Potasio y Fósforo.
*   **👤 Perfil Médico Personalizado**: Ajuste automático de recomendaciones según estadio (1-5), diálisis o trasplante.
*   **🤖 Smart Chatbot**: Integración con Google Gemini para resolver dudas nutricionales con contexto.
*   **🌍 Multi-idioma**: Soporte completo para ES, EN, DE, FR, PT y JA.
*   **🔐 Autenticación Robusta**: Flujos de registro, login y recuperación de contraseña (fix de solapamiento implementado).
*   **⚡ Cache Busting Total**: Sistema para forzar la recarga de módulos JS, CSS y componentes HTML en producción.
*   **📱 Diseño Responsive**: Experiencia premium en cualquier dispositivo.

## 🛠️ Arquitectura y Tecnologías

### Frontend
- **Core**: HTML5, CSS3, Vanilla JS (ES6 Modules).
- **Lógica**: 
  - `app.js`: Punto de entrada con versionado de módulos.
  - `auth.js`: Gestión de sesiones y visibilidad de vistas por clases.
  - `loader.js`: Cargador de componentes con sistema anti-caché.
  - `i18n.js`: Motor de traducción internacional.

### Backend & DevOps
- **Servidor**: Python `http.server` y Docker (Nginx/Python).
- **Base de Datos**: SQLite3 (`renal_diet.db` incluida en el repo).
- **Despliegue**: Optimizado para VPS con **Docker Compose**.

## 🚀 Instalación y Despliegue

### Entorno Local
1.  **Clonar**: `git clone [url-del-repo]`
2.  **Configurar**: Crea un `.env` con `GEMINI_API_KEY`.
3.  **Lanzar**: `python server.py` o vía Docker.

### Entorno de Producción (VPS)
El proyecto está preparado para desplegarse mediante Docker Compose:
```bash
docker compose up -d --build
```

## 📄 Licencia y Legal

Esta aplicación es estrictamente **informativa**. El usuario debe verificar siempre los datos con su nefrólogo. Los términos y condiciones están disponibles en la propia aplicación.

---
Desarrollado con ❤️ para mejorar la calidad de vida renal.
