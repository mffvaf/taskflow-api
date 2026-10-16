# Task API

Учебный проект — API для управления задачами команды.
Можно создавать пользователей, проекты, метки, задачи и комментарии.

## Технологии

- Python 3.12
- FastAPI
- PostgreSQL 16
- SQLAlchemy 2
- Alembic
- Docker Compose

## Как запустить

Нужно установить и запустить Docker Desktop.

В терминале из папки проекта:

```bash
cp .env.example .env
docker compose up --build -d
```

Миграции применяются автоматически.

После запуска:

- Документация API: http://localhost:8000/docs
- Проверка подключения к базе: http://localhost:8000/health

В `/docs` можно отправлять запросы через кнопку Try it out.

Посмотреть состояние контейнеров и логи:

```bash
docker compose ps
docker compose logs api
```

## Примеры запросов

Создать пользователя:

```bash
curl -X POST http://localhost:8000/v1/users \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","display_name":"Анна"}'
```

Создать проект:

```bash
curl -X POST http://localhost:8000/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"name":"Первый проект"}'
```

## Возможности API

Для пользователей, проектов, меток, задач и комментариев
реализованы создание, получение списка и записи по id,
частичное обновление и удаление.

Основные адреса:

- `/v1/users`
- `/v1/projects`
- `/v1/labels`
- `/v1/tasks`
- `/v1/comments`

Задачи можно фильтровать по проекту и статусу:

```text
/v1/tasks?project_id=1&status=open
```

Комментарии — по задаче:

```text
/v1/comments?task_id=1
```

При неправильных данных возвращается 422,
если запись не найдена — 404, при конфликте данных — 409.

## Проверка миграций

Выполнять на тестовой базе: откат удаляет таблицы и данные.

```bash
docker compose stop api
docker compose run --rm api alembic upgrade head
docker compose run --rm api alembic downgrade base
docker compose run --rm api alembic upgrade head
docker compose up -d api
```

## Остановка и повторный запуск

```bash
docker compose down
docker compose up -d
```

Данные сохраняются в Docker volume.
Команда `docker compose down -v` удаляет их.

Файл `.env` и виртуальное окружение `.venv` в Git не добавляются.