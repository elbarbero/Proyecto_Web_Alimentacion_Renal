import { getCurrentLang, translations } from './i18n.js';
import { showAlert, showConfirm, showToast } from './ui.js';

let currentThreadId = null;
let editingCommentId = null;

export async function initForum() {
    console.log('initForum: Initializing...');

    // Event Listeners
    setupForumEventListeners();
    console.log('initForum: Finished');
}

function setupForumEventListeners() {
    console.log('setupForumEventListeners: Setting up...');
    const newThreadBtn = document.getElementById('new-thread-btn');
    const newThreadModal = document.getElementById('new-thread-modal');
    const closeForumModal = document.getElementById('close-forum-modal');
    const cancelThreadBtn = document.getElementById('cancel-thread-btn');
    const newThreadForm = document.getElementById('new-thread-form');
    const backToForumBtn = document.getElementById('back-to-forum-btn');
    const commentForm = document.getElementById('comment-form');

    console.log('setupForumEventListeners: Elements found:', {
        newThreadBtn: !!newThreadBtn,
        newThreadModal: !!newThreadModal,
        newThreadForm: !!newThreadForm
    });

    if (newThreadBtn && newThreadModal) {
        newThreadBtn.addEventListener('click', () => {
            console.log('newThreadBtn: Clicked');
            newThreadModal.classList.add('active');
        });
    }

    const closeModal = () => {
        if (newThreadModal) newThreadModal.classList.remove('active');
    };
    if (closeForumModal) closeForumModal.addEventListener('click', closeModal);
    if (cancelThreadBtn) cancelThreadBtn.addEventListener('click', closeModal);

    if (newThreadForm) {
        newThreadForm.addEventListener('submit', handleNewThreadSubmit);
        console.log('setupForumEventListeners: Submit listener attached to newThreadForm');
    }

    if (backToForumBtn) {
        backToForumBtn.addEventListener('click', showThreadList);
    }

    if (commentForm) {
        commentForm.addEventListener('submit', handleCommentSubmit);
    }

    // Modal de Edición
    const editModal = document.getElementById('edit-forum-modal');
    const closeEditModal = document.getElementById('close-edit-modal');
    const cancelEditBtn = document.getElementById('cancel-edit-btn');
    const editForumForm = document.getElementById('edit-forum-form');

    const closeEModal = () => {
        if (editModal) editModal.classList.remove('active');
    };
    if (closeEditModal) closeEditModal.addEventListener('click', closeEModal);
    if (cancelEditBtn) cancelEditBtn.addEventListener('click', closeEModal);
    if (editForumForm) editForumForm.addEventListener('submit', handleEditFormSubmit);
}

export async function loadThreads() {
    const threadList = document.getElementById('thread-list');
    if (!threadList) return;

    try {
        const res = await fetch('/api/forum/threads');
        const threads = await res.json();

        if (threads.length === 0) {
            const t = translations[getCurrentLang()];
            threadList.innerHTML = `<p class="no-threads-msg" style="text-align: center; padding: 3rem; color: var(--text-muted); font-size: 1.1rem;">${t.noThreads || 'No threads yet.'}</p>`;
            return;
        }

        threadList.innerHTML = threads.map(thread => `
            <div class="thread-card" onclick="openThread(${thread.id})">
                <div class="thread-info">
                    <h3 class="thread-title">${escapeHTML(thread.title)}</h3>
                    <div class="thread-meta">
                        <strong style="color: var(--primary-color)">${escapeHTML(thread.author_name)}</strong>
                        <span style="opacity: 0.5">•</span>
                        <span>${new Date(thread.created_at).toLocaleString(getCurrentLang(), { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                </div>
                <div class="thread-stats">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
                    <span>${thread.comment_count}</span>
                </div>
            </div>
        `).join('');
    } catch (err) {
        console.error('Error loading threads:', err);
    }
}

