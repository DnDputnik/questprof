// frontend/js/effects.js - Улучшенная система частиц

// ===== ПРОДВИНУТАЯ СИСТЕМА ЧАСТИЦ НА CANVAS =====
class AdvancedParticleSystem {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;
        
        this.canvas = document.createElement('canvas');
        this.canvas.style.cssText = 'position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 1;';
        this.container.appendChild(this.canvas);
        
        this.ctx = this.canvas.getContext('2d');
        this.particles = [];
        this.mouse = { x: null, y: null, radius: 150 };
        
        this.options = {
            count: options.count || 50,
            type: options.type || 'default',
            color: options.color || 'rgba(212, 175, 55, 0.6)',
            speed: options.speed || 1,
            size: options.size || 3,
            ...options
        };
        
        this.resize();
        this.init();
        this.animate();
        
        // Отслеживание мыши
        window.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            this.mouse.x = e.clientX - rect.left;
            this.mouse.y = e.clientY - rect.top;
        });
        
        window.addEventListener('mouseleave', () => {
            this.mouse.x = null;
            this.mouse.y = null;
        });
        
        window.addEventListener('resize', () => this.resize());
    }
    
    resize() {
        this.canvas.width = this.container.offsetWidth;
        this.canvas.height = this.container.offsetHeight;
    }
    
    init() {
        for (let i = 0; i < this.options.count; i++) {
            this.particles.push(this.createParticle());
        }
    }
    
    createParticle() {
        const type = this.options.type;
        const particle = {
            x: Math.random() * this.canvas.width,
            y: Math.random() * this.canvas.height,
            size: Math.random() * this.options.size + 1,
            speedX: (Math.random() - 0.5) * this.options.speed,
            speedY: (Math.random() - 0.5) * this.options.speed,
            opacity: Math.random() * 0.5 + 0.3,
            rotation: Math.random() * 360,
            rotationSpeed: (Math.random() - 0.5) * 2
        };
        
        // Специфичные свойства для разных типов
        if (type === 'ember') {
            particle.speedY = -Math.random() * 2 - 0.5;
            particle.speedX = (Math.random() - 0.5) * 0.5;
            particle.life = 100;
            particle.decay = Math.random() * 0.5 + 0.2;
        } else if (type === 'magic') {
            particle.pulse = Math.random() * Math.PI * 2;
            particle.pulseSpeed = Math.random() * 0.05 + 0.02;
        } else if (type === 'leaf') {
            particle.speedY = Math.random() * 0.5 + 0.2;
            particle.speedX = Math.sin(Math.random() * Math.PI * 2) * 0.5;
            particle.wobble = Math.random() * Math.PI * 2;
            particle.wobbleSpeed = Math.random() * 0.02 + 0.01;
        } else if (type === 'sparkle') {
            particle.twinkle = Math.random() * Math.PI * 2;
            particle.twinkleSpeed = Math.random() * 0.1 + 0.05;
        }
        
        return particle;
    }
    
    drawParticle(p) {
        this.ctx.save();
        this.ctx.translate(p.x, p.y);
        this.ctx.rotate((p.rotation * Math.PI) / 180);
        this.ctx.globalAlpha = p.opacity;
        
        const type = this.options.type;
        const color = this.options.color;
        
        if (type === 'ember') {
            // Искры камина
            const gradient = this.ctx.createRadialGradient(0, 0, 0, 0, 0, p.size);
            gradient.addColorStop(0, color);
            gradient.addColorStop(1, 'transparent');
            this.ctx.fillStyle = gradient;
            this.ctx.beginPath();
            this.ctx.arc(0, 0, p.size, 0, Math.PI * 2);
            this.ctx.fill();
        } else if (type === 'magic') {
            // Магические символы
            this.ctx.fillStyle = color;
            this.ctx.shadowBlur = 10;
            this.ctx.shadowColor = color;
            this.ctx.beginPath();
            this.ctx.arc(0, 0, p.size, 0, Math.PI * 2);
            this.ctx.fill();
            
            // Внешнее свечение
            this.ctx.beginPath();
            this.ctx.arc(0, 0, p.size * 2, 0, Math.PI * 2);
            this.ctx.fillStyle = color.replace('0.6', '0.2');
            this.ctx.fill();
        } else if (type === 'leaf') {
            // Листья
            this.ctx.fillStyle = color;
            this.ctx.beginPath();
            this.ctx.ellipse(0, 0, p.size, p.size * 1.5, 0, 0, Math.PI * 2);
            this.ctx.fill();
        } else if (type === 'sparkle') {
            // Мерцающие звёзды
            this.ctx.fillStyle = color;
            this.ctx.shadowBlur = 15;
            this.ctx.shadowColor = color;
            
            // Рисуем звезду
            this.ctx.beginPath();
            for (let i = 0; i < 4; i++) {
                const angle = (i * Math.PI) / 2;
                const x = Math.cos(angle) * p.size;
                const y = Math.sin(angle) * p.size;
                if (i === 0) this.ctx.moveTo(x, y);
                else this.ctx.lineTo(x, y);
            }
            this.ctx.closePath();
            this.ctx.fill();
        } else {
            // Обычные частицы
            this.ctx.fillStyle = color;
            this.ctx.beginPath();
            this.ctx.arc(0, 0, p.size, 0, Math.PI * 2);
            this.ctx.fill();
        }
        
        this.ctx.restore();
    }
    
    updateParticle(p) {
        const type = this.options.type;
        
        // Базовое движение
        p.x += p.speedX;
        p.y += p.speedY;
        p.rotation += p.rotationSpeed;
        
        // Специфичная физика для типов
        if (type === 'ember') {
            p.life -= p.decay;
            p.opacity = (p.life / 100) * 0.8;
            p.speedX += (Math.random() - 0.5) * 0.1;
            
            if (p.life <= 0) {
                p.x = Math.random() * this.canvas.width;
                p.y = this.canvas.height + 10;
                p.life = 100;
                p.opacity = 0.8;
            }
        } else if (type === 'magic') {
            p.pulse += p.pulseSpeed;
            p.size = (Math.sin(p.pulse) + 2) * this.options.size;
            p.opacity = 0.3 + Math.sin(p.pulse) * 0.3;
        } else if (type === 'leaf') {
            p.wobble += p.wobbleSpeed;
            p.speedX = Math.sin(p.wobble) * 0.5;
            
            if (p.y > this.canvas.height) {
                p.y = -10;
                p.x = Math.random() * this.canvas.width;
            }
        } else if (type === 'sparkle') {
            p.twinkle += p.twinkleSpeed;
            p.opacity = 0.3 + Math.sin(p.twinkle) * 0.5;
            p.size = (Math.sin(p.twinkle) + 1.5) * this.options.size;
        }
        
        // Взаимодействие с мышью
        if (this.mouse.x !== null && this.mouse.y !== null) {
            const dx = this.mouse.x - p.x;
            const dy = this.mouse.y - p.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance < this.mouse.radius) {
                const force = (this.mouse.radius - distance) / this.mouse.radius;
                p.x -= (dx / distance) * force * 2;
                p.y -= (dy / distance) * force * 2;
            }
        }
        
        // Границы экрана
        if (p.x < 0) p.x = this.canvas.width;
        if (p.x > this.canvas.width) p.x = 0;
        if (p.y < 0) p.y = this.canvas.height;
        if (p.y > this.canvas.height) p.y = 0;
    }
    
    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        this.particles.forEach(p => {
            this.updateParticle(p);
            this.drawParticle(p);
        });
        
        requestAnimationFrame(() => this.animate());
    }
    
    destroy() {
        this.canvas.remove();
        this.particles = [];
    }
}

