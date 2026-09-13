import os
import json
import requests
from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import jwt
import datetime

# Загрузка переменных окружения
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Секретный ключ для сессий

# --- НАСТРОЙКИ GOOGLE ТАБЛИЦЫ ---
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'google_credentials.json')

# Инициализация клиента Google Sheets
try:
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
    GOOGLE_ENABLED = True
except Exception as e:
    print(f"Ошибка подключения к Google Таблице: {e}")
    GOOGLE_ENABLED = False

# --- НАСТРОЙКИ YANDEX GPT ---
YANDEX_CLOUD_ID = os.getenv('YANDEX_CLOUD_ID')
YANDEX_FOLDER_ID = os.getenv('YANDEX_FOLDER_ID')
IAM_TOKEN = None
IAM_TOKEN_EXPIRY = 0

def get_yandex_iam_token():
    """Получает IAM токен для доступа к API Яндекс Облака"""
    global IAM_TOKEN, IAM_TOKEN_EXPIRY
    
    # Проверяем, не истек ли текущий токен
    if IAM_TOKEN and datetime.datetime.now().timestamp() < IAM_TOKEN_EXPIRY:
        return IAM_TOKEN

    key_path = 'authorized_key.json'
    if not os.path.exists(key_path):
        raise FileNotFoundError("Файл authorized_key.json не найден!")

    with open(key_path, 'r') as f:
        key_data = json.load(f)
    
    key_id = key_data['key_id']
    service_account_id = key_data['subject']['id']
    
    # Создаем JWT
    header = {'alg': 'PS256', 'typ': 'JWT', 'kid': key_id}
    payload = {
        'iss': service_account_id,
        'aud': 'https://iam.api.cloud.yandex.net/iam/v1/tokens',
        'iat': int(datetime.datetime.now().timestamp()),
        'exp': int((datetime.datetime.now() + datetime.timedelta(minutes=5)).timestamp())
    }
    
    encoded_header = jwt.utils.base64url_encode(json.dumps(header).encode()).decode()
    encoded_payload = jwt.utils.base64url_encode(json.dumps(payload).encode()).decode()
    
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.asymmetric import padding
    
    private_key_str = key_data['private_key']
    private_key = serialization.load_pem_private_key(
        private_key_str.encode(),
        password=None,
        backend=default_backend()
    )
    
    message = f"{encoded_header}.{encoded_payload}".encode()
    signature = private_key.sign(message, padding.PKCS1v15(), hashes.SHA256())
    encoded_signature = jwt.utils.base64url_encode(signature).decode()
    
    jwt_token = f"{encoded_header}.{encoded_payload}.{encoded_signature}"
    
    # Обмен JWT на IAM токен
    url = 'https://iam.api.cloud.yandex.net/iam/v1/tokens'
    headers = {'Content-Type': 'application/json'}
    data = {'jwt': jwt_token}
    
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    
    if 'iamToken' in result:
        IAM_TOKEN = result['iamToken']
        # Токен живет 1 час, обновим за 5 минут до истечения
        IAM_TOKEN_EXPIRY = datetime.datetime.now().timestamp() + 3500 
        return IAM_TOKEN
    else:
        raise Exception(f"Не удалось получить IAM токен: {result}")

def call_yandex_gpt(prompt):
    """Отправляет запрос к YandexGPT"""
    try:
        iam_token = get_yandex_iam_token()
        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {iam_token}',
            'x-folder-id': YANDEX_FOLDER_ID
        }
        
        data = {
            "modelUri": f"gpt://{YANDEX_CLOUD_ID}/yandexgpt/latest",
            "completionOptions": {
                "stream": False,
                "temperature": 0.7,
                "maxTokens": 1000
            },
            "messages": [
                {"role": "system", "content": "Ты — мудрый Оракул в мире Dungeons & Dragons. Твоя задача — помогать ученикам 8-11 классов выбирать профессию, используя метафоры фэнтези-мира. Отвечай кратко, вдохновляюще и в стиле старинного свитка."},
                {"role": "user", "content": prompt}
            ]
        }
        
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        
        if 'result' in result and 'alternatives' in result['result']:
            return result['result']['alternatives'][0]['message']['text']
        else:
            return f"Ошибка генерации: {result}"
            
    except Exception as e:
        return f"Ошибка подключения к ИИ: {str(e)}"

