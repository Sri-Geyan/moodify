/**
 * Auth — Spotify authentication flow management.
 */
const auth = {
    /**
     * Redirect to Spotify login.
     */
    login() {
        window.location.href = `${API.BASE_URL}/auth/login`;
    },

    /**
     * Handle auth callback — check URL params for token.
     */
    async handleCallback() {
        const params = new URLSearchParams(window.location.search);
        const authStatus = params.get('auth');
        const token = params.get('token');

        if (authStatus === 'success' && token) {
            API.setToken(token);
            // Clean URL
            window.history.replaceState({}, '', window.location.pathname);
            return true;
        }

        if (authStatus === 'error') {
            console.error('Auth error:', params.get('message'));
            window.history.replaceState({}, '', window.location.pathname);
            return false;
        }

        // Check existing token
        return API.getToken() !== null;
    },

    /**
     * Check if user is authenticated and load profile.
     */
    async checkAuth() {
        const token = API.getToken();
        if (!token) return null;

        try {
            const status = await API.getMe();
            if (status.authenticated && status.user) {
                return status.user;
            }
        } catch (e) {
            console.error('Auth check failed:', e);
        }

        API.clearToken();
        return null;
    },

    /**
     * Logout — clear token and redirect to login screen.
     */
    logout() {
        API.clearToken();
        app.showScreen('login');
    },

    /**
     * Update the UI with user profile info.
     */
    displayUser(user) {
        const nameEl = document.getElementById('user-name');
        const avatarEl = document.getElementById('user-avatar');

        if (nameEl) nameEl.textContent = user.display_name || user.id;
        if (avatarEl) {
            if (user.images && user.images.length > 0) {
                avatarEl.src = user.images[0].url;
                avatarEl.style.display = 'block';
            } else {
                avatarEl.style.display = 'none';
            }
        }
    },
};
