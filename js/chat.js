import { sendChatMessage } from './api.js';
import { getCurrentLang, translations } from './i18n.js';

// DOM Elements
let chatWindow, chatInput, chatMessages;

export function setupChat() {
    // Initialize DOM references
    chatWindow = document.getElementById('chat-window');
    chatInput = document.getElementById('chat-input');
    chatMessages = document.getElementById('chat-messages');

    // Expose toggleChat globally for the button in HTML
    window.toggleChat = toggleChat;
    window.handleChatKey = (e) => {
        if (e.key === 'Enter') handleSendChatMessage();
    };
    window.sendChatMessage = handleSendChatMessage;

    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') handleSendChatMessage();
        });
    }

    // Initial Load
    // Check if chat is empty (first load or no history)
    if (!localStorage.getItem('chat_history') && chatMessages) {
        setWelcomeMessage();
    } else {
        loadChatHistory();
    }
}

function setWelcomeMessage() {
    if (!chatMessages) return;
    const lang = getCurrentLang();
    const t = translations[lang] || translations['es'];
    // We assume there's a key for this, if not we fallback to a simple string or add it to i18n
    // Ideally we should add 'chatWelcome' to i18n.js. For now manual Map:
    const welcomes = {
        es: "Hola, soy tu asistente virtual. ¿Tienes dudas sobre si puedes comer algún alimento con tu condición actual?",
        en: "Hello, I am your virtual assistant. Do you have any questions about what foods you can eat with your current condition?",
        de: "Hallo, ich bin Ihr virtueller Assistent. Haben Sie Fragen dazu, welche Lebensmittel Sie mit Ihrer aktuellen Erkrankung essen dürfen?",
        fr: "Bonjour, je suis votre assistant virtuel. Avez-vous des questions sur les aliments que vous pouvez manger avec votre état actuel ?",
        pt: "Olá, sou o seu assistente virtual. Tem dúvidas sobre se pode comer algum alimento com a sua condição atual?",
        ja: "こんにちは、バーチャルアシスタントです。現在の病状で食べられるものについて質問はありますか？"
    };

    const msg = welcomes[lang] || welcomes['es'];

    chatMessages.innerHTML = `
        <div class="message ai-message">
            ${msg}
        </div>
    `;
}

export function toggleChat() {
    chatWindow.classList.toggle('active');
    if (chatWindow.classList.contains('active')) {
        // Refresh welcome message if empty and just opened (in case of lang switch)
        if (!chatMessages.innerHTML.trim() || chatMessages.innerHTML.includes('Hola, soy tu asistente virtual') && getCurrentLang() !== 'es') {
            if (!localStorage.getItem('chat_history')) {
                setWelcomeMessage();
            }
        }

        if (chatInput) setTimeout(() => chatInput.focus(), 100);
        scrollToBottom();
    }
}

function loadChatHistory() {
    const history = localStorage.getItem('chat_history');
    if (history) {
        try {
            const msgs = JSON.parse(history);
            if (msgs.length > 0 && chatMessages) chatMessages.innerHTML = '';

            msgs.forEach(m => {
                addMessage(m.text, m.className, false);
            });
        } catch (e) {
            console.error("Error loading chat history", e);
        }
    }
}

export function clearChatHistory() {
    localStorage.removeItem('chat_history');
    setWelcomeMessage();
}

async function handleSendChatMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    addMessage(text, 'user-message');
    chatInput.value = '';

    // Typing Indicator
    const typingId = 'typing-' + Date.now();
    const typingDiv = document.createElement('div');
    typingDiv.id = typingId;
    typingDiv.className = 'typing-indicator';
    typingDiv.textContent = 'Escribiendo...';
    chatMessages.appendChild(typingDiv);
    scrollToBottom();

    // Get User ID
    const storedUser = localStorage.getItem('user');
    let userId = null;
    if (storedUser) {
        userId = JSON.parse(storedUser).id;
    }

    // Prepare History
    let history = [];
    const rawHistory = localStorage.getItem('chat_history');
    if (rawHistory) {
        try {
            const parsed = JSON.parse(rawHistory);

            // We just added the current message to localStorage in addMessage(),
            // so we must exclude it from the history we send to the API, 
            // otherwise the backend will append it again and create a "User, User" violation.
            // We take everything up to the last element.
            const pastHistory = parsed.slice(0, -1);

            // Limit to last 12 messages from the past
            history = pastHistory.slice(-12).map(msg => ({
                role: msg.className === 'user-message' ? 'user' : 'model',
                text: msg.text
            }));
        } catch (e) {
            console.error(e);
        }
    }

    try {
        const res = await sendChatMessage(text, userId, history);
        const data = await res.json();

        const typingEl = document.getElementById(typingId);
        if (typingEl) typingEl.remove();

        if (data.response) {
            addMessage(data.response, 'ai-message');
        } else if (data.error) {
            console.error("Chat Server Error:", data.error); // Log real error

            const lang = getCurrentLang();
            if (lang === 'es') {
                addMessage("Lo siento, hubo un error técnico. Inténtalo de nuevo.", 'ai-message');
            } else {
                addMessage("Sorry, there was a technical error. Please try again.", 'ai-message');
            }
        }
    } catch (err) {
        console.error(err);
        const typingEl = document.getElementById(typingId);
        if (typingEl) typingEl.remove();
        addMessage("Error de conexión.", 'ai-message');
    }
}

