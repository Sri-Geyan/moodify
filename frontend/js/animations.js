/**
 * Animations — particle background and micro-animations.
 */
const animations = {
    particles: [],
    canvas: null,
    ctx: null,
    animationId: null,

    /**
     * Initialize the particle background.
     */
    init() {
        this.canvas = document.getElementById('particle-canvas');
        if (!this.canvas) return;

        this.ctx = this.canvas.getContext('2d');
        this.resize();
        this.createParticles();
        this.animate();

        window.addEventListener('resize', () => this.resize());
    },

    /**
     * Resize canvas to window size.
     */
    resize() {
        if (!this.canvas) return;
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    },

    /**
     * Create floating particles.
     */
    createParticles() {
        this.particles = [];
        const count = Math.floor(window.innerWidth / 25);

        for (let i = 0; i < count; i++) {
            this.particles.push({
                x: Math.random() * window.innerWidth,
                y: Math.random() * window.innerHeight,
                size: Math.random() * 2 + 0.5,
                speedX: (Math.random() - 0.5) * 0.3,
                speedY: (Math.random() - 0.5) * 0.3,
                opacity: Math.random() * 0.3 + 0.05,
                hue: Math.random() > 0.5 ? 142 : 262, // Green or purple
            });
        }
    },

    /**
     * Animation loop.
     */
    animate() {
        if (!this.ctx || !this.canvas) return;

        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        for (const p of this.particles) {
            // Update position
            p.x += p.speedX;
            p.y += p.speedY;

            // Wrap around
            if (p.x < 0) p.x = this.canvas.width;
            if (p.x > this.canvas.width) p.x = 0;
            if (p.y < 0) p.y = this.canvas.height;
            if (p.y > this.canvas.height) p.y = 0;

            // Draw
            this.ctx.beginPath();
            this.ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            this.ctx.fillStyle = `hsla(${p.hue}, 70%, 60%, ${p.opacity})`;
            this.ctx.fill();
        }

        // Draw connections between nearby particles
        for (let i = 0; i < this.particles.length; i++) {
            for (let j = i + 1; j < this.particles.length; j++) {
                const dx = this.particles[i].x - this.particles[j].x;
                const dy = this.particles[i].y - this.particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < 100) {
                    this.ctx.beginPath();
                    this.ctx.moveTo(this.particles[i].x, this.particles[i].y);
                    this.ctx.lineTo(this.particles[j].x, this.particles[j].y);
                    this.ctx.strokeStyle = `rgba(139, 92, 246, ${0.05 * (1 - dist / 100)})`;
                    this.ctx.lineWidth = 0.5;
                    this.ctx.stroke();
                }
            }
        }

        this.animationId = requestAnimationFrame(() => this.animate());
    },

    /**
     * Stop animation.
     */
    stop() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
    },
};
