/* ── THEME ───────────────────────────────────────────────────────────────────── */
const html = document.documentElement;
const themeBtn = document.getElementById('themeToggle');
const themeIcon = themeBtn?.querySelector('.theme-icon');

function applyTheme(t) {
  html.setAttribute('data-theme', t);
  localStorage.setItem('theme', t);
  if (themeIcon) themeIcon.textContent = t === 'dark' ? '☀' : '☾';
}
applyTheme(localStorage.getItem('theme') || (matchMedia('(prefers-color-scheme:light)').matches ? 'light' : 'dark'));
themeBtn?.addEventListener('click', () => applyTheme(html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark'));

/* ── HEADER SCROLL ───────────────────────────────────────────────────────────── */
const header = document.getElementById('site-header');
window.addEventListener('scroll', () => {
  header?.classList.toggle('scrolled', window.scrollY > 40);
  document.getElementById('backToTop')?.classList.toggle('visible', window.scrollY > 300);
}, { passive: true });

/* ── MOBILE NAV ──────────────────────────────────────────────────────────────── */
const hamburger = document.getElementById('hamburger');
const navLinks  = document.getElementById('nav-links');
hamburger?.addEventListener('click', () => {
  const open = navLinks.classList.toggle('open');
  hamburger.setAttribute('aria-expanded', open);
  document.body.style.overflow = open ? 'hidden' : '';
});
navLinks?.querySelectorAll('.nav-link').forEach(l =>
  l.addEventListener('click', () => { navLinks.classList.remove('open'); document.body.style.overflow = ''; })
);

/* ── BACK TO TOP ─────────────────────────────────────────────────────────────── */
document.getElementById('backToTop')?.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));

/* ── CONTACT LINK HELPERS ───────────────────────────────────────────────────── */
function isValidEmailAddress(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(email || '').trim());
}

function normalizePhoneDigits(phone) {
  return String(phone || '').replace(/\D/g, '');
}

function buildWhatsappUrl(phone, message) {
  const digits = normalizePhoneDigits(phone);
  if (!/^\d{10,15}$/.test(digits)) return null;
  const text = String(message || '').trim();
  return text ? `https://wa.me/${digits}?text=${encodeURIComponent(text)}` : `https://wa.me/${digits}`;
}

function disableInvalidContactLink(link, reason) {
  link.setAttribute('aria-disabled', 'true');
  link.setAttribute('tabindex', '-1');
  link.classList.add('contact-link-disabled');
  link.title = reason;
  link.addEventListener('click', event => event.preventDefault());
}

function initContactLinks() {
  document.querySelectorAll('[data-contact-email]').forEach(link => {
    const email = link.dataset.contactEmail;
    if (isValidEmailAddress(email)) {
      link.href = `mailto:${email.trim()}`;
    } else {
      disableInvalidContactLink(link, 'Email address is unavailable');
      console.warn('Invalid contact email:', email);
    }
  });

  document.querySelectorAll('[data-contact-whatsapp]').forEach(link => {
    const phone = link.dataset.contactWhatsapp;
    const message = link.dataset.contactMessage || '';
    const url = buildWhatsappUrl(phone, message);
    if (url) {
      link.href = url;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
    } else {
      disableInvalidContactLink(link, 'WhatsApp chat is unavailable');
      console.warn('Invalid WhatsApp number:', phone);
    }
  });
}

initContactLinks();

/* ── FADE-IN ON SCROLL ───────────────────────────────────────────────────────── */
const io = new IntersectionObserver((entries) => {
  entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); io.unobserve(e.target); } });
}, { threshold: 0.12 });
document.querySelectorAll('.fade-in').forEach(el => io.observe(el));

/* ── COUNT-UP ANIMATION ──────────────────────────────────────────────────────── */
function animateCount(el) {
  const raw   = el.dataset.target || el.textContent;
  const num   = parseFloat(raw.replace(/[^0-9.]/g, ''));
  const suffix = raw.replace(/[0-9.]/g, '');
  const dur   = 1800, steps = 60;
  let cur = 0, step = 0;
  const timer = setInterval(() => {
    step++;
    cur = Math.min(num, Math.round((num * step) / steps));
    el.textContent = cur + suffix;
    if (step >= steps) clearInterval(timer);
  }, dur / steps);
}
const statObs = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.querySelectorAll('.stat-value, .val').forEach(animateCount);
      statObs.unobserve(e.target);
    }
  });
}, { threshold: 0.4 });
document.querySelectorAll('.hero-stats, .stats-grid').forEach(el => statObs.observe(el));

