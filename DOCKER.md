# Запуск ResumeReview в Docker Compose

Наружу публикуется только Nginx с собранным React-приложением. Браузер вызывает
относительный адрес `/api`, а Nginx проксирует его во внутренний контейнер
`backend:8000`. Redis доступен только во внутренней сети Compose. PostgreSQL или
Supabase остаётся внешней базой данных и настраивается переменными окружения.

## Настройка

Скопируйте `.env.compose.example` в `.env`, заполните подключение к PostgreSQL,
задайте длинный случайный `SECRET_KEY` и необходимые серверные интеграции.

Для локального запуска оставьте:

```env
FRONTEND_PORT=8080
FRONTEND_URL=http://localhost:8080
COOKIE_SECURE=false
```

Для публичного HTTPS-домена укажите его точный origin, например
`FRONTEND_URL=https://resume.example.com`, и задайте `COOKIE_SECURE=true`.

## Запуск

```powershell
docker compose up --build -d
docker compose ps
```

Frontend будет доступен по адресу `http://localhost:8080`. Backend сначала
дождётся готовности Redis, применит `alembic upgrade head` к настроенной базе и
затем запустит FastAPI.

Остановка:

```powershell
docker compose down
```

Данные Redis сохраняются в именованном томе `redis-data`. Команда
`docker compose down --volumes` удалит этот том и все refresh-сессии.