# --- ЛОГИКА ТЕСТА КЛИМОВА (АДАПТИРОВАННЫЙ ПОД D&D) ---
# Вопросы переформулированы под фэнтези сеттинг
QUESTIONS = [
    {
        "text": "Что тебе интереснее делать в подземелье?",
        "options": [
            {"text": "Лечить раненых соратников и готовить зелья", "type": "Ч-З"},
            {"text": "Собирать древние артефакты и изучать их свойства", "type": "Ч-Т"},
            {"text": "Рисовать карты неизведанных земель", "type": "Ч-Х"},
            {"text": "Убеждать стражу пропустить нас или торговаться с купцами", "type": "Ч-Ч"},
            {"text": "Обустроить лагерь и развести костер", "type": "Ч-П"}
        ]
    },
    {
        "text": "Какая магия тебе ближе?",
        "options": [
            {"text": "Магия природы: управление растениями и животными", "type": "Ч-П"},
            {"text": "Магия исцеления: помощь людям и снятие проклятий", "type": "Ч-З"},
            {"text": "Магия знаний: чтение древних свитков и разгадка загадок", "type": "Ч-Т"},
            {"text": "Магия иллюзий: создание образов и влияние на умы", "type": "Ч-Х"},
            {"text": "Магия общения: призыв духов-помощников или переговоры с драконами", "type": "Ч-Ч"}
        ]
    },
    {
        "text": "Какую роль в отряде ты бы выбрал?",
        "options": [
            {"text": "Хранитель знаний (архивариус гильдии)", "type": "Ч-Т"},
            {"text": "Дипломат (посол эльфов)", "type": "Ч-Ч"},
            {"text": "Зельевар (алхимик)", "type": "Ч-З"},
            {"text": "Строитель укреплений (инженер гномов)", "type": "Ч-П"},
            {"text": "Летописец подвигов (бард)", "type": "Ч-Х"}
        ]
    },
    {
        "text": "Что ты выберешь в награду?",
        "options": [
            {"text": "Чертежи механизма вечного двигателя", "type": "Ч-Т"},
            {"text": "Сад с волшебными цветами", "type": "Ч-П"},
            {"text": "Право вершить суд над пленными", "type": "Ч-Ч"},
            {"text": "Набор редких красок и холстов", "type": "Ч-Х"},
            {"text": "Аптечку с эликсирами жизни", "type": "Ч-З"}
        ]
    },
    {
        "text": "Твое любимое занятие в таверне?",
        "options": [
            {"text": "Слушать истории путешественников", "type": "Ч-Ч"},
            {"text": "Разбирать свой доспех и чинить его", "type": "Ч-П"},
            {"text": "Изучать меню и состав блюд", "type": "Ч-З"},
            {"text": "Наблюдать за игрой теней от камина", "type": "Ч-Х"},
            {"text": "Разгадывать шифры на салфетках", "type": "Ч-Т"}
        ]
    }
]

TYPES_MAP = {
    "Ч-П": {"name": "Хранитель Природы", "class": "Друид/Егерь", "desc": "Ты чувствуешь единство с живым миром."},
    "Ч-Т": {"name": "Мастер Механизмов", "class": "Изобретатель/Инженер", "desc": "Твой ум создан для техники и логики."},
    "Ч-Х": {"name": "Творец Легенд", "class": "Бард/Художник", "desc": "Ты видишь мир в красках и образах."},
    "Ч-Ч": {"name": "Повелитель Судеб", "class": "Паладин/Психолог", "desc": "Твое призвание — люди и руководство."},
    "Ч-З": {"name": "Вершитель Здоровья", "class": "Жрец/Врач", "desc": "Твоя сила — в заботе и лечении."}
}

