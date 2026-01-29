const API_BASE = '/api';

export async function fetchUser(id) {
    try {
        const res = await fetch(`${API_BASE}/get_user?id=${id}`);
        if (!res.ok) throw new Error('Failed to fetch user');
        return await res.json();
    } catch (e) {
        console.error(e);
        return null;
    }
}

export async function fetchFoods() {
    try {
        const res = await fetch(`${API_BASE}/foods`);
        if (!res.ok) throw new Error('Failed to fetch foods');
        return await res.json();
    } catch (e) {
        console.error(e);
        return [];
    }
}

export async function login(email, password) {
    const res = await fetch(`${API_BASE}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
    });
    return res;
}

export async function register(data) {
    const res = await fetch(`${API_BASE}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    return res;
}

export async function requestPasswordReset(email) {
    const res = await fetch(`${API_BASE}/request_password_reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
    });
    return res;
}

export async function resetPassword(token, password) {
    const res = await fetch(`${API_BASE}/reset_password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, password })
    });
    return res;
}

export async function updateProfile(data) {
    const res = await fetch(`${API_BASE}/update_profile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    return res;
}

export async function uploadAvatar(email, imageData) {
    const res = await fetch(`${API_BASE}/upload_avatar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, image_data: imageData })
    });
    return res;
}

export async function sendFeedback(message) {
    const res = await fetch(`${API_BASE}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
    });
    return res;
}

export async function sendChatMessage(message, userId, history) {
    const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, userId, history })
    });
    return res;
}
