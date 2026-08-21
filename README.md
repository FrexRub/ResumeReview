# ResumeReview

Первая версия сервиса для защищенной загрузки и разбора документов с вакансиями. Проект состоит из FastAPI backend и React/Vite frontend.

## Возможности

- вход по имени пользователя;
- JWT access-токены и ротируемые refresh-токены в HttpOnly-cookie;
- хранение refresh-сессий в Redis;
- немедленный отзыв старых токенов после смены пароля;
- защищенный кабинет с загрузкой документов;
- сохранение разобранного текста вакансии для подбора кандидатов;
- серверная интеграция с [ParserDoc](https://parserdoc.srubai.ru/docs).

## Структура

```text
src/             FastAPI, SQLAlchemy, Redis и ParserDoc proxy
alembic/         миграции PostgreSQL
frontend/        React + TypeScript + Vite
 tests/           backend-тесты
```

## Backend

Требования: Python 3.12+, PostgreSQL/Supabase и локальный Redis.

1. Создайте окружение и установите зависимости:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install poetry
poetry install --with dev
```

2. Скопируйте `.env.template` в `.env` и заполните параметры Supabase, Redis и `SECRET_KEY`. Для локального frontend оставьте:

```env
FRONTEND_URL=http://localhost:5173
COOKIE_SECURE=false
PARSERDOC_URL=https://parserdoc.srubai.ru
```

Для скачивания резюме с Яндекс Диска также укажите серверный OAuth-токен:

```env
YANDEX_DISK_OAUTH_TOKEN=your_oauth_token
YANDEX_DISK_API_URL=https://cloud-api.yandex.net
YANDEX_DISK_TIMEOUT_SECONDS=120
```

В production задайте длинный случайный `SECRET_KEY`, HTTPS-адрес frontend и `COOKIE_SECURE=true`.

3. Примените миграции и запустите API:

```powershell
.venv\Scripts\alembic.exe upgrade head
.venv\Scripts\uvicorn.exe src.main:app --reload
```

API: `http://127.0.0.1:8000`, Swagger: `http://127.0.0.1:8000/docs`.

### Ручное создание пользователя в Supabase

Сначала безопасно получите bcrypt-хеш — пароль вводится скрыто и не сохраняется в истории команд:

```powershell
.venv\Scripts\python.exe -c "import bcrypt,getpass; p=getpass.getpass('Password: '); print(bcrypt.hashpw(p.encode(),bcrypt.gensalt()).decode())"
```

Затем выполните в Supabase SQL Editor, подставив имя и полученный хеш:

```sql
insert into users (name, hashed_password, is_active, is_superuser, auth_version)
values ('your_username', '$2b$...your_hash...', true, false, 0);
```

Если ранняя миграция проекта уже создала пользователя `revisor`, смените его пароль или удалите запись перед публикацией сервиса: прежний seed больше не создается.

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

По умолчанию Vite проксирует `/api` на `http://127.0.0.1:8000`. Для отдельного backend URL скопируйте `frontend/.env.example` в `frontend/.env` и задайте `VITE_API_URL`.

## Проверки

```powershell
.venv\Scripts\python.exe -m pytest
cd frontend
npm test
npm run build
```

## API первой версии

- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `GET /api/users/me`
- `POST /api/users/me/change-password`
- `POST /api/vacancies`
- `GET /api/vacancies/active`
- `PATCH /api/vacancies/active`
- `GET /api/vacancies/active/resumes`
- `GET /api/vacancies/resumes/{resume_id}/download`
- `PATCH /api/vacancies/resumes/{resume_id}/viewed`
- `POST /api/vacancies/parse`

`POST /api/vacancies` принимает извлечённый текст и имя файла из ответа ParserDoc:

```json
{
  "content": "Python developer",
  "filename": "vacancy.txt"
}
```

В `vacancy_resume.url_resume` хранится постоянный путь вида `disk:/test/resume.docx`. При скачивании backend получает свежий временный URL у Яндекс Диска и потоково передаёт файл авторизованному пользователю. OAuth-токен во frontend не передаётся.

Регистрация, восстановление пароля, хранение исходных файлов и сопоставление резюме с вакансией пока не входят в эту версию.
