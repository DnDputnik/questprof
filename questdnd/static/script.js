// Простой скрипт для дополнительных интерактивных эффектов
document.addEventListener('DOMContentLoaded', function() {
    // Плавное появление карточек
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 200);
    });

    // Подсветка выбранных вариантов в тесте
    const radioButtons = document.querySelectorAll('input[type="radio"]');
    radioButtons.forEach(radio => {
        radio.addEventListener('change', function() {
            // Убираем подсветку со всех вариантов в этой группе
            const name = this.name;
            document.querySelectorAll(`input[name="${name}"]`).forEach(rb => {
                rb.closest('.option-card').style.borderColor = '#ddd';
                rb.closest('.option-card').style.background = 'white';
            });
            
            // Подсвечиваем выбранный
            this.closest('.option-card').style.borderColor = '#D2691E';
            this.closest('.option-card').style.background = '#FFF8F0';
        });
    });

    // Валидация кода доступа (автоматический перевод в верхний регистр)
    const codeInput = document.getElementById('code');
    if (codeInput) {
        codeInput.addEventListener('input', function() {
            this.value = this.value.toUpperCase();
        });
    }

    console.log('⚔️ Гильдия Исследователей готова к приключениям!');
});
