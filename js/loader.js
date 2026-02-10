/**
 * js/loader.js
 * Dynamic HTML Component Loader
 */

export async function loadComponent(path, targetSelector = null) {
    try {
        const response = await fetch(path);
        if (!response.ok) throw new Error(`Failed to load ${path}`);

        const html = await response.text();

        // Create a temporary container
        const temp = document.createElement('div');
        temp.innerHTML = html;

        const target = targetSelector ? document.querySelector(targetSelector) : document.body;
        if (!target) throw new Error(`Target not found: ${targetSelector}`);

        // Append all children to target
        while (temp.firstChild) {
            target.appendChild(temp.firstChild);
        }

        console.log(`Loaded component: ${path} into ${targetSelector || 'body'}`);
    } catch (error) {
        console.error(`Error loading component from ${path}:`, error);
    }
}
