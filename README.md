# Telegram Feedback Constructor Platform

Мультибот-платформа на Python + aiogram 3:
- конструктор-бот с личными кабинетами админов,
- динамический запуск/остановка подключенных feedback-ботов,
- анонимный мост "клиент <-> админ" для каждого экземпляра.

## Возможности

### Конструктор-бот
- подключение ботов по токену BotFather;
- кабинет администратора (мои боты, статистика, экспорт CSV);
- управление статусом бота (вкл/выкл);
- изменение приветствия для подключенного бота;
- owner-only глобальная рассылка по всем экземплярам.

### Feedback-боты
- анонимная пересылка сообщений клиент -> админ -> клиент;
- диалоги и маршрутизация ответов;
- команды `/answer`, `/broadcast`, `/block`, `/unblock`, `/stats`, `/bind`, `/setwelcome`;
- поддержка контента: text, voice, photo, video, audio, documents.

### Платформа
- multi-tenant модель (каждый админ управляет только своими ботами);
- SQLite + SQLAlchemy (async), миграции совместимости;
- Redis FSM с fallback на MemoryStorage;
- Docker-ready;
- логирование, глобальный обработчик ошибок, process-lock от дублей процесса.

## Структура проекта

```text
.
├── app.py
├── bot/
├── database/
├── handlers/
├── keyboards/
├── services/
├── utils/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Быстрый запуск (локально)

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

## Запуск через Docker

```bash
cp .env.example .env
docker compose up --build -d
```

## Переменные окружения

Смотрите `.env.example`.

Основные:
- `CONSTRUCTOR_BOT_TOKEN` - токен конструктора (кабинет);
- `BOT_TOKENS` - необязательные seed-токены managed-ботов;
- `ADMIN_CHAT_ID` / `BOT_ADMIN_CHAT_IDS` - admin chat для seed-ботов;
- `SERVICE_OWNER_TELEGRAM_IDS` - Telegram IDs владельцев сервиса (owner-команды);
- `DATABASE_URL`, `REDIS_URL`, `MANAGED_BOTS_SYNC_INTERVAL_SECONDS`, `LOG_LEVEL`.

## Подготовка к GitHub

Репозиторий уже подготовлен для переноса:
- безопасный `.gitignore` (env, базы, кэш, IDE, node artifacts);
- шаблоны для PR и Issues (bug/feature), плюс issue config;
- `CODEOWNERS` для авто-назначения ревьюеров;
- GitHub Actions CI workflow;
- release checklist: `docs/RELEASE_CHECKLIST.md`;
- upload guide: `docs/GITHUB_UPLOAD.md`;
- `LICENSE` и `CONTRIBUTING.md`.

Рекомендуемый порядок переноса:
1. Создать новый репозиторий на GitHub.
2. Добавить remote:
   ```bash
   git remote add origin <your-repo-url>
   ```
3. Запушить ветки:
   ```bash
   git push -u origin <branch>
   ```
4. Проверить GitHub Actions (workflow CI).
5. Заполнить Secrets/Variables (если понадобится CI/CD для деплоя).

## Важно по безопасности

- Никогда не коммитить реальный `.env`.
- Токены ботов хранить только в Secrets/Variables CI/CD или в защищенной среде.
- Перед публикацией убедиться, что в истории коммитов нет секретов.
