# backend/main.py
# Главный файл сервера квеста "Гильдия Путников"

# === ЖЕСТКОЕ ОТКЛЮЧЕНИЕ ПРОВЕРКИ SSL ДЛЯ WINDOWS ===
import os
import urllib3
import requests

# Отключаем предупреждения о небезопасных запросах
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Заставляем библиотеку requests игнорировать проверку сертификатов
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

# Перехватываем метод request, чтобы всегда передавать verify=False
_original_request = requests.Session.request
def _new_request(self, *args, **kwargs):
    kwargs['verify'] = False
    return _original_request(self, *args, **kwargs)
requests.Session.request = _new_request
# ====================================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from quest_data import QUEST_DATA
from ai_service import analyze_answer as ai_analyze
from dotenv import load_dotenv
import re

# Попытка импорта Google библиотек (если их нет, сервер всё равно запустится)
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

load_dotenv()

app = FastAPI(title="Гильдия Путников API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Настройка Google Sheets =====
sheet = None
if GOOGLE_AVAILABLE:
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    KEY_FILE = os.getenv("GOOGLE_KEY_FILE", "google_credentials.json")
    SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

    try:
        creds = Credentials.from_service_account_file(KEY_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).sheet1
        print("✅ Google Sheets успешно подключен!")
    except Exception as e:
        print(f"⚠️ Не удалось подключить Google Sheets: {e}")
        print("💡 Квест будет работать в режиме локального тестирования (результаты будут в консоли).")
else:
    print("⚠️ Библиотеки Google не установлены. Режим локального тестирования.")

# ===== Модели данных =====
class LoginRequest(BaseModel):
    code: str
    heroName: str = Field(..., alias="heroName")
    class Config:
        populate_by_name = True

class QuestResult(BaseModel):
    code: str
    hero_name: str
    class_name: str
    quest_type: str
    scores: dict
    choices: str

class AnalyzeRequest(BaseModel):
    answer: str

# ===== Вспомогательные функции =====
def is_valid_code(code: str) -> bool:
    pattern = r"^\d{1,2}[А-ЯA-Z]\d{2}$"
    return bool(re.match(pattern, code.upper()))

def extract_class(code: str) -> str:
    match = re.match(r"^(\d{1,2}[А-ЯA-Z])", code.upper())
    return match.group(1) if match else "—"

# ===== API Endpoints =====
@app.get("/")
def read_root():
    return {"message": "Сервер Гильдии Путников работает!"}

@app.get("/api/quest")
def get_quest():
    return {"quest": QUEST_DATA}

@app.post("/api/login")
def login(request: LoginRequest):
    code = request.code.upper().strip()
    hero_name = request.heroName.strip()

    if not is_valid_code(code):
        raise HTTPException(status_code=400, detail="Неверный формат кода. Пример: 8А02 или 11Б15")
    if not hero_name:
        raise HTTPException(status_code=400, detail="Введите имя героя")

    return {
        "success": True,
        "code": code,
        "class_name": extract_class(code),
        "hero_name": hero_name
    }

@app.post("/api/analyze_answer")
def analyze_answer_endpoint(request: AnalyzeRequest):
    answer = request.answer.strip()
    if not answer or len(answer) < 10:
        raise HTTPException(status_code=400, detail="Ответ слишком короткий. Напишите хотя бы одно предложение.")
    
    try:
        return ai_analyze(answer)
    except Exception as e:
        print(f"❌ Ошибка ИИ-анализа: {e}")
        return {"Ч-П": 1, "Ч-Т": 1, "Ч-Х": 1, "Ч-Ч": 1, "Ч-З": 1}

@app.post("/api/save_result")
def save_result(result: QuestResult):
    if sheet is None:
        # Если таблица не подключилась, просто выводим в консоль и отдаем успех
        print("\n" + "="*50)
        print("📜 НОВЫЙ РЕЗУЛЬТАТ КВЕСТА (Локальный режим):")
        print(f"Код: {result.code} | Класс: {result.class_name} | Герой: {result.hero_name}")
        print(f"Тип: {result.quest_type} | Баллы: {result.scores}")
        print("="*50 + "\n")
        return {"success": True, "message": "Результат сохранён в консоли сервера (таблица недоступна)."}

    try:
        row = [
            result.code.upper(), result.hero_name, result.class_name,
            result.scores.get("date", ""), result.quest_type,
            result.scores.get("Ч-П", 0), result.scores.get("Ч-Т", 0),
            result.scores.get("Ч-Х", 0), result.scores.get("Ч-Ч", 0),
            result.scores.get("Ч-З", 0), result.choices
        ]
        sheet.append_row(row)
        return {"success": True, "message": "Результат сохранён в Гильдии!"}
    except Exception as e:
        print(f"❌ Ошибка записи в таблицу: {e}")
        raise HTTPException(status_code=500, detail=f"Не удалось сохранить: {str(e)}")