/* ── PARTICLE CANVAS (HERO) ──────────────────────────────────────────────────── */
(function initCanvas() {
  const canvas = document.getElementById('heroCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let W, H, particles = [];

  function resize() { W = canvas.width = canvas.offsetWidth; H = canvas.height = canvas.offsetHeight; }
  resize();
  window.addEventListener('resize', resize);

  const isDark = () => html.getAttribute('data-theme') !== 'light';

  function makeParticle() {
    return {
      x: Math.random() * W, y: Math.random() * H,
      r: Math.random() * 1.8 + 0.4,
      vx: (Math.random() - 0.5) * 0.35, vy: (Math.random() - 0.5) * 0.35,
      a: Math.random() * 0.6 + 0.1,
      hue: Math.random() < 0.6 ? 258 : 195,
    };
  }
  for (let i = 0; i < 90; i++) particles.push(makeParticle());

  let mx = W / 2, my = H / 2;
  canvas.addEventListener('mousemove', e => { mx = e.offsetX; my = e.offsetY; });

  function draw() {
    ctx.clearRect(0, 0, W, H);
    const alpha = isDark() ? 1 : 0.5;
    particles.forEach(p => {
      const dx = mx - p.x, dy = my - p.y, dist = Math.sqrt(dx*dx + dy*dy);
      if (dist < 120) { p.vx += dx * 0.00012; p.vy += dy * 0.00012; }
      p.x += p.vx; p.y += p.vy;
      p.vx *= 0.995; p.vy *= 0.995;
      if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;
      if (p.y < 0) p.y = H; if (p.y > H) p.y = 0;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `hsla(${p.hue},90%,70%,${p.a * alpha})`;
      ctx.fill();
    });
    // draw lines between close particles
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const a = particles[i], b = particles[j];
        const d = Math.hypot(a.x - b.x, a.y - b.y);
        if (d < 100) {
          ctx.beginPath();
          ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y);
          ctx.strokeStyle = `hsla(258,80%,70%,${(1 - d / 100) * 0.18 * alpha})`;
          ctx.lineWidth = 0.6;
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(draw);
  }
  draw();
})();

/* ── TESTIMONIALS SLIDER ─────────────────────────────────────────────────────── */
(function initSlider() {
  const track  = document.querySelector('.testimonials-track');
  const dots   = document.querySelectorAll('.slider-dot');
  const prevBtn = document.querySelector('.slider-arrow.prev');
  const nextBtn = document.querySelector('.slider-arrow.next');
  if (!track) return;
  const slides = track.querySelectorAll('.testimonial-slide');
  let cur = 0, timer;

  function go(n) {
    cur = (n + slides.length) % slides.length;
    track.style.transform = `translateX(-${cur * 100}%)`;
    dots.forEach((d, i) => d.classList.toggle('active', i === cur));
  }
  function autoPlay() { timer = setInterval(() => go(cur + 1), 5000); }
  function pause() { clearInterval(timer); }

  dots.forEach((d, i) => d.addEventListener('click', () => { go(i); pause(); autoPlay(); }));
  prevBtn?.addEventListener('click', () => { go(cur - 1); pause(); autoPlay(); });
  nextBtn?.addEventListener('click', () => { go(cur + 1); pause(); autoPlay(); });
  track?.addEventListener('mouseenter', pause);
  track?.addEventListener('mouseleave', autoPlay);

  // touch/swipe
  let tx = 0;
  track?.addEventListener('touchstart', e => { tx = e.touches[0].clientX; }, { passive: true });
  track?.addEventListener('touchend', e => {
    const diff = tx - e.changedTouches[0].clientX;
    if (Math.abs(diff) > 40) { go(diff > 0 ? cur + 1 : cur - 1); pause(); autoPlay(); }
  });
  go(0); autoPlay();
})();

/* ── TECH TABS ───────────────────────────────────────────────────────────────── */
document.querySelectorAll('.tech-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    const target = tab.dataset.target;
    document.querySelectorAll('.tech-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tech-panel').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    document.querySelector(`.tech-panel[data-panel="${target}"]`)?.classList.add('active');
  });
});

