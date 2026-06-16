/**
 * API Client — handles all backend communication with auth headers.
 */
const API = {
    // Empty string means it will use the current host (works for both local and Render if served from same origin)
    BASE_URL: '',
    token: null,

    /**
     * Set the session token for authenticated requests.
     */
    setToken(token) {
        this.token = token;
        localStorage.setItem('moodify_token', token);
    },

    /**
     * Get stored token from localStorage.
     */
    getToken() {
        if (!this.token) {
            this.token = localStorage.getItem('moodify_token');
        }
        return this.token;
    },

    /**
     * Clear stored token.
     */
    clearToken() {
        this.token = null;
        localStorage.removeItem('moodify_token');
    },

    /**
     * Build headers with auth token.
     */
    _headers(extra = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...extra,
        };
        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        return headers;
    },

    /**
     * Generic fetch wrapper with error handling.
     */
    async _fetch(endpoint, options = {}) {
        const url = `${this.BASE_URL}${endpoint}`;
        const response = await fetch(url, {
            ...options,
            headers: this._headers(options.headers),
        });

        if (response.status === 401) {
            // Try to refresh token
            const refreshed = await this.refreshToken();
            if (refreshed) {
                // Retry with new token
                const retryResponse = await fetch(url, {
                    ...options,
                    headers: this._headers(options.headers),
                });
                if (!retryResponse.ok) {
                    throw new Error(`API Error: ${retryResponse.status}`);
                }
                return retryResponse.json();
            }
            this.clearToken();
            throw new Error('Authentication expired');
        }

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `API Error: ${response.status}`);
        }

        return response.json();
    },

    // --- Auth ---
    async getMe() {
        return this._fetch('/auth/me');
    },

    async refreshToken() {
        try {
            const data = await this._fetch('/auth/refresh', { method: 'POST' });
            if (data.token) {
                this.setToken(data.token);
                return true;
            }
        } catch {
            return false;
        }
        return false;
    },

    // --- Songs ---
    async searchSongs(query, limit = 10) {
        return this._fetch(`/songs/search?q=${encodeURIComponent(query)}&limit=${limit}`);
    },

    async getSong(spotifyId) {
        return this._fetch(`/songs/${spotifyId}`);
    },

    // --- Recommendations ---
    async getRecommendations(seedSpotifyId, playlistLength = 20, nlpPrompt = null) {
        return this._fetch('/recommend', {
            method: 'POST',
            body: JSON.stringify({
                seed_spotify_id: seedSpotifyId,
                playlist_length: playlistLength,
                natural_language_prompt: nlpPrompt || null,
            }),
        });
    },

    // --- Playlists ---
    async createPlaylist(trackIds, seedName, seedArtist, name = '') {
        return this._fetch('/playlists/create', {
            method: 'POST',
            body: JSON.stringify({
                track_spotify_ids: trackIds,
                seed_song_name: seedName,
                seed_artist: seedArtist,
                name: name,
            }),
        });
    },

    // --- Health ---
    async healthCheck() {
        return this._fetch('/health');
    },
};
