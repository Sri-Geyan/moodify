/**
 * Search — song search with debounced input and results display.
 */
const search = {
    debounceTimer: null,
    isSearching: false,

    /**
     * Initialize search input listeners.
     */
    init() {
        const input = document.getElementById('search-input');
        if (!input) return;

        input.addEventListener('input', (e) => {
            clearTimeout(this.debounceTimer);
            const query = e.target.value.trim();

            if (query.length < 2) {
                this.clearResults();
                return;
            }

            this.debounceTimer = setTimeout(() => {
                this.performSearch(query);
            }, 350);
        });

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.clearResults();
                input.blur();
            }
        });

        // Close results when clicking outside
        document.addEventListener('click', (e) => {
            const resultsEl = document.getElementById('search-results');
            const searchBar = document.querySelector('.search-bar');
            if (resultsEl && !searchBar.contains(e.target)) {
                this.clearResults();
            }
        });
    },

    /**
     * Perform search via API.
     */
    async performSearch(query) {
        if (this.isSearching) return;
        this.isSearching = true;
        this.showSpinner(true);

        try {
            const data = await API.searchSongs(query);
            this.renderResults(data.tracks);
        } catch (error) {
            console.error('Search failed:', error);
            this.renderError('Search failed. Please try again.');
        } finally {
            this.isSearching = false;
            this.showSpinner(false);
        }
    },

    /**
     * Render search results dropdown.
     */
    renderResults(tracks) {
        const container = document.getElementById('search-results');
        if (!container) return;

        if (!tracks || tracks.length === 0) {
            container.innerHTML = `
                <div class="search-result-item" style="justify-content: center; color: var(--text-tertiary);">
                    No songs found. Try a different search.
                </div>
            `;
            container.classList.add('open');
            return;
        }

        container.innerHTML = tracks.map(track => `
            <div class="search-result-item" onclick="search.selectTrack('${track.spotify_id}', this)" data-id="${track.spotify_id}">
                <img class="search-result-art" 
                     src="${track.album_art_url || 'data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%2248%22 height=%2248%22><rect fill=%22%231a1a24%22 width=%2248%22 height=%2248%22/><text x=%2224%22 y=%2228%22 text-anchor=%22middle%22 fill=%22%236b6b80%22 font-size=%2220%22>♪</text></svg>'}" 
                     alt="${track.name}">
                <div class="search-result-info">
                    <div class="search-result-name">${this._escapeHtml(track.name)}</div>
                    <div class="search-result-artist">${this._escapeHtml(track.artist)}${track.album ? ' · ' + this._escapeHtml(track.album) : ''}</div>
                </div>
                <div class="search-result-popularity">${track.popularity}%</div>
            </div>
        `).join('');

        container.classList.add('open');
    },

    /**
     * Handle track selection from search results.
     */
    async selectTrack(spotifyId) {
        this.clearResults();
        document.getElementById('search-input').value = '';
        app.selectSeedSong(spotifyId);
    },

    /**
     * Render error message.
     */
    renderError(message) {
        const container = document.getElementById('search-results');
        if (container) {
            container.innerHTML = `
                <div class="search-result-item" style="justify-content: center; color: var(--accent-rose);">
                    ${message}
                </div>
            `;
            container.classList.add('open');
        }
    },

    /**
     * Clear search results.
     */
    clearResults() {
        const container = document.getElementById('search-results');
        if (container) {
            container.classList.remove('open');
            setTimeout(() => { container.innerHTML = ''; }, 300);
        }
    },

    /**
     * Show/hide the search spinner.
     */
    showSpinner(show) {
        const spinner = document.getElementById('search-spinner');
        if (spinner) {
            spinner.classList.toggle('active', show);
        }
    },

    /**
     * HTML escape helper.
     */
    _escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
};