/* ── PORTFOLIO FILTER ────────────────────────────────────────────────────────── */
document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const cat = btn.dataset.filter;
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.portfolio-card').forEach(card => {
      const show = cat === 'all' || card.dataset.category === cat;
      card.style.display = show ? '' : 'none';
      if (show) { card.style.animation = 'none'; void card.offsetWidth; card.style.animation = ''; }
    });
  });
});

/* ── BLOG FILTER ─────────────────────────────────────────────────────────────── */
document.querySelectorAll('.blog-filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const cat = btn.dataset.filter;
    document.querySelectorAll('.blog-filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.blog-card').forEach(card => {
      card.style.display = (cat === 'all' || card.dataset.category === cat) ? '' : 'none';
    });
  });
});

/* ── FAQ ACCORDION ───────────────────────────────────────────────────────────── */
document.querySelectorAll('.faq-q').forEach(q => {
  q.addEventListener('click', () => {
    const item = q.closest('.faq-item');
    const wasOpen = item.classList.contains('open');
    document.querySelectorAll('.faq-item').forEach(i => i.classList.remove('open'));
    if (!wasOpen) item.classList.add('open');
  });
  q.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); q.click(); } });
});

/* ── CAREERS FILTER ──────────────────────────────────────────────────────────── */
document.querySelectorAll('.dept-filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const dept = btn.dataset.dept;
    document.querySelectorAll('.dept-filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.job-card').forEach(card => {
      card.style.display = (dept === 'all' || card.dataset.dept === dept) ? '' : 'none';
    });
  });
});

/* ── CONTACT FORM ────────────────────────────────────────────────────────────── */
const contactForm = document.getElementById('contactForm');
const formMsg     = document.getElementById('formMsg');
contactForm?.addEventListener('submit', async e => {
  e.preventDefault();
  const btn = contactForm.querySelector('[type=submit]');
  btn.disabled = true; btn.textContent = 'Sending…';
  try {
    const res = await fetch('/contact', { method: 'POST', body: new FormData(contactForm) });
    if (res.status === 401) {
      // Not authenticated — redirect to login page
      window.location.href = '/login';
      return;
    }
    const data = await res.json();
    formMsg.className = 'form-msg ' + (data.ok ? 'success' : 'error');
    formMsg.textContent = data.ok ? data.message : data.error;
    if (data.ok) contactForm.reset();
  } catch {
    formMsg.className = 'form-msg error';
    formMsg.textContent = 'Something went wrong. Please try again.';
  }
  btn.disabled = false; btn.textContent = 'Send Message';
});

/* ── NEWSLETTER ──────────────────────────────────────────────────────────────── */
document.getElementById('newsletterForm')?.addEventListener('submit', async e => {
  e.preventDefault();
  const email = document.getElementById('newsletterEmail').value;
  const msg   = document.getElementById('newsletterMsg');
  try {
    const res  = await fetch('/newsletter', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ email }) });
    const data = await res.json();
    msg.textContent = data.message || data.error;
    msg.style.color = data.ok ? 'var(--success)' : 'var(--danger)';
    if (data.ok) document.getElementById('newsletterEmail').value = '';
  } catch { msg.textContent = 'Error. Please try again.'; }
});

/* ── FLOATING SPEED-DIAL TOGGLE ─────────────────────────────────────────────── */
(function initSpeedDial() {
  const bar = document.getElementById('floatingContactBar');
  const mainBtn = document.getElementById('floatMainBtn');
  mainBtn?.addEventListener('click', () => {
    bar?.classList.toggle('open');
  });
})();

