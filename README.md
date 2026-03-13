# Telegram Bot Constructor + Feedback Bridge (aiogram 3)

Production-ready проект на Python + aiogram 3:  
бот-конструктор с личными кабинетами админов и динамическим управлением несколькими feedback-ботами.

## Что теперь умеет система

### 1) Конструктор-бот (Admin Bot)

- персональный кабинет каждого админа
- кнопочная навигация:
  - `➕ Добавить бота`
  - `🤖 Мои боты`
  - `📊 Моя статистика`
  - `📥 Выгрузка базы`
- добавление нового Telegram-бота по токену из BotFather
- включение/выключение каждого бота прямо из кабинета
- выгрузка базы пользователей в CSV

### 2) Управляемые feedback-боты

- анонимный мост user → admin → user
- авто-регистрация пользователей
- создание и хранение диалогов
- определение ответов администратора по `reply`
- threading диалогов
- рассылки (`/broadcast`)
- статистика (`/stats`)
- поддержка контента:
  - text
  - voice
  - photo
  - video
  - audio
  - documents

### 3) Платформенные возможности

- multi-tenant: у каждого админа свои боты и свои данные
- динамический запуск/остановка управляемых ботов без рестарта приложения
- SQLite + SQLAlchemy (async)
- Redis FSM
- Docker-ready
- логирование и глобальный error handler

## Архитектура (папки)

```text
.
├── app.py
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── database/
│   ├── __init__.py
│   ├── base.py
│   ├── migrations.py
│   ├── models.py
│   └── session.py
├── bot/
│   ├── __init__.py
│   ├── factory.py
│   └── runtime.py
├── handlers/
│   ├── __init__.py
│   ├── admin.py
│   ├── cabinet.py
│   ├── errors.py
│   └── user.py
├── services/
│   ├── __init__.py
│   ├── bot_registry_service.py
│   ├── broadcast_service.py
│   ├── cabinet_service.py
│   ├── dialog_service.py
│   ├── polling_manager.py
│   ├── routing_service.py
│   └── stats_service.py
├── keyboards/
│   ├── __init__.py
│   ├── admin.py
│   └── cabinet.py
└── utils/
    ├── __init__.py
    ├── config.py
    ├── constants.py
    └── logging.py
```

## Модели БД

- `admins`
- `bots`
- `users`
- `dialogs`
- `messages`

## Конфигурация `.env`

```env
# Токен конструктора (кабинеты админов)
CONSTRUCTOR_BOT_TOKEN=...

# Опционально: seed-набор уже готовых feedback-ботов
BOT_TOKENS=

# Для seed-ботов
ADMIN_CHAT_ID=
# BOT_ADMIN_CHAT_IDS=

DATABASE_URL=sqlite+aiosqlite:///./data/feedback_bot.db
REDIS_URL=redis://localhost:6379/0
MANAGED_BOTS_SYNC_INTERVAL_SECONDS=8
LOG_LEVEL=INFO
```

## Локальный запуск

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Docker запуск

```bash
cp .env.example .env
docker compose up --build -d
```

## Как работает в проде

1. Админ открывает конструктор-бота (`/start`), получает личный кабинет.
2. Добавляет токен нового бота через кнопку `➕ Добавить бота`.
3. Платформа валидирует токен, сохраняет бота в БД и автоматически поднимает polling.
4. Пользователи пишут уже в подключенный feedback-бот.
5. Сообщения уходят админу, ответы админа (reply) возвращаются пользователю.

> ID администратора остаётся скрытым: пользователь всегда видит отправителем только бота.
