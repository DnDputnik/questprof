// frontend/js/quest.js

const QUESTIONS_COUNT = 6;
let currentSituation = 0;
let situations = [];
let questScores = { "Ч-П": 0, "Ч-Т": 0, "Ч-Х": 0, "Ч-Ч": 0, "Ч-З": 0 };
let choicesLog = [];
let isAnswering = false;

function shuffleArray(array) {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
}

document.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('http://127.0.0.1:8000/api/quest');
        const data = await response.json();
        const allSituations = data.quest;
        
        situations = shuffleArray(allSituations).slice(0, QUESTIONS_COUNT);
        
        situations = situations.map(s => {
            const options = Object.entries(s.options);
            const shuffled = shuffleArray(options);
            const newOptions = {};
            shuffled.forEach(([key, value], index) => {
                const letters = ['A', 'B', 'C', 'D', 'E', 'F'];
                newOptions[letters[index]] = value;
            });
            return { ...s, options: newOptions };
        });
        
        console.log(`✅ Загружено ситуаций для квеста: ${situations.length}`);
        renderSituation(0);
    } catch (error) {
        console.error('Ошибка загрузки квеста:', error);
        const container = document.getElementById('situationsContainer');
        if (container) {
            container.innerHTML = `<p style="color: red; text-align: center;">Ошибка загрузки. Убедись, что сервер запущен (uvicorn main:app --reload).</p>`;
        }
    }
});

function renderSituation(index) {
    const container = document.getElementById('situationsContainer');
    container.innerHTML = '';
    
    const situation = situations[index];
    const card = document.createElement('div');
    card.className = 'situation-card active animate-slide-up';
    
    const title = document.createElement('h2');
    title.className = 'situation-title';
    title.textContent = `Ситуация ${index + 1}: ${situation.title}`;
    
    const text = document.createElement('p');
    text.className = 'situation-text';
    text.textContent = situation.text;
    
    const optionsList = document.createElement('div');
    optionsList.className = 'options-list';
    
    // Создаём кнопки только для готовых вариантов (пропускаем "Свой ответ")
    for (const [key, option] of Object.entries(situation.options)) {
        // Пропускаем вариант "Свой ответ" (ключ F или текст содержит "Свой ответ")
        if (key !== 'F' && !option.text.includes('Свой ответ')) {
            const btn = document.createElement('button');
            btn.className = 'option-btn';
            btn.textContent = option.text;
            btn.style.marginBottom = '12px';
            btn.onclick = () => handleChoice(index, key, option.scores, situation.title);
            optionsList.appendChild(btn);
        }
    }
    
    // Блок для своего ответа (всегда виден отдельно)
    const customBlock = document.createElement('div');
    customBlock.className = 'custom-answer show';
    customBlock.style.marginTop = '20px';
    customBlock.style.paddingTop = '20px';
    customBlock.style.borderTop = '2px solid rgba(212, 175, 55, 0.3)';
    
    const customLabel = document.createElement('label');
    customLabel.style.color = '#d4af37';
    customLabel.style.fontWeight = 'bold';
    customLabel.style.marginBottom = '10px';
    customLabel.style.display = 'block';
    customLabel.textContent = '✍️ Или напиши свой ответ:';
    
    const textarea = document.createElement('textarea');
    textarea.placeholder = 'Опиши своё решение ситуации...';
    textarea.id = 'customAnswerText';
    textarea.style.marginTop = '10px';
    textarea.style.minHeight = '100px';
    
    const submitBtn = document.createElement('button');
    submitBtn.className = 'btn-primary';
    submitBtn.style.marginTop = '15px';
    submitBtn.textContent = 'Отправить свой ответ';
    submitBtn.onclick = () => handleCustomAnswer(index, situation.title);
    
    customBlock.appendChild(customLabel);
    customBlock.appendChild(textarea);
    customBlock.appendChild(submitBtn);
    optionsList.appendChild(customBlock);
    
    card.appendChild(title);
    card.appendChild(text);
    card.appendChild(optionsList);
    container.appendChild(card);
    
    const progress = ((index) / situations.length) * 100;
    const progressBar = document.getElementById('progressBar');
    if (progressBar) progressBar.style.width = `${progress}%`;
}

function handleChoice(situationIndex, choice, scores, title) {
    if (isAnswering) return;
    isAnswering = true;
    
    for (const [type, score] of Object.entries(scores)) {
        questScores[type] += score;
    }
    
    choicesLog.push(`Ситуация ${situationIndex + 1} (${title}): ${choice}`);
    
    const card = document.querySelector('.situation-card');
    if (card) {
        card.style.transition = 'all 0.5s ease';
        card.style.opacity = '0';
        card.style.transform = 'translateX(-50px)';
    }
    
    setTimeout(() => {
        currentSituation++;
        isAnswering = false;
        nextSituation();
    }, 600);
}

async function handleCustomAnswer(situationIndex, title) {
    if (isAnswering) return;
    
    const text = document.getElementById('customAnswerText').value.trim();
    if (!text) {
        alert('Пожалуйста, введите свой ответ');
        return;
    }
    
    if (text.length < 10) {
        alert('Ответ слишком короткий. Напишите хотя бы одно предложение.');
        return;
    }
    
    isAnswering = true;
    const loadingIndicator = document.getElementById('loadingIndicator');
    if (loadingIndicator) loadingIndicator.style.display = 'block';
    
    try {
        const response = await fetch('http://127.0.0.1:8000/api/analyze_answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ answer: text })
        });
        
        if (response.ok) {
            const aiScores = await response.json();
            for (const [type, score] of Object.entries(aiScores)) {
                questScores[type] += score;
            }
            choicesLog.push(`Ситуация ${situationIndex + 1} (${title}): Свой ответ (ИИ)`);
            
            const card = document.querySelector('.situation-card');
            if (card) {
                card.style.transition = 'all 0.5s ease';
                card.style.opacity = '0';
                card.style.transform = 'translateX(-50px)';
            }
            
            setTimeout(() => {
                currentSituation++;
                isAnswering = false;
                nextSituation();
            }, 600);
        } else {
            alert('Ошибка анализа ответа. Попробуй ещё раз.');
            isAnswering = false;
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Не удалось связаться с сервером.');
        isAnswering = false;
    } finally {
        const loadingIndicator = document.getElementById('loadingIndicator');
        if (loadingIndicator) loadingIndicator.style.display = 'none';
    }
}

function nextSituation() {
    if (currentSituation < situations.length) {
        renderSituation(currentSituation);
    } else {
        finishQuest();
    }
}

function finishQuest() {
    const oracleScores = JSON.parse(localStorage.getItem('oracleScores') || '{"Ч-П":0,"Ч-Т":0,"Ч-Х":0,"Ч-Ч":0,"Ч-З":0}');
    for (const type in oracleScores) {
        questScores[type] += oracleScores[type];
    }
    
    localStorage.setItem('finalQuestScores', JSON.stringify(questScores));
    localStorage.setItem('questChoices', choicesLog.join('; '));
    
    const dominantType = Object.entries(questScores).reduce((a, b) => b[1] > a[1] ? b : a)[0];
    localStorage.setItem('dominantType', dominantType);
    
    window.location.href = 'destiny.html';
}