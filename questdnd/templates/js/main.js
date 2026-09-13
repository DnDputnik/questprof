// frontend/js/main.js

document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const errorMessage = document.getElementById('errorMessage');
    
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const code = document.getElementById('code').value.trim().toUpperCase();
        const heroName = document.getElementById('heroName').value.trim();
        
        // Проверяем формат кода
        const codePattern = /^\d{1,2}[А-ЯA-Z]\d{2}$/;
        if (!codePattern.test(code)) {
            showError('Неверный формат кода. Пример: 8А02 или 11Б15');
            return;
        }
        
        if (!heroName) {
            showError('Введите имя героя');
            return;
        }
        
        try {
            // Отправляем данные на сервер
            const response = await fetch('http://127.0.0.1:8000/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    code: code,
                    heroName: heroName
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                // Сохраняем данные в localStorage
                localStorage.setItem('questCode', code);
                localStorage.setItem('questHeroName', heroName);
                localStorage.setItem('questClassName', data.class_name);
                
                // Переходим к следующей странице
                window.location.href = 'hero-name.html';
            } else {
                const errorData = await response.json();
                showError(errorData.detail || 'Ошибка входа');
            }
        } catch (error) {
            console.error('Ошибка:', error);
            showError('Не удалось подключиться к серверу. Убедитесь, что сервер запущен.');
        }
    });
    
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.add('show');
        setTimeout(() => {
            errorMessage.classList.remove('show');
        }, 5000);
    }
});