/**
 * js/loader.js
 * Dynamic HTML Component Loader
 */

export async function loadComponent(path) {
    try {
        const response = await fetch(path);
        if (!response.ok) throw new Error(`Failed to load ${path}`);

        const html = await response.text();

        // Create a temporary container
        const temp = document.createElement('div');
        temp.innerHTML = html;

        // Append all children to document.body
        while (temp.firstChild) {
            document.body.appendChild(temp.firstChild);
        }

        console.log(`Loaded component: ${path}`);
    } catch (error) {
        console.error(`Error loading component from ${path}:`, error);
    }
}
