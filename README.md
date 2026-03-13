# Telegram Feedback Bot (aiogram 3, Clean Architecture)

Production-ready Telegram Feedback Bot на Python и aiogram 3.
Бот выступает анонимным мостом между пользователем и администратором.

## Основные возможности

- анонимный канал связи user → admin → user
- авто-регистрация пользователей
- создание и хранение диалогов
- детекция ответов администратора по reply
- маршрутизация сообщений с привязкой к диалогу
- поддержка контента:
  - text
  - voice
  - photo
  - video
  - audio
  - documents
- статистика (`/stats`)
- рассылки (`/broadcast`)
- поддержка нескольких ботов через список токенов
- Redis FSM (состояния администратора)
- SQLite + SQLAlchemy
- Docker-ready
- логирование и централизованная обработка ошибок

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
│   ├── models.py
│   └── session.py
├── bot/
│   ├── __init__.py
│   ├── factory.py
│   └── runtime.py
├── handlers/
│   ├── __init__.py
│   ├── admin.py
│   ├── errors.py
│   └── user.py
├── services/
│   ├── __init__.py
│   ├── bot_registry_service.py
│   ├── broadcast_service.py
│   ├── dialog_service.py
│   ├── routing_service.py
│   └── stats_service.py
├── keyboards/
│   ├── __init__.py
│   └── admin.py
└── utils/
    ├── __init__.py
    ├── config.py
    ├── constants.py
    └── logging.py
```

## Модели БД

- `users`
- `dialogs`
- `messages`
- `bots`

## Локальный запуск

1. Создайте `.env` из примера:

```bash
cp .env.example .env
```

2. Укажите переменные:

- `BOT_TOKENS` — токены через запятую
- `ADMIN_CHAT_ID` — id админ-чата/группы
- `BOT_ADMIN_CHAT_IDS` — (опционально) список chat id по порядку токенов

3. Установите зависимости и запустите:

```bash
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

## Как работает диалог

1. Пользователь пишет боту.
2. Бот копирует сообщение в админ-чат.
3. Администратор отвечает reply на пересланное сообщение.
4. Бот копирует ответ админа обратно пользователю.
5. В БД сохраняется связка сообщений для маршрутизации и статистики.

> Telegram ID администратора не раскрывается пользователю — отправителем для пользователя всегда выступает бот.
