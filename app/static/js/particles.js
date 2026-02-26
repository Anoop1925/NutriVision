/* ═══════════════════════════════════════════════════════════
   particles.js — Subtle floating background dots
   ═══════════════════════════════════════════════════════════ */
(() => {
  const canvas = document.getElementById("particles");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  let W, H;
  const COUNT = 60;
  const particles = [];

  function resize() {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }

  function rand(a, b) { return Math.random() * (b - a) + a; }

  class Dot {
    constructor() { this.reset(); }
    reset() {
      this.x = rand(0, W);
      this.y = rand(0, H);
      this.r = rand(1.2, 2.8);
      this.dx = rand(-0.15, 0.15);
      this.dy = rand(-0.1, 0.1);
      this.o = rand(0.08, 0.22);
    }
    update() {
      this.x += this.dx;
      this.y += this.dy;
      if (this.x < -10 || this.x > W + 10 || this.y < -10 || this.y > H + 10) this.reset();
    }
    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(34,197,94,${this.o})`;
      ctx.fill();
    }
  }

  function init() {
    resize();
    particles.length = 0;
    for (let i = 0; i < COUNT; i++) particles.push(new Dot());
  }

  function frame() {
    ctx.clearRect(0, 0, W, H);

    // draw connections
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 140) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(34,197,94,${0.04 * (1 - dist / 140)})`;
          ctx.lineWidth = 0.6;
          ctx.stroke();
        }
      }
    }

    for (const p of particles) {
      p.update();
      p.draw();
    }
    requestAnimationFrame(frame);
  }

  window.addEventListener("resize", resize);
  init();
  frame();
})();
