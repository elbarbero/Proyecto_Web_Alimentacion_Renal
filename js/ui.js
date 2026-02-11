export function setupCustomSelects() {
    const x = document.getElementsByClassName("custom-select");
    for (let i = 0; i < x.length; i++) {
        const selElmnt = x[i].getElementsByTagName("select")[0];
        // If real select exists (maybe hidden), updated it. But widely in this app we use divs
        // Structure: div.custom-select > div.select-selected + div.select-items > div

        const selectedDiv = x[i].querySelector(".select-selected");
        const itemsDiv = x[i].querySelector(".select-items");

        if (selectedDiv && itemsDiv) {
            // Determine initial selected value based on context
            let initialVal = null;
            if (x[i].id === 'language-select') {
                // For language select, sync with current document language
                const currentLang = document.documentElement.lang || 'es';
                const matchingOption = Array.from(itemsDiv.querySelectorAll("div"))
                    .find(div => div.getAttribute("data-value") === currentLang);

                if (matchingOption) {
                    selectedDiv.innerHTML = matchingOption.innerHTML;
                }
            }

            // Remove old listeners to avoid duplicates if re-run
            const newSelected = selectedDiv.cloneNode(true);
            selectedDiv.parentNode.replaceChild(newSelected, selectedDiv);

            newSelected.addEventListener("click", function (e) {
                e.stopPropagation();
                closeAllSelects(this);
                itemsDiv.classList.toggle("select-hide");
                this.classList.toggle("select-arrow-active");
            });

            const options = itemsDiv.querySelectorAll("div");
            options.forEach(opt => {
                // Clone to remove old listeners
                const newOpt = opt.cloneNode(true);
                opt.parentNode.replaceChild(newOpt, opt);

                newOpt.addEventListener("click", function (e) {
                    const val = this.getAttribute("data-value");
                    const txt = this.textContent;

                    // Update User Interface
                    newSelected.innerHTML = this.innerHTML; // Keep flag/icon if any
                    // Update Hidden Input if exists (common pattern)
                    // Update Hidden Input
                    // Try to find input inside first
                    let hiddenInput = x[i].querySelector("input[type=hidden]");

                    // Fallback to heuristic ID if not found inside
                    if (!hiddenInput) {
                        const inputId = x[i].id.replace("-select", "-type-hidden");
                        hiddenInput = document.getElementById(inputId);
                    }

                    if (hiddenInput) {
                        hiddenInput.value = val;
                        hiddenInput.dispatchEvent(new Event('change'));
                        // console.log('Updated hidden input:', hiddenInput.id, 'to', val);
                    } else {
                        console.error('Hidden input not found for select:', x[i].id);
                    }

                    // Trigger change event if needed?
                    // For now handled by click.

                    // Check if it's language selector
                    if (x[i].id === 'language-select') {
                        // Dispatch event
                        const event = new CustomEvent('languageChanged', { detail: val });
                        document.dispatchEvent(event);
                    }

                    itemsDiv.classList.add("select-hide");
                    newSelected.classList.remove("select-arrow-active");
                });
            });
        }
    }

    document.addEventListener("click", closeAllSelects);
}

function closeAllSelects(elmnt) {
    const x = document.getElementsByClassName("select-items");
    const y = document.getElementsByClassName("select-selected");
    const arrNo = [];

    for (let i = 0; i < y.length; i++) {
        if (elmnt == y[i]) {
            arrNo.push(i)
        } else {
            y[i].classList.remove("select-arrow-active");
        }
    }

    for (let i = 0; i < x.length; i++) {
        if (arrNo.indexOf(i) == -1) {
            x[i].classList.add("select-hide");
        }
    }
}

export function togglePasswordVisibility(inputId, icon) {
    const input = document.getElementById(inputId);
    if (input.type === "password") {
        input.type = "text";
        // Change icon to eye-off ideally, or generic toggle
        icon.style.opacity = "0.7";
    } else {
        input.type = "password";
        icon.style.opacity = "1";
    }
}