function addMessage(text, className, save = true) {
    if (!chatMessages) return;

    const div = document.createElement('div');
    div.className = `message ${className}`;

    // Basic Markdown Formatting
    let formatted = text;

    // Headers: ### text -> 3 text
    formatted = formatted.replace(/### (.*?)$/gm, '<h3>$1</h3>');

    // Bold: **text**
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Tables: | Header | ... | \n | --- | ... |
    // Simple parser: find blocks that look like tables
    const tableRegex = /((?:\|.*\|(?:\r?\n|$))+)/g;

    formatted = formatted.replace(tableRegex, (match) => {
        const lines = match.trim().split('\n').map(l => l.trim());
        if (lines.length < 2) return match; // Not a table

        // Check for separator line |---|
        const separatorIndex = lines.findIndex(l => /^\|[\s-:]+\|[\s-:|]*$/.test(l));
        if (separatorIndex === -1) return match; // No separator found

        let html = '<div class="table-container"><table>';

        // Header
        const headerRow = lines[0];
        const headers = headerRow.split('|').filter(c => c.trim() !== '').map(c => c.trim());
        html += '<thead><tr>' + headers.map(h => `<th>${h}</th>`).join('') + '</tr></thead>';

        // Body
        html += '<tbody>';
        for (let i = 0; i < lines.length; i++) {
            if (i === 0 || i === separatorIndex) continue; // Skip header and separator
            const row = lines[i];
            const cells = row.split('|').filter((c, idx, arr) => {
                // Filter out empty start/end logic if standard md table
                if (idx === 0 && c.trim() === '') return false;
                if (idx === arr.length - 1 && c.trim() === '') return false;
                return true;
            }).map(c => c.trim());

            if (cells.length) {
                html += '<tr>' + cells.map(c => `<td>${c}</td>`).join('') + '</tr>';
            }
        }
        html += '</tbody></table></div>';
        return html;
    });

    // Lists: - item or * item (at start of line)
    // We split by newline to handle list items correctly (excluding lines that are now HTML tables)
    // Note: This split logic is tricky with embedded HTML. 
    // Simplified strategy: If a line is part of a table (starts with <div or <table or <tbody etc, skip list parsing)
    // Ideally we would parse linewise first.
    // For now, let's just do a simple pass that avoids touching HTML tags if possible, or accept that tables are already formatted.

    // HOWEVER, since we did replace() above, the table is now a single huge line of HTML.
    // So splitting by \n might behave oddly if the table html contains newlines (we stripped them but verify).

    formatted = formatted.split('\n').map(line => {
        line = line.trim();
        if (line.startsWith('<div class="table-container">')) return line; // Already formatted table block
        if (line.startsWith('<h3>')) return line;
        if (line.startsWith('- ') || line.startsWith('* ')) {
            return `<li>${line.substring(2)}</li>`;
        }
        return line ? `<p>${line}</p>` : '<br>';
    }).join('');

    div.innerHTML = formatted;
    chatMessages.appendChild(div);
    scrollToBottom();

    if (save) {
        const history = localStorage.getItem('chat_history') ? JSON.parse(localStorage.getItem('chat_history')) : [];
        history.push({ text: text, className: className, timestamp: Date.now() });
        if (history.length > 50) history.shift();
        localStorage.setItem('chat_history', JSON.stringify(history));
    }

    // Add Download Button for AI messages (Menus/Recipes)
    if (className.includes('ai-message')) {
        const user = localStorage.getItem('user');
        if (user) {
            const btn = document.createElement('button');
            btn.className = 'download-pdf-btn';
            btn.innerHTML = '📄 Descargar (PDF)';
            btn.style.cssText = 'margin-top: 10px; padding: 5px 10px; border-radius: 5px; border: 1px solid #ddd; background: white; cursor: pointer; font-size: 0.8rem; display: block;';

            btn.addEventListener('click', async () => {
                const u = JSON.parse(user);
                btn.textContent = 'Generando...';
                try {
                    const response = await fetch('/api/generate_pdf', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ userId: u.id, text: text })
                    });

                    if (response.ok) {
                        const blob = await response.blob();
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = "menu_renal.pdf";
                        document.body.appendChild(a);
                        a.click();
                        a.remove();
                        btn.textContent = '📄 Descargar (PDF)';
                    } else {
                        btn.textContent = 'Error';
                    }
                } catch (e) {
                    console.error(e);
                    btn.textContent = 'Error';
                }
            });
            div.appendChild(btn);
        }
    }
}

function scrollToBottom() {
    if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;
}