PROFESSIONS = {
    "Ч-П": ["Эколог", "Геолог", "Агроном", "Ветеринар", "Лесничий"],
    "Ч-Т": ["Программист", "Инженер", "Архитектор", "Механик", "Технолог"],
    "Ч-Х": ["Дизайнер", "Режиссер", "Писатель", "Художник", "Актер"],
    "Ч-Ч": ["Психолог", "Учитель", "Менеджер", "Юрист", "Врач (терапевт)"],
    "Ч-З": ["Врач", "Фармацевт", "Биолог", "Химик-технолог", "Диетолог"]
}

EXAMS_MAP = {
    "Ч-П": "Биология, География, Математика",
    "Ч-Т": "Математика (проф), Информатика, Физика",
    "Ч-Х": "Литература, Обществознание, Творческий экзамен",
    "Ч-Ч": "Обществознание, Биология, История",
    "Ч-З": "Биология, Химия, Математика"
}

def calculate_type(scores):
    max_score = -1
    best_type = "Ч-Ч"
    for t, s in scores.items():
        if s > max_score:
            max_score = s
            best_type = t
    return best_type

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    code = request.form.get('code').strip().upper()
    hero_name = request.form.get('hero_name').strip()
    
    if not code or not hero_name:
        return redirect(url_for('index'))
    
    session['user_code'] = code
    session['hero_name'] = hero_name
    
    # Проверка кода в таблице (опционально можно добавить проверку существования)
    # Если нужно строго проверять наличие кода в таблице перед стартом:
    # row = sheet.find(code)
    # if not row: ... error ...
    
    return redirect(url_for('oracle_room'))

@app.route('/oracle')
def oracle_room():
    if 'user_code' not in session:
        return redirect(url_for('index'))
    return render_template('oracle_room.html', questions=QUESTIONS)

@app.route('/submit_test', methods=['POST'])
def submit_test():
    if 'user_code' not in session:
        return redirect(url_for('index'))
    
    scores = {"Ч-П": 0, "Ч-Т": 0, "Ч-Х": 0, "Ч-Ч": 0, "Ч-З": 0}
    choices = []
    
    for i in range(len(QUESTIONS)):
        answer = request.form.get(f'q{i}')
        if answer:
            scores[answer] += 1
            choices.append(answer)
    
    personality_type = calculate_type(scores)
    session['personality_type'] = personality_type
    session['scores'] = scores
    session['choices'] = choices
    
    # Сохранение в Google Таблицу
    if GOOGLE_ENABLED:
        try:
            # Проверяем, есть ли уже такой код
            found_cell = sheet.find(session['user_code'])
            if found_cell:
                row_idx = found_cell.row
                # Обновляем строку: Код, Имя, Класс (извлекаем из кода), Дата, Тип, Баллы..., Выборы
                class_name = session['user_code'][:-2] # Например 9А из 9А14
                date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                
                row_data = [
                    session['user_code'],
                    session['hero_name'],
                    class_name,
                    date_str,
                    TYPES_MAP[personality_type]['name'],
                    scores['Ч-П'],
                    scores['Ч-Т'],
                    scores['Ч-Х'],
                    scores['Ч-Ч'],
                    scores['Ч-З'],
                    json.dumps(choices)
                ]
                sheet.update(f'A{row_idx}:K{row_idx}', [row_data])
            else:
                # Если кода нет, добавляем новую строку (если учитель не вводил заранее)
                class_name = session['user_code'][:-2]
                date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                row_data = [
                    session['user_code'],
                    session['hero_name'],
                    class_name,
                    date_str,
                    TYPES_MAP[personality_type]['name'],
                    scores['Ч-П'],
                    scores['Ч-Т'],
                    scores['Ч-Х'],
                    scores['Ч-Ч'],
                    scores['Ч-З'],
                    json.dumps(choices)
                ]
                sheet.append_row(row_data)
        except Exception as e:
            print(f"Ошибка записи в таблицу: {e}")
            # Не прерываем игру пользователя, если таблица недоступна
    
    return redirect(url_for('quest_room'))