// Simple Toast fallback
export function showToast(message, type = 'info') {
    // Check if toast container exists
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.position = 'fixed';
        container.style.bottom = '20px';
        container.style.right = '20px';
        container.style.zIndex = '9999';
        document.body.appendChild(container); // Safe DOM manipulation
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.style.background = type === 'error' ? '#ef4444' : '#10b981';
    toast.style.color = 'white';
    toast.style.padding = '12px 24px';
    toast.style.marginBottom = '10px';
    toast.style.borderRadius = '8px';
    toast.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
    toast.style.animation = 'slideIn 0.3s ease-out';
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

let currentViewId = 'view-home';
const viewHistory = [];

export function showView(viewId, saveHistory = true) {
    const views = document.querySelectorAll('.view-section');
    const backBtn = document.getElementById('global-back-btn');

    if (saveHistory && currentViewId !== viewId) {
        viewHistory.push(currentViewId);
    }
    currentViewId = viewId;

    const sectionId = viewId.startsWith('view-menus') ? 'view-menus' : viewId;

    views.forEach(view => {
        if (view.id === sectionId) {
            view.classList.remove('hidden');
        } else {
            view.classList.add('hidden');
        }
    });

    if (viewId === 'view-home') {
        if (backBtn) backBtn.classList.add('hidden');
    } else {
        if (backBtn) backBtn.classList.remove('hidden');
    }

    // Trigger an event so other modules (like menus.js) can react to view changes
    const event = new CustomEvent('viewChanged', { detail: { viewId } });
    document.dispatchEvent(event);

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

export function goBack() {
    if (viewHistory.length > 0) {
        const prevView = viewHistory.pop();
        showView(prevView, false);
    } else {
        showView('view-home', false);
    }
}

// Custom Confirm/Alert Modal Logic
let currentModalResolve = null;

export function showConfirm(title, message, icon = '⚠️') {
    if (currentModalResolve) currentModalResolve(false); // Resolve previous if any

    return new Promise((resolve) => {
        currentModalResolve = resolve;
        const modal = document.getElementById('custom-confirm-modal');
        const titleEl = document.getElementById('confirm-title');
        const messageEl = document.getElementById('confirm-message');
        const okBtn = document.getElementById('confirm-ok-btn');
        const cancelBtn = document.getElementById('confirm-cancel-btn');
        const iconEl = modal.querySelector('.confirmation-icon');

        if (!modal || !titleEl || !messageEl || !okBtn) {
            resolve(confirm(message));
            currentModalResolve = null;
            return;
        }

        titleEl.textContent = title;
        messageEl.textContent = message;
        if (iconEl) iconEl.textContent = icon;
        if (cancelBtn) cancelBtn.style.display = 'block';

        const handleOk = () => {
            cleanup();
            resolve(true);
        };

        const handleCancel = () => {
            cleanup();
            resolve(false);
        };

        const cleanup = () => {
            okBtn.removeEventListener('click', handleOk);
            if (cancelBtn) cancelBtn.removeEventListener('click', handleCancel);
            modal.classList.remove('active');
            document.body.style.overflow = '';
            currentModalResolve = null;
        };

        okBtn.addEventListener('click', handleOk);
        if (cancelBtn) cancelBtn.addEventListener('click', handleCancel);

        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    });
}

export function showAlert(title, message, icon = 'ℹ️') {
    if (currentModalResolve) currentModalResolve(null);

    return new Promise((resolve) => {
        currentModalResolve = resolve;
        const modal = document.getElementById('custom-confirm-modal');
        const titleEl = document.getElementById('confirm-title');
        const messageEl = document.getElementById('confirm-message');
        const okBtn = document.getElementById('confirm-ok-btn');
        const cancelBtn = document.getElementById('confirm-cancel-btn');
        const iconEl = modal.querySelector('.confirmation-icon');

        if (!modal || !titleEl || !messageEl || !okBtn) {
            alert(message);
            resolve();
            currentModalResolve = null;
            return;
        }

        titleEl.textContent = title;
        messageEl.textContent = message;
        if (iconEl) iconEl.textContent = icon;
        if (cancelBtn) cancelBtn.style.display = 'none';

        const handleOk = () => {
            cleanup();
            resolve();
        };

        const cleanup = () => {
            modal.classList.remove('active');
            document.body.style.overflow = '';
            okBtn.removeEventListener('click', handleOk);
            currentModalResolve = null;
        };

        okBtn.addEventListener('click', handleOk);
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    });
}

window.closeConfirmModal = () => {
    const modal = document.getElementById('custom-confirm-modal');
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
        if (currentModalResolve) {
            currentModalResolve(false);
            currentModalResolve = null;
        }
    }
};

// Global exposure for onclick handlers
window.goBack = goBack;
