import { getCurrentLang, translations } from './i18n.js';
import { showAlert } from './ui.js';

let currentThreadId = null;

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
                        <span>${new Date(thread.created_at).toLocaleDateString()}</span>
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
        showAlert('Foro', 'Error de sesión (ID no encontrado)', "❌");
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
                                <span>${new Date(thread.created_at).toLocaleDateString()}</span>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="thread-content">${escapeHTML(thread.content)}</div>
            `;
            loadComments(threadId);
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

        commentList.innerHTML = comments.map(comment => `
            <div class="comment-card">
                <div class="comment-header">
                    <img src="${comment.author_avatar || 'images/default_avatar.png'}" class="author-avatar" style="width: 38px; height: 38px; border: 2px solid white; box-shadow: var(--shadow-sm);">
                    <div style="display: flex; flex-direction: column;">
                        <span class="comment-author-name">${escapeHTML(comment.author_name)}</span>
                        <span class="comment-date">${new Date(comment.created_at).toLocaleDateString()}</span>
                    </div>
                </div>
                <div class="comment-content">${escapeHTML(comment.content)}</div>
            </div>
        `).join('');
    } catch (err) {
        console.error('Error loading comments:', err);
    }
}

async function handleCommentSubmit(e) {
    e.preventDefault();
    const user = JSON.parse(localStorage.getItem('user'));
    if (!user || !currentThreadId) return;

    const content = document.getElementById('comment-content').value;

    try {
        const res = await fetch('/api/forum/create_comment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                thread_id: currentThreadId,
                user_id: user.id,
                content
            })
        });

        if (res.ok) {
            document.getElementById('comment-form').reset();
            loadComments(currentThreadId);
            // Update thread list in background to refresh comment count
            loadThreads();
        }
    } catch (err) {
        console.error('Error posting comment:', err);
    }
}

function showThreadList() {
    document.getElementById('forum-list-view').classList.remove('hidden');
    document.getElementById('forum-thread-view').classList.add('hidden');
    currentThreadId = null;
}

function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
