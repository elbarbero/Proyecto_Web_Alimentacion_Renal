# 🍎 Alimentación Renal Inteligente

> **Tu compañera digital para el control nutricional avanzado en pacientes renales.**

![Preview del Proyecto](https://via.placeholder.com/800x400?text=Preview+App+Renal+Diet)

## 📋 Descripción

Esta aplicación web está diseñada específicamente para ayudar a personas con enfermedad renal crónica a gestionar su dieta de manera precisa y segura. Permite consultar al instante valores nutricionales críticos como **Potasio**, **Fósforo**, **Proteínas**, **Sal**, **Azúcares** y **Grasas**.

La interfaz ha sido diseñada siguiendo principios de **Glassmorphism** y **Modern UI**, ofreciendo una experiencia de usuario premium, limpia y accesible.

## ✨ Características Principales

*   **🔍 Buscador en Tiempo Real**: Filtra alimentos instantáneamente mientras escribes.
*   **🖼️ Base de Datos Visual**: Imágenes de alta calidad (Bing Thumbnails) estandarizadas y optimizadas.
*   **⚡ Cálculo Dinámico**: Introduce los gramos de tu ración y la app recalculará automáticamente todos los microbióticos y macrobióticos.
*   **🏥 Enfoque Renal**: Alertas visuales y destaque de valores críticos (Potasio, Fósforo).
*   **📱 Diseño Responsive**: Funciona perfectamente en móviles, tablets y escritorio.

## 🛠️ Tecnologías Utilizadas

*   **Frontend**: HTML5, CSS3 (Variables, Flexbox, Grid, Glassmorphism), Vanilla JavaScript.
*   **Backend**: Python (`http.server` personalizado).
*   **Base de Datos**: SQLite3 (Ligera y portable).
*   **API**: REST API propia servida desde Python.

## 🚀 Instalación y Uso

1.  **Clonar el repositorio**:
    ```bash
    git clone https://github.com/elbarbero/Proyecto_Web_Alimentacion_Renal.git
    cd Proyecto_Web_Alimentacion_Renal
    ```

2.  **Ejecutar el servidor**:
    Asegúrate de tener Python instalado.
    ```bash
    python server.py
    ```

3.  **Acceder a la web**:
    Abre tu navegador favorito y ve a:
    [http://localhost:8000](http://localhost:8000)

## 🔄 Regeneración de Datos
Si deseas resetear la base de datos o actualizar las imágenes, ejecuta:
```bash
python db_init.py
```
Esto borrará `renal_diet.db` y la creará de nuevo con los datos iniciales actualizados.

---
Desarrollado con ❤️ para mejorar la calidad de vida renal.