export function refreshForumView() {
    const t = translations[getCurrentLang()];

    if (currentThreadId) {
        window.openThread(currentThreadId);
        // Si estábamos editando un comentario, el re-render de openThread -> loadComments
        // NO afecta al formulario de comentario (está fuera de #thread-detail y #comment-list)
        // Pero updateTexts() habrá puesto el botón de submit a "Publicar" si tiene data-i18n.
        if (editingCommentId) {
            const submitBtn = document.querySelector('#comment-form button[type="submit"]');
            if (submitBtn) submitBtn.textContent = t.saveChanges || 'Guardar Cambios';
            const cancelBtn = document.getElementById('cancel-edit-comment-btn');
            if (cancelBtn) cancelBtn.textContent = t.cancel || 'Cancelar';
        }
    } else {
        loadThreads();
    }
}

async function handleNewThreadSubmit(e) {
    e.preventDefault();
    console.log('handleNewThreadSubmit: Starting...');

    let user = null;
    try {
        const stored = localStorage.getItem('user');
        if (stored) user = JSON.parse(stored);
    } catch (err) {
        console.error('handleNewThreadSubmit: Error parsing user', err);
    }

    if (!user) {
        console.error('handleNewThreadSubmit: No user found');
        const t = translations[getCurrentLang()];
        showAlert(t.forum || 'Foro', t.errorLogin || 'Debes iniciar sesión', "❌");
        return;
    }

    const userId = user.id || user.userId || user.user_id;
    if (!userId) {
        console.error('handleNewThreadSubmit: User object missing ID', user);
        const t = translations[getCurrentLang()];
        showAlert(t.forum || 'Foro', 'Error de sesión (ID no encontrado)', "❌");
        return;
    }

    const titleEl = document.getElementById('thread-title');
    const contentEl = document.getElementById('thread-content');

    if (!titleEl || !contentEl) {
        console.error('handleNewThreadSubmit: Form elements not found', { titleEl: !!titleEl, contentEl: !!contentEl });
        return;
    }

    const title = titleEl.value;
    const content = contentEl.value;

    console.log('handleNewThreadSubmit: Payload', { userId, title, content });

    try {
        const res = await fetch('/api/forum/create_thread', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                title,
                content
            })
        });

        let data;
        try {
            data = await res.json();
        } catch (jsonErr) {
            console.error('handleNewThreadSubmit: Response is not JSON', jsonErr);
            throw new Error('Invalid JSON response');
        }

        console.log('handleNewThreadSubmit: Response', data);

        if (res.ok && data.status === 'success') {
            document.getElementById('new-thread-form').reset();
            document.getElementById('new-thread-modal').classList.remove('active');
            loadThreads();

            // Google Analytics: Thread Created
            if (typeof gtag === 'function') {
                gtag('event', 'create_thread', {
                    thread_title: title
                });
            }

            const t = translations[getCurrentLang()];
            showAlert(t.forum || 'Foro', t.threadCreated || '¡Tema creado!', "✅");
        } else {
            console.error('handleNewThreadSubmit: Error response', data);
            const t = translations[getCurrentLang()];
            showAlert(t.forum || 'Foro', data.message || data.error || t.errorGeneric || 'Error al crear el tema', "❌");
        }
    } catch (err) {
        console.error('handleNewThreadSubmit: Crash', err);
        const t = translations[getCurrentLang()];
        showAlert(t.forum || 'Foro', t.connectionError || 'Error de conexión', "❌");
    }
}

