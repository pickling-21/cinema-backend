# Auth Service

Микросервис аутентификации и авторизации на FastAPI с JWT-токенами, PostgreSQL и Redis.

- Регистрация и аутентификация пользователей
- JWT access/refresh токены
- Чёрный список токенов в Redis
- CRUD (admin, subscriber, member)
- CLI для создания суперпользователя

## Быстрый старт

1. Переменные окружения заполнить

```bash
cp .env.example .env
```

2. Запуск через docker compose

```bash
docker compose up -d
```
3. Локальная разработка

```bash
# Поднять только БД и redis
docker compose up -d db redis

# зависимости
uv sync
# или
pip install -e .

# Применить миграции
alembic upgrade head

# Запустить приложение
uvicorn src.main:app --reload
```

4. Создание суперпользователя

```bash
python -m src.cli --login admin --password secret
```

## API

Базовый путь: `/api/v1`

API для сайта и личного кабинета:

`/auth/`
- `signup/` регистрация пользователя;
- `login/` вход пользователя в аккаунт (обмен логина и пароля на пару токенов: JWT-access токен и refresh токен);
- `refresh/` выдача новой пары токенов в обмен на корректный refresh-токен, обновление access токена; 
- `logout/` выход пользователя из аккаунта;

API для управления доступами:

`/roles/`
- роли пользователя в виде ENUM;
- `grant/` назначить пользователю роль;
- `revoke/` отобрать у пользователя роль;
- `check/` метод для проверки наличия прав у пользователя.

См. http://localhost:8000/api/openapi

## Тесты

### Локально

```bash
docker compose -f docker-compose.tests.yaml up -d db redis
uv run alembic upgrade head
uv run pytest tests/ -v
```

### Через Docker Compose

```bash
docker compose -f docker-compose.tests.yaml build --no-cache
docker compose -f docker-compose.tests.yaml up --abort-on-container-exit 
```