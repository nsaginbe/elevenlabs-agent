# API Examples

## Создание тренировочной сессии

```bash
curl -X POST "http://127.0.0.1:8000/api/sessions/" \
  -H "Content-Type: application/json" \
  -d '{"manager_name": "Иван Петров"}'
```

Response:
```json
{
  "id": 1,
  "manager_name": "Иван Петров",
  "session_start": "2024-01-15T10:30:00.000Z",
  "session_end": null,
  "conversation_log": null,
  "ai_analysis": null,
  "score": null,
  "feedback": null,
  "status": "active"
}
```

## Завершение сессии

```bash
curl -X PUT "http://127.0.0.1:8000/api/sessions/1/complete" \
  -H "Content-Type: application/json" \
  -d '{"conversation_log": "Лог разговора здесь..."}'
```

## Получение сессии

```bash
curl "http://127.0.0.1:8000/api/sessions/1"
```

Response:
```json
{
  "id": 1,
  "manager_name": "Иван Петров",
  "session_start": "2024-01-15T10:30:00.000Z",
  "session_end": "2024-01-15T10:45:00.000Z",
  "conversation_log": "Полный лог разговора...",
  "ai_analysis": "# Анализ тренировочной сессии...",
  "score": 7.5,
  "feedback": "Хорошая работа с возражениями...",
  "status": "analyzed"
}
```

## Список всех сессий

```bash
curl "http://127.0.0.1:8000/api/sessions/"
```

## JavaScript примеры

### Создание сессии
```javascript
const response = await fetch('/api/sessions/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({ 
        manager_name: 'Иван Петров' 
    })
});

const session = await response.json();
console.log('Сессия создана:', session.id);
```

### Завершение сессии
```javascript
const response = await fetch(`/api/sessions/${sessionId}/complete`, {
    method: 'PUT',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        conversation_log: conversationText
    })
});

const completedSession = await response.json();
console.log('Оценка:', completedSession.score);
```

### Получение анализа
```javascript
// Проверяем готовность анализа
const checkAnalysis = async (sessionId) => {
    const response = await fetch(`/api/sessions/${sessionId}`);
    const session = await response.json();
    
    if (session.status === 'analyzed') {
        console.log('Анализ готов!');
        console.log('Оценка:', session.score);
        console.log('Обратная связь:', session.ai_analysis);
        return session;
    } else {
        console.log('Анализ в процессе...');
        return null;
    }
};
```

## Python примеры

### Использование с requests
```python
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

# Создание сессии
response = requests.post(
    f"{BASE_URL}/api/sessions/",
    json={"manager_name": "Иван Петров"}
)
session = response.json()
print(f"Сессия создана: {session['id']}")

# Завершение сессии
response = requests.put(
    f"{BASE_URL}/api/sessions/{session['id']}/complete",
    json={"conversation_log": "Лог разговора..."}
)
completed_session = response.json()
print(f"Оценка: {completed_session['score']}")
```

### Асинхронный клиент
```python
import aiohttp
import asyncio

async def create_session(manager_name):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://127.0.0.1:8000/api/sessions/",
            json={"manager_name": manager_name}
        ) as response:
            return await response.json()

# Использование
session = await create_session("Иван Петров")
```

## WebSocket для реального времени (будущее расширение)

```javascript
// Пример для будущего WebSocket API
const ws = new WebSocket('ws://127.0.0.1:8000/ws/session/1');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'analysis_update') {
        console.log('Промежуточный анализ:', data.partial_analysis);
    }
    
    if (data.type === 'conversation_event') {
        console.log('Событие разговора:', data.event);
    }
};

// Отправка событий
ws.send(JSON.stringify({
    type: 'conversation_start',
    session_id: 1
}));
```