// ===== ДОПОЛНИТЕЛЬНЫЕ ЭФФЕКТЫ =====

// Эффект свечения при наведении на кнопки
function addGlowEffect() {
    document.querySelectorAll('.btn-primary, .option-btn').forEach(btn => {
        btn.addEventListener('mouseenter', function() {
            this.style.transition = 'all 0.3s ease';
            this.style.boxShadow = '0 0 30px rgba(212, 175, 55, 0.8), 0 0 60px rgba(212, 175, 55, 0.4)';
        });
        
        btn.addEventListener('mouseleave', function() {
            this.style.boxShadow = '';
        });
    });
}

// Анимация появления элементов при загрузке
function animatePageLoad() {
    const elements = document.querySelectorAll('header, .registration-form, .situation-card, .scroll-container');
    elements.forEach((el, index) => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        
        setTimeout(() => {
            el.style.transition = 'all 0.8s cubic-bezier(0.34, 1.56, 0.64, 1)';
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
        }, index * 200);
    });
}

// Эффект параллакса для фонов
function addParallaxEffect() {
    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        const parallaxElements = document.querySelectorAll('.bg-tavern, .bg-elf, .bg-oracle, .bg-council, .bg-scroll');
        
        parallaxElements.forEach(el => {
            const speed = 0.5;
            el.style.backgroundPositionY = `${scrolled * speed}px`;
        });
    });
}

// ===== ИНИЦИАЛИЗАЦИЯ =====
document.addEventListener('DOMContentLoaded', () => {
    addGlowEffect();
    animatePageLoad();
    
    // Добавляем класс для анимаций
    document.body.classList.add('page-loaded');
});

// Экспорт
window.AdvancedParticleSystem = AdvancedParticleSystem;