@app.route('/quest')
def quest_room():
    if 'personality_type' not in session:
        return redirect(url_for('index'))
    
    p_type = session['personality_type']
    hero = session['hero_name']
    
    # Генерируем промпт для ИИ
    prompt = f"""
    Герой '{hero}' (тип личности: {TYPES_MAP[p_type]['desc']}) стоит перед выбором пути.
    Придумай короткую фэнтези-ситуацию (квест) из 5 шагов, соответствующую этому типу.
    Ситуация должна быть связана с будущей профессией: {', '.join(PROFESSIONS[p_type][:2])}.
    В конце герой должен сделать выбор.
    Ответ дай в формате JSON: {{ "story": "текст ситуации", "steps": ["шаг1", "шаг2"...], "choice_question": "вопрос выбора" }}
    """
    
    # Если ИИ недоступен, используем заглушку
    try:
        ai_response = call_yandex_gpt(prompt)
        # Пытаемся распарсить JSON из ответа (ИИ может добавить лишний текст)
        import re
        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if json_match:
            quest_data = json.loads(json_match.group())
        else:
            raise ValueError("Нет JSON в ответе")
    except:
        quest_data = {
            "story": f"Герой {hero}, ты чувствуешь зов своей судьбы. Перед тобой древний портал.",
            "steps": [
                "Ты видишь заросший тропинкой лес.",
                "На камне высечены странные символы.",
                "Ветер шепчет тебе подсказки.",
                "Твоя интуиция подсказывает верный путь.",
                "Ты стоишь перед дверью в будущее."
            ],
            "choice_question": "Готов ли ты войти?"
        }
    
    return render_template('quest_room.html', 
                           quest=quest_data, 
                           type_info=TYPES_MAP[p_type],
                           professions=PROFESSIONS[p_type])

@app.route('/finish_quest', methods=['POST'])
def finish_quest():
    if 'personality_type' not in session:
        return redirect(url_for('index'))
    
    p_type = session['personality_type']
    hero = session['hero_name']
    
    # Генерация Свитка Судьбы через ИИ
    prompt = f"""
    Составь 'Свиток Судьбы' для героя {hero}.
    Тип личности: {TYPES_MAP[p_type]['name']} ({TYPES_MAP[p_type]['class']}).
    Подходящие профессии: {', '.join(PROFESSIONS[p_type])}.
    Необходимые ЕГЭ/ОГЭ: {EXAMS_MAP[p_type]}.
    
    Напиши краткое, эпичное поздравление в стиле D&D.
    Перечисли 3-5 лучших ВУЗов России для этих профессий.
    Ответ верни строго в формате HTML фрагмента (без тегов html/body), используй теги <h3>, <p>, <ul>, <li>.
    """
    
    try:
        scroll_content = call_yandex_gpt(prompt)
        # Очистка от возможных маркеров кода
        scroll_content = scroll_content.replace('```html', '').replace('```', '')
    except:
        scroll_content = f"""
        <h3>Свиток Судьбы Героя {hero}</h3>
        <p>Твой путь предопределен звездами!</p>
        <p><strong>Класс:</strong> {TYPES_MAP[p_type]['class']}</p>
        <p><strong>Предназначение:</strong> {', '.join(PROFESSIONS[p_type])}</p>
        <p><strong>Испытания (ЕГЭ/ОГЭ):</strong> {EXAMS_MAP[p_type]}</p>
        <p><strong>Храмы Знаний (ВУЗы):</strong></p>
        <ul>
            <li>МГУ им. Ломоносова</li>
            <li>МГТУ им. Баумана</li>
            <li>СПбГУ</li>
            <li>НИУ ВШЭ</li>
            <li>МИФИ</li>
        </ul>
        <p>Да пребудет с тобой сила знаний!</p>
        """
    
    return render_template('scroll.html', 
                           hero=hero, 
                           type_info=TYPES_MAP[p_type],
                           professions=PROFESSIONS[p_type],
                           exams=EXAMS_MAP[p_type],
                           scroll_html=scroll_content)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
