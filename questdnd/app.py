import os
import json
import requests
from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Загрузка переменных окружения
load_dotenv()

app = Flask(__name__)
app.secret_key = 'super_secret_key_dnd_quest'  # Нужен для сессий

# --- НАСТРОЙКИ GOOGLE ТАБЛИЦЫ ---
def get_google_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('google_credentials.json', scope)
    client = gspread.authorize(creds)
    sheet_id = os.getenv('GOOGLE_SHEET_ID')
    return client.open_by_key(sheet_id).sheet1

# --- НАСТРОЙКИ YANDEX GPT ---
YANDEX_CLOUD_ID = os.getenv('YANDEX_CLOUD_ID')
YANDEX_FOLDER_ID = os.getenv('YANDEX_FOLDER_ID')
IAM_TOKEN = None # Будет обновляться автоматически при запуске, если нужно, но лучше использовать ключ

def get_yandex_gpt_response(prompt):
    # Здесь должна быть логика получения IAM токена через сервисный аккаунт Яндекса
    # Для упрощения пока вернем заглушку, если токен не настроен, 
    # но в идеале тут запрос к https://iam.api.cloud.yandex.net/iam/v1/tokens
    # В рамках этого примера мы эмулируем ответ ИИ, чтобы сайт работал сразу.
    
    responses = {
        "Человек-Природа": "Ты чувствуешь зов лесов! Твой путь — ветеринар, эколог или геолог.",
        "Человек-Техника": "Механизмы подчиняются тебе! Инженер, программист или архитектор — твоя судьба.",
        "Человек-Художественный образ": "Творец миров! Дизайнер, режиссер или писатель ждут тебя.",
        "Человек-Человек": "Душа компании! Врач, учитель или психолог — твои инструменты.",
        "Человек-Знаковая система": "Повелитель кодов и цифр! Аналитик, экономист или лингвист."
    }
    return responses.get(prompt, "Твой путь уникален и полон открытий!")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/oracle', methods=['GET', 'POST'])
def oracle():
    if request.method == 'POST':
        code = request.form.get('code')
        hero_name = request.form.get('hero_name')
        
        # Сохраняем в сессию
        session['user_code'] = code
        session['hero_name'] = hero_name
        
        # Тут можно сразу записать в таблицу начало игры
        try:
            sheet = get_google_sheet()
            sheet.append_row([code, hero_name, '-', '-', '-', '-', '-', '-', '-', 'Начал игру'])
        except Exception as e:
            print(f"Ошибка Google Sheets: {e}")
            
        return render_template('oracle_room.html', hero_name=hero_name)
    
    return redirect(url_for('index'))

@app.route('/submit_test', methods=['POST'])
def submit_test():
    # Сбор ответов
    answers = []
    types_count = {'Ч-П': 0, 'Ч-Т': 0, 'Ч-Х': 0, 'Ч-Ч': 0, 'Ч-З': 0}
    
    # Логика подсчета баллов (упрощенная, нужно адаптировать под названия полей в форме)
    # Предположим, что в форме поля называются q1, q2... и значения соответствуют типу
    # В реальном проекте тут нужен точный маппинг вопросов Климова
    
    # Эмуляция результата для примера (замени на реальный подсчет)
    final_type = "Ч-Т" # Заглушка, будет пересчитано
    
    # Сохранение результатов
    code = session.get('user_code')
    hero_name = session.get('hero_name')
    
    try:
        sheet = get_google_sheet()
        # Формируем строку: Код, Имя, Тип, Баллы...
        row = [code, hero_name, final_type, 0, 0, 0, 0, 0, json.dumps(answers), 'Пройден тест']
        sheet.append_row(row)
    except Exception as e:
        print(f"Ошибка записи теста: {e}")

    # Генерация квеста (заглушка ИИ)
    quest_text = get_yandex_gpt_response(final_type)
    
    session['personality_type'] = final_type
    session['quest_text'] = quest_text
    
    return render_template('quest_room.html', quest_text=quest_text, hero_name=hero_name)

@app.route('/finish_quest', methods=['POST'])
def finish_quest():
    # Финализация и выдача свитка
    p_type = session.get('personality_type', 'Ч-Т')
    
    # Данные для свитка (можно расширить списком вузов)
    scroll_data = {
        'type': p_type,
        'professions': ['Инженер', 'Робототехник', 'Архитектор'],
        'exams': ['Математика (профиль)', 'Физика', 'Русский язык'],
        'universities': ['МГТУ им. Баумана', 'МИФИ', 'СПбПУ']
    }
    
    return render_template('scroll.html', data=scroll_data, hero_name=session.get('hero_name'))

if __name__ == '__main__':
    app.run(debug=True)