import { fetchUser, login, register, requestPasswordReset, resetPassword } from './api.js';
import { translations, getCurrentLang } from './i18n.js';
import { clearChatHistory } from './chat.js';

// Module-Scope Variables (Initialized in setupAuth)
let userBtn, authModal, closeAuthBtn, authForm, authBody;
let tabLogin, tabRegister, nameGroup, termsGroup, forgotLinkContainer, authTitle, authSubmit, switchRegister, authError;
let forgotView, resetView, forgotForm, resetForm, forgotMsg, forgotError, resetMsg, resetError;
let termsModal, openTermsBtn, closeTermsBtn, acceptTermsBtn, termsContentDiv;

// Profile & Medical Variables
let medicalModal, medicalForm, saveMedicalBtn, cancelMedicalBtn, closeMedicalBtn, medicalError;
let profileName, profileSurnames, profileBirthdate, profileEmail, profilePassword;
let insufficiencyToggle, treatmentGroup, stageGroup, treatmentHidden, treatmentSelect;

// State
let isRegistering = false;
let pendingAvatarUpload = null;

export function setupAuth() {
    // --- Auth DOM Elements ---
    userBtn = document.getElementById('user-btn');
    authModal = document.getElementById('auth-modal');
    closeAuthBtn = document.getElementById('close-auth');
    authForm = document.getElementById('auth-form');
    tabLogin = document.getElementById('tab-login');
    tabRegister = document.getElementById('tab-register');
    nameGroup = document.getElementById('register-fields');
    termsGroup = document.getElementById('register-terms');
    forgotLinkContainer = document.getElementById('forgot-password-link-container');
    authTitle = document.getElementById('auth-title');
    authSubmit = document.getElementById('auth-submit');
    switchRegister = document.getElementById('switch-to-register');
    authError = document.getElementById('auth-error');
    authBody = document.querySelector('.auth-body:not(#forgot-password-view):not(#reset-password-view)');

    forgotView = document.getElementById('forgot-password-view');
    resetView = document.getElementById('reset-password-view');
    forgotForm = document.getElementById('forgot-form');
    resetForm = document.getElementById('reset-form');
    forgotMsg = document.getElementById('forgot-msg');
    forgotError = document.getElementById('forgot-error');
    resetMsg = document.getElementById('reset-msg');
    resetError = document.getElementById('reset-error');

    // --- Terms Modal Elements ---
    termsModal = document.getElementById('terms-modal');
    openTermsBtn = document.getElementById('open-terms');
    closeTermsBtn = document.getElementById('close-terms');
    acceptTermsBtn = document.getElementById('accept-terms-btn');
    termsContentDiv = document.getElementById('terms-content');

    // --- Profile/Medical DOM Elements ---
    medicalModal = document.getElementById('medical-modal');
    medicalForm = document.getElementById('medical-form');
    saveMedicalBtn = document.getElementById('save-medical');
    cancelMedicalBtn = document.getElementById('cancel-medical');
    closeMedicalBtn = document.getElementById('close-medical');
    medicalError = document.getElementById('medical-error');

    profileName = document.getElementById('profile-name');
    profileSurnames = document.getElementById('profile-surnames');
    profileBirthdate = document.getElementById('profile-birthdate');
    profileEmail = document.getElementById('profile-email');
    profilePassword = document.getElementById('profile-password');

    insufficiencyToggle = document.getElementById('insufficiency-toggle');
    treatmentGroup = document.getElementById('treatment-group');
    stageGroup = document.getElementById('stage-group');
    treatmentHidden = document.getElementById('treatment-type-hidden');
    treatmentSelect = document.getElementById('treatment-select');

    if (!userBtn) {
        console.warn("setupAuth: user-btn not found. Auth listeners skipped.");
        return;
    }

    // --- Listeners ---

    // 1. User Button (Login / Dropdown)
    userBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
            const dropdown = document.getElementById('user-dropdown');
            if (dropdown) dropdown.classList.toggle('active');
        } else {
            openAuthModal();
        }
    });

    // 2. Auth Modal Close
    if (closeAuthBtn) closeAuthBtn.addEventListener('click', closeAuthModal);

    // 3. Global Click (Close Modals/Dropdowns)
    window.addEventListener('click', (e) => {
        if (authModal && e.target === authModal) closeAuthModal();
        if (medicalModal && e.target === medicalModal) closeMedicalModal();
        if (termsModal && e.target === termsModal) termsModal.classList.remove('active');

        const dropdown = document.getElementById('user-dropdown');
        if (dropdown && dropdown.classList.contains('active')) {
            if (!userBtn.contains(e.target) && !dropdown.contains(e.target)) {
                dropdown.classList.remove('active');
            }
        }
    });

    // 4. Tabs
    if (tabLogin) tabLogin.addEventListener('click', () => toggleAuthMode(false));
    if (tabRegister) tabRegister.addEventListener('click', () => toggleAuthMode(true));

    // 5. Switch Link
    if (switchRegister) {
        switchRegister.addEventListener('click', (e) => {
            e.preventDefault();
            toggleAuthMode(!isRegistering);
        });
    }

    // 6. Auth Submit
    if (authForm) authForm.addEventListener('submit', handleAuthSubmit);

    // 7. Input Validation Clearing
    const inputs = document.querySelectorAll('#auth-form input');
    inputs.forEach(input => {
        input.addEventListener('input', (e) => clearError(e.target));
        input.addEventListener('change', (e) => clearError(e.target));
    });

    // 8. Initial Login Check
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
        const user = JSON.parse(storedUser);
        userBtn.classList.add('user-logged-in');
        updateUserAvatar(user.avatar_url || 'images/default_avatar.png');
    }

    // 9. Setup Sub-Components
    setupDropdownListeners();
    setupForgotReset();
    setupDropdownListeners();
    setupForgotReset();
    setupMedicalProfile();
    setupTermsModal();
    checkResetToken();
}

