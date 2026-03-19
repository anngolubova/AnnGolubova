# Contributing

Спасибо за вклад в проект.

## Local setup

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Before creating PR

1. Проверить, что проект компилируется:
   ```bash
   python3 -m compileall app.py bot handlers services database keyboards utils
   ```
2. Обновить README/.env.example, если добавлены новые переменные окружения.
3. Не коммитить `.env`, базы данных и секреты.

## Commit style

Рекомендуется использовать короткие и понятные conventional-style заголовки:
- `feat: ...`
- `fix: ...`
- `docs: ...`
- `refactor: ...`

## Pull Request checklist

- [ ] Описание проблемы и что изменено
- [ ] Проверены edge-cases
- [ ] Обновлена документация (если нужно)
- [ ] Нет секретов в diff