/* ── SMART ASSISTANT CHATBOT ─────────────────────────────────────────────────── */
(function initChat() {
  const toggle   = document.getElementById('chatToggle');
  const panel    = document.getElementById('chatPanel');
  const form     = document.getElementById('chatForm');
  const input    = document.getElementById('chatInput');
  const msgs     = document.getElementById('chatMessages');
  const clearBtn = document.getElementById('clearChatBtn');
  const iconO    = toggle?.querySelector('.chat-icon-open');
  const iconC    = toggle?.querySelector('.chat-icon-close');
  if (!toggle) return;

  const CHAT_HISTORY_KEY = 'novatech_chat_history_v2';
  let history = [];

  try {
    const saved = localStorage.getItem(CHAT_HISTORY_KEY);
    if (saved) history = JSON.parse(saved);
  } catch(e) {}

  let open = false;
  toggle.addEventListener('click', () => {
    open = !open;
    panel.classList.toggle('open', open);
    iconO.style.display = open ? 'none' : '';
    iconC.style.display = open ? '' : 'none';
    if (open) input.focus();
  });

  function renderHistory() {
    if (!history.length) return;
    msgs.innerHTML = '';
    history.forEach(item => {
      appendMsgElement(item.text, item.who, item.actions, false);
    });
    msgs.scrollTop = msgs.scrollHeight;
  }

  function formatText(text) {
    if (!text) return '';
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
               .replace(/\n/g, '<br/>');
  }

  function appendMsgElement(text, who, actions = null, save = true) {
    const div = document.createElement('div');
    div.className = `chat-msg ${who}`;

    let html = `<div class="msg-bubble">${formatText(text)}`;
    if (actions && actions.length) {
      html += `<div style="margin-top:.65rem;display:flex;flex-direction:column;gap:.35rem;">`;
      actions.forEach(act => {
        if (act.url) {
          html += `<a href="${act.url}" target="_blank" class="btn btn-secondary btn-sm" style="font-size:.78rem;padding:.35rem .75rem;justify-content:center;">${act.label}</a>`;
        } else if (act.action === 'open_contact') {
          html += `<a href="/contact" class="btn btn-primary btn-sm" style="font-size:.78rem;padding:.35rem .75rem;justify-content:center;">${act.label}</a>`;
        } else if (act.action === 'open_meeting') {
          html += `<a href="/contact" class="btn btn-secondary btn-sm" style="font-size:.78rem;padding:.35rem .75rem;justify-content:center;">${act.label}</a>`;
        }
      });
      html += `</div>`;
    }
    html += `</div>`;

    div.innerHTML = html;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;

    if (save) {
      history.push({ text, who, actions });
      try { localStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(history)); } catch(e){}
    }
    return div;
  }

  function showTyping() {
    const div = document.createElement('div');
    div.className = 'chat-msg bot chat-typing';
    div.innerHTML = '<div class="msg-bubble"><span class="typing-dots"><span></span><span></span><span></span></span></div>';
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
    return div;
  }

  async function sendMessage(text) {
    if (!text) return;
    appendMsgElement(text, 'user', null, true);
    input.value = '';
    const typing = showTyping();

    // Natural bot delay
    await new Promise(r => setTimeout(r, 500));

    try {
      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });
      const data = await res.json();
      typing.remove();
      appendMsgElement(data.reply, 'bot', data.actions || null, true);
    } catch {
      typing.remove();
      appendMsgElement('Sorry, I\'m having trouble connecting to my database. Please reach out to teckhubofficals@gmail.com', 'bot', null, true);
    }
  }

  form?.addEventListener('submit', e => {
    e.preventDefault();
    sendMessage(input.value.trim());
  });

  // Suggestion Chips Click
  document.querySelectorAll('.chat-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      sendMessage(chip.dataset.query);
    });
  });

  // Clear Chat History
  clearBtn?.addEventListener('click', () => {
    history = [];
    localStorage.removeItem(CHAT_HISTORY_KEY);
    msgs.innerHTML = '<div class="chat-msg bot"><div class="msg-bubble">Chat history cleared! How can I help you today? 👋</div></div>';
  });

  // Load initial history if available
  if (history.length > 0) {
    renderHistory();
  }
})();


/* ── MARQUEE DUPLICATE ───────────────────────────────────────────────────────── */
document.querySelectorAll('.marquee-track').forEach(track => {
  track.innerHTML += track.innerHTML;
});

/* ── SMOOTH ANCHOR LINKS ─────────────────────────────────────────────────────── */
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const target = document.querySelector(a.getAttribute('href'));
    if (target) { e.preventDefault(); target.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
  });
});
