/**
 * Mood — radar chart visualization and mood tag rendering.
 */
const mood = {
    /**
     * Render the full mood visualization.
     */
    render(moodProfile) {
        const section = document.getElementById('mood-section');
        if (!section) return;

        this.renderRadar(moodProfile);
        this.renderTags(moodProfile);
        this.renderMeters(moodProfile);
        this.renderDescription(moodProfile);

        section.style.display = 'block';
    },

    /**
     * Draw the radar chart on canvas.
     */
    renderRadar(profile) {
        const canvas = document.getElementById('mood-radar');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const w = canvas.width;
        const h = canvas.height;
        const cx = w / 2;
        const cy = h / 2;
        const radius = Math.min(cx, cy) - 40;

        ctx.clearRect(0, 0, w, h);

        // Data points
        const labels = ['Intensity', 'Energy', 'Valence', 'Mood Depth', 'Thematic'];
        const values = [
            profile.emotional_intensity || 0,
            profile.energy_level || 0,
            profile.valence || 0,
            Math.min((profile.moods?.length || 0) / 5, 1),
            Math.min((profile.themes?.length || 0) / 5, 1),
        ];
        const n = labels.length;
        const angleStep = (2 * Math.PI) / n;
        const startAngle = -Math.PI / 2; // Start from top

        // Draw background rings
        for (let ring = 1; ring <= 4; ring++) {
            const r = (radius * ring) / 4;
            ctx.beginPath();
            for (let i = 0; i <= n; i++) {
                const angle = startAngle + i * angleStep;
                const x = cx + r * Math.cos(angle);
                const y = cy + r * Math.sin(angle);
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }
            ctx.closePath();
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
            ctx.lineWidth = 1;
            ctx.stroke();
        }

        // Draw axis lines
        for (let i = 0; i < n; i++) {
            const angle = startAngle + i * angleStep;
            ctx.beginPath();
            ctx.moveTo(cx, cy);
            ctx.lineTo(cx + radius * Math.cos(angle), cy + radius * Math.sin(angle));
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
            ctx.lineWidth = 1;
            ctx.stroke();
        }

        // Draw data polygon
        ctx.beginPath();
        for (let i = 0; i <= n; i++) {
            const idx = i % n;
            const angle = startAngle + idx * angleStep;
            const r = radius * values[idx];
            const x = cx + r * Math.cos(angle);
            const y = cy + r * Math.sin(angle);
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.closePath();

        // Gradient fill
        const gradient = ctx.createLinearGradient(cx - radius, cy - radius, cx + radius, cy + radius);
        gradient.addColorStop(0, 'rgba(139, 92, 246, 0.2)');
        gradient.addColorStop(1, 'rgba(244, 63, 94, 0.15)');
        ctx.fillStyle = gradient;
        ctx.fill();

        // Gradient stroke
        ctx.strokeStyle = 'rgba(139, 92, 246, 0.6)';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Draw data points
        for (let i = 0; i < n; i++) {
            const angle = startAngle + i * angleStep;
            const r = radius * values[i];
            const x = cx + r * Math.cos(angle);
            const y = cy + r * Math.sin(angle);

            // Glow
            ctx.beginPath();
            ctx.arc(x, y, 6, 0, 2 * Math.PI);
            ctx.fillStyle = 'rgba(139, 92, 246, 0.3)';
            ctx.fill();

            // Point
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, 2 * Math.PI);
            ctx.fillStyle = '#8B5CF6';
            ctx.fill();
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.8)';
            ctx.lineWidth = 1.5;
            ctx.stroke();
        }

        // Draw labels
        ctx.font = '500 11px Inter, sans-serif';
        ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        for (let i = 0; i < n; i++) {
            const angle = startAngle + i * angleStep;
            const labelR = radius + 22;
            const x = cx + labelR * Math.cos(angle);
            const y = cy + labelR * Math.sin(angle);
            ctx.fillText(labels[i], x, y);
        }
    },

    /**
     * Render mood/theme/atmosphere tags.
     */
    renderTags(profile) {
        const container = document.getElementById('mood-tags');
        if (!container) return;

        let html = '';

        (profile.moods || []).forEach(m => {
            html += `<span class="mood-tag mood">${m}</span>`;
        });
        (profile.themes || []).forEach(t => {
            html += `<span class="mood-tag theme">${t}</span>`;
        });
        (profile.atmosphere || []).forEach(a => {
            html += `<span class="mood-tag atmos">${a}</span>`;
        });

        container.innerHTML = html;
    },

    /**
     * Render the intensity/energy/valence meters with animation.
     */
    renderMeters(profile) {
        // Animate meters with a slight delay
        setTimeout(() => {
            this._setMeter('intensity', profile.emotional_intensity || 0);
            this._setMeter('energy', profile.energy_level || 0);
            this._setMeter('valence', profile.valence || 0);
        }, 200);
    },

    _setMeter(name, value) {
        const fill = document.getElementById(`meter-${name}`);
        const val = document.getElementById(`val-${name}`);
        if (fill) fill.style.width = `${value * 100}%`;
        if (val) val.textContent = Math.round(value * 100);
    },

    /**
     * Render the mood description.
     */
    renderDescription(profile) {
        const el = document.getElementById('mood-description');
        if (el) {
            el.textContent = profile.description || 'Analyzing emotional character...';
        }
    },
};