window.openThread = async function (threadId) {
    currentThreadId = threadId;
    const listView = document.getElementById('forum-list-view');
    const threadView = document.getElementById('forum-thread-view');
    const threadDetail = document.getElementById('thread-detail');

    listView.classList.add('hidden');
    threadView.classList.remove('hidden');
    window.scrollTo({ top: 0, behavior: 'smooth' });

    try {
        const res = await fetch('/api/forum/threads');
        const threads = await res.json();
        const thread = threads.find(t => t.id === threadId);

        if (thread) {
            threadDetail.innerHTML = `
                <div class="thread-detail-header">
                    <h2 class="thread-detail-title">${escapeHTML(thread.title)}</h2>
                    <div class="thread-author">
                        <img src="${thread.author_avatar || 'images/default_avatar.png'}" class="author-avatar" alt="Avatar">
                        <div class="author-info">
                            <strong>${escapeHTML(thread.author_name)}</strong>
                            <div class="thread-meta">
                                <span>${new Date(thread.created_at).toLocaleString(getCurrentLang(), { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })}</span>
                            </div>
                        </div>
                    </div>
                <div class="thread-content" id="thread-content-div-${thread.id}">${escapeHTML(thread.content)}</div>
            `;

            // Check Edit/Delete viability client-side to show buttons
            const userStr = localStorage.getItem('user');
            if (userStr) {
                const userObj = JSON.parse(userStr);
                const isOwner = String(userObj.id) === String(thread.user_id);
                // SQLite datetime es UTC nativamente, hay que parsearlo como estándar ISO para evitar timezone drift local.
                const threadDate = new Date(thread.created_at.replace(' ', 'T') + 'Z').getTime();
                const threadAge = new Date().getTime() - threadDate;
                const canModify = isOwner && (threadAge <= 10 * 60 * 1000);

                if (isOwner) {
                    const t = translations[getCurrentLang()];
                    const disabledAttr = canModify ? '' : 'disabled';
                    const opacityStyle = canModify ? '' : 'opacity: 0.5; cursor: not-allowed;';
                    const titleHint = canModify ? '' : `title="${t.timeExpiredHint || 'El tiempo para editar o eliminar ha expirado (10 min)'}"`;

                    threadDetail.innerHTML += `
                        <div class="thread-actions" style="margin-top: 20px; display: flex; gap: 10px; border-top: 1px solid var(--border-color, #e2e8f0); padding-top: 15px;">
                            <button class="btn-secondary btn-small" onclick="${canModify ? `editThread(${thread.id})` : ''}" ${disabledAttr} ${titleHint} style="display: flex; align-items: center; gap: 6px; ${opacityStyle}">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                                ${t.editThreadBtn || 'Editar tema'}
                            </button>
                            <button class="btn-small delete-menu" onclick="${canModify ? `deleteThread(${thread.id})` : ''}" ${disabledAttr} ${titleHint} style="display: flex; align-items: center; gap: 6px; ${opacityStyle}">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                                ${t.deleteBtn || 'Eliminar'}
                            </button>
                        </div>
                    `;
                }
            }

            loadComments(threadId);

            // Google Analytics: Thread View
            if (typeof gtag === 'function') {
                gtag('event', 'view_thread', {
                    thread_id: thread.id,
                    thread_title: thread.title
                });
            }
        }
    } catch (err) {
        console.error('Error loading thread detail:', err);
    }
};

async function loadComments(threadId) {
    const commentList = document.getElementById('comment-list');
    try {
        const res = await fetch(`/api/forum/comments?thread_id=${threadId}`);
        const comments = await res.json();

        const userStr = localStorage.getItem('user');
        const userObj = userStr ? JSON.parse(userStr) : null;
        const nowMs = new Date().getTime();

        commentList.innerHTML = comments.map(comment => {
            const isOwner = userObj && String(userObj.id) === String(comment.user_id);
            const commentDate = new Date(comment.created_at.replace(' ', 'T') + 'Z').getTime();
            const commentAge = nowMs - commentDate;
            const canModify = isOwner && (commentAge <= 10 * 60 * 1000);

            let actionsHTML = '';
            if (isOwner) {
                const t = translations[getCurrentLang()];
                const disabledAttr = canModify ? '' : 'disabled';
                const opacityStyle = canModify ? '' : 'opacity: 0.5; cursor: not-allowed;';
                const titleHint = canModify ? '' : `title="${t.timeExpiredHint || 'El tiempo para editar o borrar ha expirado (10 min)'}"`;

                actionsHTML = `
                    <div class="comment-actions" style="margin-top: 12px; display: flex; gap: 10px;">
                        <button class="btn-secondary btn-small" onclick="${canModify ? `editComment(${comment.id})` : ''}" ${disabledAttr} ${titleHint} style="display: flex; align-items: center; gap: 4px; padding: 4px 10px; ${opacityStyle}">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                            ${t.editBtn || 'Editar'}
                        </button>
                        <button class="btn-small delete-menu" onclick="${canModify ? `deleteComment(${comment.id})` : ''}" ${disabledAttr} ${titleHint} style="display: flex; align-items: center; gap: 4px; padding: 4px 10px; ${opacityStyle}">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                            ${t.deleteCommentBtn || 'Borrar'}
                        </button>
                    </div>
                `;
            }

            return `
            <div class="comment-card" data-comment-id="${comment.id}">
                <div class="comment-header">
                    <img src="${comment.author_avatar || 'images/default_avatar.png'}" class="author-avatar" style="width: 38px; height: 38px; border: 2px solid white; box-shadow: var(--shadow-sm);">
                    <div style="display: flex; flex-direction: column;">
                        <span class="comment-author-name">${escapeHTML(comment.author_name)}</span>
                        <span class="comment-date">${new Date(comment.created_at).toLocaleString(getCurrentLang(), { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                </div>
                <div class="comment-content" id="comment-content-div-${comment.id}">${escapeHTML(comment.content)}</div>
                ${actionsHTML}
            </div>
            `;
        }).join('');
    } catch (err) {
        console.error('Error loading comments:', err);
    }
}

