# Sales Training Platform

Веб-сервис для тренировки продажников с ИИ-клиентом в реальном времени, используя ElevenLabs ConvAI.

## Возможности

- 🎯 **Интерактивная тренировка**: Менеджер говорит с ИИ-клиентом голосом в реальном времени
- 🤖 **ИИ-анализ**: Автоматический анализ разговора после завершения сессии
- 📊 **Подробная обратная связь**: Оценки, сильные стороны, области для улучшения
- 📈 **История тренировок**: Отслеживание прогресса во времени
- 🎨 **Современный интерфейс**: Удобный веб-интерфейс с адаптивным дизайном

## Архитектура

```
├── backend/           # FastAPI бэкенд
│   ├── main.py       # Основное приложение
│   ├── database.py   # Модели базы данных
│   ├── models.py     # Pydantic модели
│   └── analyzer.py   # Анализатор разговоров
├── frontend/         # Веб-интерфейс
│   ├── templates/    # HTML шаблоны
│   └── static/       # CSS и JavaScript
└── database/         # SQLite база данных
```

## Установка и запуск

### 1. Установка зависимостей

```bash
cd backend
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Скопируйте `.env.example` в `.env` и заполните:

```bash
cp .env.example .env
```

Обязательные параметры:
- `ELEVENLABS_API_KEY` - ваш API ключ ElevenLabs
- `ELEVENLABS_AGENT_ID` - ID вашего ConvAI агента
- `OPENAI_API_KEY` - API ключ OpenAI для анализа (опционально)

### 3. Запуск сервера

```bash
cd backend
python main.py
```

Приложение будет доступно по адресу: http://127.0.0.1:8000

## Использование

1. **Откройте приложение** в браузере
2. **Введите ваше имя** в поле "Ваше имя"
3. **Нажмите "Начать тренировку"** - откроется виджет ElevenLabs ConvAI
4. **Говорите с ИИ-клиентом** голосом в реальном времени
5. **Скажите "Завершить"** или нажмите кнопку "Завершить тренировку"
6. **Дождитесь анализа** - ИИ проанализирует ваш разговор
7. **Изучите обратную связь** на странице анализа

## API Endpoints

- `GET /` - Главная страница
- `POST /api/sessions/` - Создать новую сессию
- `GET /api/sessions/{id}` - Получить сессию
- `PUT /api/sessions/{id}/complete` - Завершить сессию
- `GET /api/sessions/{id}/analysis` - Страница анализа
- `GET /api/sessions/` - Список всех сессий

## Настройка ElevenLabs ConvAI

1. Создайте агента в [ElevenLabs](https://elevenlabs.io/app/conversational-ai)
2. Настройте личность агента как "клиента" для ваших продуктов
3. Добавьте стоп-слово "Завершить" для автоматического завершения
4. Скопируйте Agent ID в переменную `ELEVENLABS_AGENT_ID`

## Анализ разговоров

Система использует OpenAI GPT-4 для анализа разговоров по критериям:
- Установление контакта с клиентом
- Выявление потребностей
- Презентация продукта/услуги  
- Работа с возражениями
- Закрытие сделки
- Общее впечатление

## Технологии

- **Backend**: FastAPI, SQLAlchemy, SQLite
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **AI**: ElevenLabs ConvAI, OpenAI GPT-4
- **Database**: SQLite
- **UI**: Font Awesome, CSS Grid/Flexbox

## Разработка

### Структура базы данных

```sql
CREATE TABLE training_sessions (
    id INTEGER PRIMARY KEY,
    manager_name VARCHAR,
    session_start DATETIME,
    session_end DATETIME,
    conversation_log TEXT,
    ai_analysis TEXT,
    score FLOAT,
    feedback TEXT,
    status VARCHAR
);
```

### Добавление новых функций

1. **Новые критерии анализа**: Модифицируйте `analyzer.py`
2. **Дополнительные поля**: Обновите модели в `database.py` и `models.py`
3. **UI изменения**: Редактируйте шаблоны в `frontend/templates/`

## Лицензия

MIT License