function setupTermsModal() {
    if (openTermsBtn) {
        openTermsBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation(); // Prevent label click from checking box
            openTerms();
        });
    }
    if (closeTermsBtn) closeTermsBtn.addEventListener('click', () => termsModal.classList.remove('active'));
    if (acceptTermsBtn) acceptTermsBtn.addEventListener('click', () => termsModal.classList.remove('active'));
}

function openTerms() {
    if (!termsModal) return;
    const t = translations[getCurrentLang()];
    if (termsContentDiv) termsContentDiv.innerHTML = t.termsContent || '<p>Terms not available.</p>';
    termsModal.classList.add('active');
}

// --- Auth Modal Logic ---

function openAuthModal() {
    if (!authModal) return;
    if (authForm) authForm.style.display = 'block';
    if (forgotView) forgotView.style.display = 'none';
    if (resetView) resetView.style.display = 'none';
    if (authBody) authBody.style.display = 'block';

    const tabs = document.querySelector('.auth-tabs');
    if (tabs) tabs.style.display = 'flex';

    toggleAuthMode(false);
    authModal.classList.add('active');
}

function closeAuthModal() {
    if (authModal) authModal.classList.remove('active');
}

function toggleAuthMode(register) {
    isRegistering = register;
    if (authError) authError.textContent = '';
    const t = translations[getCurrentLang()];

    if (isRegistering) {
        if (tabLogin) tabLogin.classList.remove('active');
        if (tabRegister) tabRegister.classList.add('active');
        if (nameGroup) nameGroup.style.display = 'block';
        if (termsGroup) termsGroup.style.display = 'block';
        if (forgotLinkContainer) forgotLinkContainer.style.display = 'none';

        if (authTitle) authTitle.textContent = t.createAccount;
        if (authSubmit) authSubmit.textContent = t.registerBtn;

        const footer = document.getElementById('auth-footer-text');
        if (footer) footer.style.display = 'none';

        const n = document.getElementById('auth-name'); if (n) n.required = true;
        const s = document.getElementById('auth-surnames'); if (s) s.required = true;
        const b = document.getElementById('auth-birthdate'); if (b) b.required = true;
    } else {
        if (tabLogin) tabLogin.classList.add('active');
        if (tabRegister) tabRegister.classList.remove('active');
        if (nameGroup) nameGroup.style.display = 'none';
        if (termsGroup) termsGroup.style.display = 'none';
        if (forgotLinkContainer) forgotLinkContainer.style.display = 'block';

        if (authTitle) authTitle.textContent = t.welcomeBack;
        if (authSubmit) authSubmit.textContent = t.loginBtn;

        const footer = document.getElementById('auth-footer-text');
        if (footer) footer.style.display = 'block';

        const n = document.getElementById('auth-name'); if (n) n.required = false;
        const s = document.getElementById('auth-surnames'); if (s) s.required = false;
        const b = document.getElementById('auth-birthdate'); if (b) b.required = false;
    }
}