async function handleCommentSubmit(e) {
    e.preventDefault();
    const user = JSON.parse(localStorage.getItem('user'));
    if (!user || !currentThreadId) return;

    const contentEl = document.getElementById('comment-content');
    const content = contentEl.value;

    try {
        let url = '/api/forum/create_comment';
        let body = {
            thread_id: currentThreadId,
            user_id: user.id,
            content
        };

        if (editingCommentId) {
            url = '/api/forum/edit_comment';
            body = {
                comment_id: editingCommentId,
                user_id: user.id,
                content
            };
        }

        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        const data = await res.json();
        const t = translations[getCurrentLang()];

        if (res.ok && data.status === 'success') {
            showToast(editingCommentId ? (t.commentUpdated || 'Comentario actualizado') : (t.commentPublished || 'Comentario publicado'), 'success');
            resetCommentForm();
            loadComments(currentThreadId);
            if (!editingCommentId) loadThreads(); // Refresh count only on new
        } else {
            showToast(data.error || t.errorGeneric || 'Error al procesar el comentario', 'error');
        }
    } catch (err) {
        console.error('Error in handleCommentSubmit:', err);
    }
}

function resetCommentForm() {
    editingCommentId = null;
    const form = document.getElementById('comment-form');
    if (form) {
        form.reset();
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.textContent = translations[getCurrentLang()].postComment || 'Publicar';
        }
    }
    const cancelBtn = document.getElementById('cancel-edit-comment-btn');
    if (cancelBtn) cancelBtn.remove();
}

function showThreadList() {
    document.getElementById('forum-list-view').classList.remove('hidden');
    document.getElementById('forum-thread-view').classList.add('hidden');
    currentThreadId = null;
}

// Funciones globales de EDICIÓN y BORRADO

window.deleteThread = async function (threadId) {
    const t = translations[getCurrentLang()];
    if (!(await showConfirm(t.deleteMenu || "Eliminar", t.deleteThreadConfirm || "¿Seguro que deseas eliminar este tema y todos sus comentarios? Esta acción no se puede deshacer."))) return;
    const user = JSON.parse(localStorage.getItem('user'));
    try {
        const res = await fetch('/api/forum/delete_thread', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ thread_id: threadId, user_id: user.id })
        });
        const data = await res.json();
        if (res.ok && data.status === 'success') {
            showToast(t.threadDeleted || 'Tema eliminado correctamente', 'success');
            showThreadList();
            loadThreads();
        } else {
            showToast(data.error || t.errorDelete || 'No se puede eliminar', 'error');
        }
    } catch (err) {
        console.error(err);
        showToast(t.connectionError || 'Error al conectar con el servidor', 'error');
    }
};

