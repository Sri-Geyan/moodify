/**
 * Playlist — render recommended tracks and export functionality.
 */
const playlist = {
    currentTracks: [],
    seedSong: null,

    /**
     * Render the full playlist results.
     */
    render(data) {
        this.currentTracks = data.tracks || [];
        this.seedSong = data.seed_song;

        // Update subtitle
        const subtitle = document.getElementById('results-subtitle');
        if (subtitle) {
            subtitle.textContent = `${this.currentTracks.length} songs · Based on "${data.seed_song.name}" · ${data.total_candidates} candidates analyzed`;
        }

        // Update vector DB count
        const dbCount = document.getElementById('db-count');
        if (dbCount) dbCount.textContent = data.vector_db_size || 0;

        // NLP prompt display
        if (data.natural_language_prompt) {
            const nlpDisplay = document.getElementById('nlp-display');
            const nlpText = document.getElementById('nlp-text');
            if (nlpDisplay) nlpDisplay.style.display = 'block';
            if (nlpText) nlpText.textContent = data.natural_language_prompt;
        }

        // Render track list
        this.renderTracks();

        // Hide export success if previously shown
        const exportSuccess = document.getElementById('export-success');
        if (exportSuccess) exportSuccess.style.display = 'none';
    },

    /**
     * Render individual track items.
     */
    renderTracks() {
        const container = document.getElementById('track-list');
        if (!container) return;

        container.innerHTML = this.currentTracks.map((track, index) => `
            <div class="track-item" id="track-${index}" style="animation: fadeIn 0.4s ${index * 0.05}s both var(--ease-smooth);">
                <span class="track-index">${index + 1}</span>
                <img class="track-art" 
                     src="${track.album_art_url || 'data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%2248%22 height=%2248%22><rect fill=%22%231a1a24%22 width=%2248%22 height=%2248%22/><text x=%2224%22 y=%2228%22 text-anchor=%22middle%22 fill=%22%236b6b80%22 font-size=%2220%22>♪</text></svg>'}" 
                     alt="${this._esc(track.name)}">
                <div class="track-info">
                    <div class="track-name">${this._esc(track.name)}</div>
                    <div class="track-artist">${this._esc(track.artist)}${track.album ? ' · ' + this._esc(track.album) : ''}</div>
                </div>
                <div class="track-score">
                    <div class="score-bar">
                        <div class="score-fill" style="width: ${Math.round(track.hybrid_score * 100)}%"></div>
                    </div>
                    <span class="score-value">${Math.round(track.hybrid_score * 100)}%</span>
                </div>
                <span class="track-expand" onclick="playlist.toggleDetails(${index})" title="Show details">
                    ▼
                </span>
                <div class="track-details" id="details-${index}">
                    <div class="track-explanation">${track.explanation || 'Selected based on AI similarity analysis.'}</div>
                    <div class="track-score-breakdown">
                        <span class="breakdown-item">
                            <span class="breakdown-dot emb"></span>
                            Embedding: ${Math.round(track.embedding_similarity * 100)}%
                        </span>
                        <span class="breakdown-item">
                            <span class="breakdown-dot genre"></span>
                            Genre: ${Math.round(track.genre_similarity * 100)}%
                        </span>
                        <span class="breakdown-item">
                            <span class="breakdown-dot artist"></span>
                            Artist: ${Math.round(track.artist_similarity * 100)}%
                        </span>
                        <span class="breakdown-item">
                            <span class="breakdown-dot pop"></span>
                            Popularity: ${Math.round(track.popularity_similarity * 100)}%
                        </span>
                    </div>
                    ${track.moods && track.moods.length > 0 ? `
                        <div class="track-mood-tags">
                            ${track.moods.map(m => `<span class="track-mood-tag">${m}</span>`).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
        `).join('');
    },

    /**
     * Toggle track details panel.
     */
    toggleDetails(index) {
        const details = document.getElementById(`details-${index}`);
        const expand = document.querySelector(`#track-${index} .track-expand`);
        if (details) {
            details.classList.toggle('open');
            if (expand) {
                expand.textContent = details.classList.contains('open') ? '▲' : '▼';
            }
        }
    },

    /**
     * Export current playlist to Spotify.
     */
    async export() {
        if (!this.currentTracks.length || !this.seedSong) return;

        const btn = document.getElementById('btn-export');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '⏳ Creating...';
        }

        try {
            const trackIds = this.currentTracks.map(t => t.spotify_id);
            const result = await API.createPlaylist(
                trackIds,
                this.seedSong.name,
                this.seedSong.artist,
            );

            // Show success
            const exportSuccess = document.getElementById('export-success');
            const exportLink = document.getElementById('export-link');
            if (exportSuccess) exportSuccess.style.display = 'block';
            if (exportLink) exportLink.href = result.playlist_url;

            // Scroll to success card
            exportSuccess?.scrollIntoView({ behavior: 'smooth', block: 'center' });

        } catch (error) {
            alert(`Failed to create playlist: ${error.message}`);
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = `
                    <svg class="spotify-icon-sm" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/></svg>
                    Export to Spotify
                `;
            }
        }
    },

    /**
     * HTML escape.
     */
    _esc(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    },
};