function clearError(input) {
    if (input) input.classList.remove('input-error');
    const group = document.querySelector('.checkbox-group');
    if (group) group.classList.remove('checkbox-error');
}

async function handleAuthSubmit(e) {
    e.preventDefault();
    if (authError) authError.textContent = '';
    const t = translations[getCurrentLang()];

    // --- Validation Logic ---
    let isValid = true;
    let firstInvalid = null;

    const email = document.getElementById('auth-email');
    const password = document.getElementById('auth-password');

    const markInvalid = (el) => {
        if (el) {
            el.classList.add('input-error');
            if (!firstInvalid) firstInvalid = el;
        }
        isValid = false;
    };

    if (!email.value) markInvalid(email);
    if (!password.value) markInvalid(password);

    if (isRegistering) {
        const name = document.getElementById('auth-name');
        const surnames = document.getElementById('auth-surnames');
        const birthdate = document.getElementById('auth-birthdate');

        if (!name.value) markInvalid(name);
        if (!surnames.value) markInvalid(surnames);
        if (!birthdate.value) markInvalid(birthdate);

        // Terms
        const termsCheck = document.getElementById('terms-check');
        if (termsCheck && !termsCheck.checked) {
            const group = document.querySelector('.checkbox-group');
            if (group) group.classList.add('checkbox-error');
            isValid = false;
            if (!firstInvalid) {
                if (authError) authError.textContent = t.validationTerms;
                return;
            }
        }

        const birthDateObj = new Date(birthdate.value);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        if (birthDateObj > today) {
            if (authError) authError.textContent = 'La fecha de nacimiento no puede ser futura.';
            return;
        }
    }

    if (!isValid) {
        if (authError) authError.textContent = t.validationGeneric || "Por favor, complete todos los campos requeridos.";
        if (firstInvalid) firstInvalid.focus();
        return;
    }

    try {
        let res;
        const payload = {
            email: email.value,
            password: password.value
        };

        if (isRegistering) {
            payload.name = document.getElementById('auth-name').value;
            payload.surnames = document.getElementById('auth-surnames').value;
            payload.birthdate = document.getElementById('auth-birthdate').value;
            res = await register(payload);
        } else {
            res = await login(payload.email, payload.password);
        }

        const data = await res.json();

        if (data.status === 'success') {
            const userData = {
                id: data.userId,
                name: data.name,
                surnames: data.surnames,
                birthdate: data.birthdate,
                has_insufficiency: data.has_insufficiency,
                treatment_type: data.treatment_type,
                treatment_type: data.treatment_type,
                kidney_stage: data.kidney_stage,
                email: data.email || payload.email, // Prefer backend source
                avatar_url: data.avatar_url || 'images/default_avatar.png'
            };

            localStorage.setItem('user', JSON.stringify(userData));
            userBtn.classList.add('user-logged-in');
            updateUserAvatar(userData.avatar_url);
            closeAuthModal();
            authForm.reset();

            if (isRegistering) {
                // Open Profile for setup
                loadProfileData();
                if (medicalModal) medicalModal.classList.add('active');
            } else {
                // Optional welcome
                // alert(`Hola ${data.name}!`); 
            }
            // Reload to ensure state consistency if needed, though strictly not required if we update UI
            location.reload();
        } else {
            if (authError) authError.textContent = data.message || "Error";
        }

    } catch (err) {
        console.error(err);
        if (authError) authError.textContent = "Error de conexión";
    }
}

