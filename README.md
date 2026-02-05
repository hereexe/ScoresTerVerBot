# ScoresTerVerBot

Telegram-бот на `aiogram v3` для учета баллов.

Регистрация нового пользователя выполняется через верификацию ответа `@fiitobot`:
- пользователь в нашем боте вводит только `Имя Фамилию` (например: `Елисей Яковлев`);
- бот автоматически формирует строку запроса `@fiitobot Имя Фамилия` внутри авторизации (без отдельного сообщения с этой строкой от бота);
- далее бот ожидает карточку-ответ от `@fiitbot` и просит прислать ее в чат;
- бот извлекает ФИ в формате `Фамилия Имя` из первой строки карточки и сохраняет в БД.

## Локальный запуск (Windows / PowerShell)

0) Запустите MongoDB (если нет своей):

```powershell
docker compose up -d
```

1) Создайте файл `.env`:

- Скопируйте `.env.example` → `.env`
- Заполните переменные:
  - `BOT_TOKEN` — токен Telegram-бота
  - `MONGODB_URI` — строка подключения к MongoDB (например, `mongodb://localhost:27017`)
  - `DB_NAME` — имя БД (по умолчанию `scores_bot`)
  - `ADMINS` — TG user id админов (через запятую), чтобы работала команда `/add_lecture`

2) Установите зависимости:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```

3) Запустите бота:

```powershell
.\.venv\Scripts\python main.py
```