window.editThread = async function (threadId) {
    const editModal = document.getElementById('edit-forum-modal');
    const titleInput = document.getElementById('edit-thread-title');
    const contentInput = document.getElementById('edit-content');
    const itemIdInput = document.getElementById('edit-item-id');
    const itemTypeInput = document.getElementById('edit-item-type');
    const titleGroup = document.getElementById('edit-title-group');
    const modalTitle = document.getElementById('edit-modal-title');
    const t = translations[getCurrentLang()];

    // Configurar modal para Hilos
    if (modalTitle) modalTitle.textContent = t.editThreadTitle || "Editar Tema";
    itemIdInput.value = threadId;
    itemTypeInput.value = 'thread';
    titleGroup.style.display = 'block';

    // Obtener valores actuales (desde el DOM para rapidez)
    const currentTitle = document.querySelector(`.thread-detail-title`)?.innerText || "";
    const currentContent = document.getElementById(`thread-content-div-${threadId}`)?.innerText || "";

    titleInput.value = currentTitle;
    contentInput.value = currentContent;

    editModal.classList.add('active');
};

window.deleteComment = async function (commentId) {
    const t = translations[getCurrentLang()];
    if (!(await showConfirm(t.deleteMenu || "Eliminar", t.confirmDeleteComment || "¿Seguro que deseas eliminar el comentario?"))) return;
    const user = JSON.parse(localStorage.getItem('user'));
    try {
        const res = await fetch('/api/forum/delete_comment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ comment_id: commentId, user_id: user.id })
        });
        const data = await res.json();
        if (res.ok && data.status === 'success') {
            showToast(t.commentDeleted || 'Comentario eliminado', 'success');
            loadComments(currentThreadId);
            loadThreads();
        } else {
            showToast(data.error || t.errorGeneric || 'No se puede eliminar', 'error');
        }
    } catch (err) {
        console.error(err);
        showToast(t.errorGeneric || 'Error al eliminar el comentario', 'error');
    }
};

window.editComment = async function (commentId) {
    editingCommentId = commentId;
    const contentInput = document.getElementById('comment-content');
    const form = document.getElementById('comment-form');

    if (!contentInput || !form) return;

    const t = translations[getCurrentLang()];

    // Obtener contenido actual
    const currentContent = document.getElementById(`comment-content-div-${commentId}`)?.innerText || "";
    contentInput.value = currentContent;

    // Cambiar botón
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.textContent = t.saveChanges || 'Guardar Cambios';
    }

    // Añadir botón cancelar si no existe
    if (!document.getElementById('cancel-edit-comment-btn')) {
        const cancelBtn = document.createElement('button');
        cancelBtn.type = 'button';
        cancelBtn.id = 'cancel-edit-comment-btn';
        cancelBtn.className = 'btn-secondary';
        cancelBtn.style.marginRight = '10px';
        cancelBtn.setAttribute('data-i18n', 'cancel');
        cancelBtn.textContent = t.cancel || 'Cancelar';
        cancelBtn.onclick = resetCommentForm;
        submitBtn.parentNode.insertBefore(cancelBtn, submitBtn);
    }

    // Scroll al formulario
    form.scrollIntoView({ behavior: 'smooth', block: 'center' });
    contentInput.focus();
};

async function handleEditFormSubmit(e) {
    e.preventDefault();
    const itemId = document.getElementById('edit-item-id').value;
    const itemType = document.getElementById('edit-item-type').value;
    const title = document.getElementById('edit-thread-title').value;
    const content = document.getElementById('edit-content').value;
    const user = JSON.parse(localStorage.getItem('user'));

    if (!user || itemType !== 'thread') return;

    try {
        const res = await fetch('/api/forum/edit_thread', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                thread_id: itemId,
                user_id: user.id,
                title: title,
                content: content
            })
        });
        const data = await res.json();
        const t = translations[getCurrentLang()];

        if (res.ok && data.status === 'success') {
            showToast(t.threadUpdated || 'Tema actualizado correctamente', 'success');
            document.getElementById('edit-forum-modal').classList.remove('active');
            window.openThread(itemId);
        } else {
            showToast(data.error || t.errorDelete || 'No se puede editar', 'error');
        }
    } catch (err) {
        console.error('Error in handleEditFormSubmit:', err);
        showToast(t.errorGeneric || 'Error al guardar los cambios', 'error');
    }
}

function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
