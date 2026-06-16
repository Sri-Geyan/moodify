/**
 * App — main application controller.
 */
const app = {
    currentSeed: null,
    lastRecommendationData: null,

    /**
     * Initialize the application.
     */
    async init() {
        // Start animations
        animations.init();

        // Initialize search
        search.init();

        // Setup playlist length slider
        const slider = document.getElementById('playlist-length');
        const sliderVal = document.getElementById('playlist-length-val');
        if (slider && sliderVal) {
            slider.addEventListener('input', () => {
                sliderVal.textContent = `${slider.value} songs`;
            });
        }

        // Handle auth callback
        const hasAuth = await auth.handleCallback();

        if (hasAuth) {
            // Check if token is still valid
            const user = await auth.checkAuth();
            if (user) {
                auth.displayUser(user);
                this.showScreen('main');
                this.loadDbStatus();
                return;
            }
        }

        // Show login
        this.showScreen('login');
    },

    /**
     * Switch between screens.
     */
    showScreen(screenName) {
        document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
        const screen = document.getElementById(`${screenName}-screen`);
        if (screen) screen.classList.add('active');
    },

    /**
     * Load vector database status.
     */
    async loadDbStatus() {
        try {
            const health = await API.healthCheck();
            const dbCount = document.getElementById('db-count');
            if (dbCount) dbCount.textContent = health.vector_count || 0;
        } catch (e) {
            console.error('Health check failed:', e);
        }
    },

    /**
     * Select a seed song and display its details.
     */
    async selectSeedSong(spotifyId) {
        try {
            const song = await API.getSong(spotifyId);
            this.currentSeed = song;

            // Update seed display
            document.getElementById('seed-name').textContent = song.name;
            document.getElementById('seed-artist').textContent = song.artist;
            document.getElementById('seed-album').textContent = song.album || '';
            document.getElementById('seed-popularity').textContent = `${song.popularity}% popularity`;

            const artEl = document.getElementById('seed-art');
            if (artEl && song.album_art_url) {
                artEl.src = song.album_art_url;
                // Apply glow effect using album art color
                document.querySelector('.seed-art-glow').style.background =
                    `url(${song.album_art_url}) center/cover`;
            }

            // Genres
            const genresEl = document.getElementById('seed-genres');
            if (genresEl) {
                genresEl.innerHTML = (song.genres || [])
                    .map(g => `<span class="genre-tag">${g}</span>`)
                    .join('');
            }

            // Show mood if already analyzed
            if (song.mood_profile) {
                mood.render(song.mood_profile);
            } else {
                document.getElementById('mood-section').style.display = 'none';
            }

            // Show seed section
            document.getElementById('seed-section').style.display = 'block';

            // Hide results from previous generation
            document.getElementById('results-section').style.display = 'none';

            // Scroll to seed card
            document.getElementById('seed-section').scrollIntoView({
                behavior: 'smooth',
                block: 'start',
            });

        } catch (error) {
            console.error('Failed to load song:', error);
            alert(`Failed to load song details: ${error.message}`);
        }
    },

    /**
     * Generate AI playlist.
     */
    async generatePlaylist() {
        if (!this.currentSeed) return;

        const btn = document.getElementById('btn-generate');
        const playlistLength = parseInt(document.getElementById('playlist-length')?.value || '20');
        const nlpPrompt = document.getElementById('nlp-input')?.value?.trim() || null;

        // Disable button
        if (btn) btn.disabled = true;

        // Show loading
        document.getElementById('results-section').style.display = 'none';
        document.getElementById('loading-section').style.display = 'flex';

        // Animate loading steps
        this._animateLoading();

        // Scroll to loading
        document.getElementById('loading-section').scrollIntoView({
            behavior: 'smooth',
            block: 'center',
        });

        try {
            const data = await API.getRecommendations(
                this.currentSeed.spotify_id,
                playlistLength,
                nlpPrompt,
            );

            this.lastRecommendationData = data;

            // Update mood visualization with the analysis
            if (data.seed_mood_profile) {
                mood.render(data.seed_mood_profile);
            }

            // Hide loading, show results
            document.getElementById('loading-section').style.display = 'none';
            document.getElementById('results-section').style.display = 'block';

            // Render playlist
            playlist.render(data);

            // Scroll to results
            document.getElementById('results-section').scrollIntoView({
                behavior: 'smooth',
                block: 'start',
            });

        } catch (error) {
            console.error('Generation failed:', error);
            document.getElementById('loading-section').style.display = 'none';
            alert(`Playlist generation failed: ${error.message}`);
        } finally {
            if (btn) btn.disabled = false;
        }
    },

    /**
     * Regenerate playlist with the same seed.
     */
    async regenerate() {
        await this.generatePlaylist();
    },

    /**
     * Export playlist to Spotify.
     */
    async exportToSpotify() {
        await playlist.export();
    },

    /**
     * Animate the loading steps.
     */
    _animateLoading() {
        const steps = [
            { text: 'Fetching lyrics and metadata...', progress: 15 },
            { text: 'Extracting mood and themes with AI...', progress: 35 },
            { text: 'Generating emotional embeddings...', progress: 55 },
            { text: 'Searching vector database...', progress: 70 },
            { text: 'Computing hybrid similarity scores...', progress: 85 },
            { text: 'Applying diversity constraints...', progress: 95 },
        ];

        const stepEl = document.getElementById('loading-step');
        const barEl = document.getElementById('loading-progress-bar');

        steps.forEach((step, i) => {
            setTimeout(() => {
                if (stepEl) stepEl.textContent = step.text;
                if (barEl) barEl.style.width = `${step.progress}%`;
            }, i * 1200);
        });
    },
};

// --- Bootstrap ---
document.addEventListener('DOMContentLoaded', () => {
    app.init();
});
