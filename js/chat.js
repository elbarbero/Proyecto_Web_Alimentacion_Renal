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
    let formatted = text.replace(/\n/g, '<br>');
    div.innerHTML = formatted;
    chatMessages.appendChild(div);
    scrollToBottom();

    if (save) {
        const history = localStorage.getItem('chat_history') ? JSON.parse(localStorage.getItem('chat_history')) : [];
        history.push({ text: text, className: className, timestamp: Date.now() });
        if (history.length > 50) history.shift();
        localStorage.setItem('chat_history', JSON.stringify(history));
    }
}

function scrollToBottom() {
    if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;
}