// --- Dropdown & Profile Listeners ---

function setupDropdownListeners() {
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            logout();
        });
    }

    const profileBtn = document.getElementById('profile-btn');
    if (profileBtn) {
        profileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const dropdown = document.getElementById('user-dropdown');
            if (dropdown) dropdown.classList.remove('active');

            // Open Profile Modal
            loadProfileData();
            if (medicalModal) medicalModal.classList.add('active');
        });
    }
}

// --- Medical / Profile Logic ---

function setupMedicalProfile() {
    if (!medicalForm) return;

    // Avatar Input
    const avatarInput = document.getElementById('avatar-input');
    const avatarPreview = document.getElementById('avatar-preview');
    if (avatarInput) {
        avatarInput.addEventListener('change', function (e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    avatarPreview.src = e.target.result;
                    pendingAvatarUpload = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // Toggle Visibility
    if (insufficiencyToggle) {
        insufficiencyToggle.addEventListener('change', updateMedicalVisibility);
        // Init logic
        updateMedicalVisibility();
    }

    if (treatmentHidden) {
        treatmentHidden.addEventListener('change', updateMedicalVisibility);
    }

    // Close Actions
    if (closeMedicalBtn) closeMedicalBtn.addEventListener('click', closeMedicalModal);
    if (cancelMedicalBtn) cancelMedicalBtn.addEventListener('click', closeMedicalModal);

    // Submit
    medicalForm.addEventListener('submit', handleMedicalSubmit);
}

function closeMedicalModal() {
    if (medicalModal) medicalModal.classList.remove('active');
}

function updateMedicalVisibility() {
    if (!insufficiencyToggle || !treatmentGroup || !stageGroup) return;

    if (insufficiencyToggle.checked) {
        treatmentGroup.classList.remove('disabled-section');
        treatmentGroup.querySelectorAll('input, select, button').forEach(el => el.disabled = false);

        if (treatmentHidden && treatmentHidden.value === 'dialysis') {
            stageGroup.classList.add('disabled-section');
            stageGroup.querySelectorAll('input, select, button').forEach(el => el.disabled = true);
        } else {
            stageGroup.classList.remove('disabled-section');
            stageGroup.querySelectorAll('input, select, button').forEach(el => el.disabled = false);
        }
    } else {
        treatmentGroup.classList.add('disabled-section');
        stageGroup.classList.add('disabled-section');
        treatmentGroup.querySelectorAll('input, select, button').forEach(el => el.disabled = true);
        stageGroup.querySelectorAll('input, select, button').forEach(el => el.disabled = true);
    }
}

async function loadProfileData() {
    let storedUser = localStorage.getItem('user');
    if (!storedUser) return;
    let user = JSON.parse(storedUser);

    // Self-healing: If email missing but ID exists, fetch full data
    if (!user.email && user.id) {
        try {
            const res = await fetch(`/api/get_user?id=${user.id}`);
            if (res.ok) {
                const freshData = await res.json();
                user = { ...user, ...freshData };
                localStorage.setItem('user', JSON.stringify(user));
            } else {
                // If fetch fails (e.g. user deleted), force logout
                logout();
                return;
            }
        } catch (e) {
            console.error("Auto-repair failed:", e);
        }
    }

    pendingAvatarUpload = null;
    const avatarInput = document.getElementById('avatar-input');
    if (avatarInput) avatarInput.value = '';

    if (profileName) profileName.value = user.name || '';
    if (profileSurnames) profileSurnames.value = user.surnames || '';
    if (profileBirthdate) profileBirthdate.value = user.birthdate || '';
    if (profileEmail) profileEmail.value = user.email || '';

    // Disable email editing
    const emailGroup = document.getElementById('profile-email-group');
    if (emailGroup) {
        emailGroup.style.display = 'block';
        if (profileEmail) profileEmail.disabled = true;
    }

    const passGroup = document.getElementById('profile-password-group');
    if (passGroup) passGroup.style.display = 'none'; // Or block if we want to allow change

    const nameDisplay = document.getElementById('profile-name-display');
    if (nameDisplay) nameDisplay.textContent = (user.name || '') + " " + (user.surnames || '');

    if (user.avatar_url) {
        const url = user.avatar_url;
        const timestamp = new Date().getTime();
        const preview = document.getElementById('avatar-preview');
        if (preview) preview.src = url.includes('?') ? `${url}&t=${timestamp}` : `${url}?t=${timestamp}`;
    }

    // Medical Data
    if (insufficiencyToggle) {
        const val = user.has_insufficiency;
        const isChecked = val === '1' || val === 1 || val === true || val === 'true';
        insufficiencyToggle.checked = isChecked;
        updateMedicalVisibility();
    }

    const t = translations[getCurrentLang()];
    if (saveMedicalBtn) saveMedicalBtn.textContent = t.saveBtn;
    if (cancelMedicalBtn) cancelMedicalBtn.style.display = 'block';

    if (user.treatment_type) {
        if (treatmentHidden && treatmentSelect) {
            treatmentHidden.value = user.treatment_type;
            const selectedText = treatmentSelect.querySelector('.select-selected');
            const option = treatmentSelect.querySelector(`.select-items div[data-value="${user.treatment_type}"]`);
            if (option && selectedText) {
                const key = option.getAttribute('data-i18n');
                if (key) {
                    selectedText.setAttribute('data-i18n', key);
                    selectedText.textContent = t[key] || option.textContent;
                } else {
                    selectedText.textContent = option.textContent;
                    selectedText.removeAttribute('data-i18n');
                }
                selectedText.classList.add('selected-value');
            }
        }
    }

    if (user.kidney_stage) {
        const val = String(user.kidney_stage);
        const radio = document.querySelector(`input[name="kidney_stage"][value="${val}"]`);
        if (radio) radio.checked = true;
    }
}

async function handleMedicalSubmit(e) {
    e.preventDefault();
    if (medicalError) medicalError.textContent = '';
    if (saveMedicalBtn) saveMedicalBtn.disabled = true;

    const storedUser = localStorage.getItem('user');
    if (!storedUser) {
        if (medicalError) medicalError.textContent = 'Error: Usuario no identificado';
        if (saveMedicalBtn) saveMedicalBtn.disabled = false;
        return;
    }
    let user = JSON.parse(storedUser);

    const name = profileName.value;
    const surnames = profileSurnames.value;
    const birthdate = profileBirthdate.value;
    const pass = profilePassword ? profilePassword.value : '';
    const insufficiency = insufficiencyToggle && insufficiencyToggle.checked ? '1' : '0';

    let treatment = null;
    let stage = null;

    if (insufficiency === '1') {
        treatment = treatmentHidden.value;
        stage = document.querySelector('input[name="kidney_stage"]:checked')?.value;
    }

    const payload = {
        email: user.email,
        name: name,
        surnames: surnames,
        birthdate: birthdate,
        has_insufficiency: insufficiency,
        treatment_type: treatment || null,
        kidney_stage: stage || null
    };

    if (pass) payload.password = pass;

    // Date check
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    if (new Date(birthdate) > today) {
        if (medicalError) medicalError.textContent = 'Fecha inválida';
        if (saveMedicalBtn) saveMedicalBtn.disabled = false;
        return;
    }

    try {
        const res = await fetch('/api/update_profile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            // Upload avatar if pending
            if (pendingAvatarUpload) {
                const avRes = await fetch('/api/upload_avatar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: user.email, image_data: pendingAvatarUpload })
                });
                if (avRes.ok) {
                    const avData = await avRes.json();
                    user.avatar_url = avData.avatar_url;
                }
            }

            // Update Local Storage
            user.name = name;
            user.surnames = surnames;
            user.birthdate = birthdate;
            user.has_insufficiency = insufficiency;
            user.treatment_type = treatment;
            user.kidney_stage = stage;
            localStorage.setItem('user', JSON.stringify(user));

            closeMedicalModal();
            updateUserAvatar(user.avatar_url);

            // Clear password
            if (profilePassword) profilePassword.value = '';
            alert('Perfil actualizado!');
            location.reload();

        } else {
            const data = await res.json();
            if (medicalError) medicalError.textContent = data.message || 'Error';
        }

    } catch (err) {
        console.error(err);
        if (medicalError) medicalError.textContent = 'Error de conexión';
    } finally {
        if (saveMedicalBtn) saveMedicalBtn.disabled = false;
    }
}


// --- Shared Helpers ---

export function logout() {
    localStorage.removeItem('user');
    localStorage.removeItem('chat_history');
    clearChatHistory(); // Reset chat UI immediately
    location.reload();
}

function updateUserAvatar(url) {
    const userBtn = document.getElementById('user-btn');
    const avatarImg = document.getElementById('user-avatar-img');

    if (userBtn && avatarImg) {
        userBtn.classList.add('has-avatar');
        if (url.includes('?')) {
            avatarImg.src = `${url}&t=${new Date().getTime()}`;
        } else {
            avatarImg.src = `${url}?t=${new Date().getTime()}`;
        }
    }
}

function setupForgotReset() {
    const btn = document.getElementById('forgot-password-btn');
    if (btn) {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            if (authBody) authBody.style.display = 'none';
            if (forgotView) forgotView.style.display = 'block';
        });
    }

    const back = document.getElementById('back-to-login');
    if (back) {
        back.addEventListener('click', (e) => {
            e.preventDefault();
            if (forgotView) forgotView.style.display = 'none';
            if (authBody) authBody.style.display = 'block';
        });
    }

    if (forgotForm) {
        forgotForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('forgot-email').value;
            if (forgotError) forgotError.textContent = '';
            if (forgotMsg) forgotMsg.style.display = 'none';

            try {
                const res = await requestPasswordReset(email);
                const data = await res.json();
                if (data.status === 'success') {
                    if (forgotMsg) {
                        forgotMsg.style.display = 'block';
                        forgotMsg.textContent = data.message || "Enlace enviado. Revise su correo.";
                    }
                } else {
                    if (forgotError) forgotError.textContent = data.message;
                }
            } catch (err) {
                if (forgotError) forgotError.textContent = 'Connection Error';
            }
        });
    }

    if (resetForm) {
        resetForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const urlParams = new URLSearchParams(window.location.search);
            const token = urlParams.get('reset_token');
            const password = document.getElementById('reset-new-password').value;

            if (resetError) resetError.textContent = '';
            if (resetMsg) resetMsg.style.display = 'none';

            if (!token) {
                if (resetError) resetError.textContent = "Token inválido o expirado.";
                return;
            }

            try {
                const res = await resetPassword(token, password);
                const data = await res.json();
                if (data.status === 'success') {
                    if (resetMsg) {
                        resetMsg.style.display = 'block';
                        resetMsg.textContent = data.message || "Contraseña actualizada.";
                    }
                    setTimeout(() => {
                        window.location.href = window.location.pathname; // Clear token from URL and reload logic
                    }, 2000);
                } else {
                    if (resetError) resetError.textContent = data.message;
                }
            } catch (err) {
                if (resetError) resetError.textContent = 'Connection Error';
            }
        });
    }
}

function checkResetToken() {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('reset_token');

    if (token) {
        if (!authModal) return;

        // Open Modal
        authModal.classList.add('active');

        // Hide others
        if (authBody) authBody.style.display = 'none';
        if (forgotView) forgotView.style.display = 'none';

        // Show Reset View
        if (resetView) resetView.style.display = 'block';
    }
}
