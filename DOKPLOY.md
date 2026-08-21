# Развертывание ResumeReview в Dokploy

## Топология

Dokploy/Traefik завершает TLS для `test.srubai.ru` и отправляет HTTP-трафик на
внутренний порт `80` сервиса `frontend`. Nginx отдаёт React SPA и проксирует
`/api` во внутренний сервис `backend:8000`. Backend и Redis не публикуют порты
на хост.

Используйте тип развертывания **Docker Compose**, а не Docker Stack: конфигурация
собирает образы через `build`.

## DNS

До добавления домена в Dokploy создайте A-запись:

```text
test.srubai.ru -> IPv4-адрес сервера Dokploy
```

DNS должен указывать на сервер до запроса сертификата Let's Encrypt.

## Compose

Создайте Compose service из Git-репозитория и задайте:

```text
Compose Path: ./docker-compose.dokploy.yml
```

В разделе Environment добавьте содержимое `.env.dokploy.example`, заменив
пустые значения и `SECRET_KEY` реальными секретами. Обязательные production
настройки:

```env
FRONTEND_URL=https://test.srubai.ru
COOKIE_SECURE=true
```

Dokploy записывает эти значения в `.env`; директива `env_file` передаёт их
backend-контейнеру. Не добавляйте `FRONTEND_PORT`: host-порт не используется.

## Домен и сертификат

После первого успешного deploy откройте вкладку Domains у Compose service и
создайте домен со значениями:

```text
Host: test.srubai.ru
Path: /
Service: frontend
Container Port: 80
HTTPS: On
Certificate: Let's Encrypt
Strip Path: Off
```

Internal Path оставьте пустым. После создания или изменения домена выполните
redeploy Compose service: Dokploy применяет домены Compose через Traefik labels
во время развертывания.

Не добавляйте host ports и ручные Traefik labels: нативная вкладка Domains сама
подключает frontend к нужной сети и создаёт маршрутизацию. Backend доступен только
Nginx по имени `backend:8000`, Redis — только backend по имени `redis:6379`.

## Проверка после deploy

```text
https://test.srubai.ru/
https://test.srubai.ru/health
```

`/health` должен вернуть `{"status":"ok"}`. Затем проверьте вход и обновление
страницы: refresh-cookie должен иметь атрибуты `HttpOnly`, `Secure`,
`SameSite=Lax` и путь `/api/auth`.
