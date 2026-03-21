# Деплой в продакшн

В продакшене поднимаются **два отдельных сервиса**:

1. **REST API** — приложение FastAPI (`main:app`), HTTP.
2. **WebSocket-сервер** — `web/server.py` (отдельный порт, тот же `.env` и зависимости).

Оба читают настройки из переменных окружения и используют общую MySQL через `DATABASE_URL`. Таблицы создаются при старте API (`init_db`).

---

## Требования

- Python 3.10+ (рекомендуется версия, с которой вы разрабатываете локально).
- MySQL с созданной пустой БД (имя из URL в `DATABASE_URL`).
- Для браузерных клиентов за другим origin — настройка `CORS_ALLOWED_ORIGINS` (см. ниже).

---

## Подготовка на сервере

```bash
git clone <url-репозитория> /opt/fastapi-support-tickets
cd /opt/fastapi-support-tickets
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Создайте файл окружения (не коммитьте его в git):

```bash
cp .env.example .env
```

### Переменные окружения

| Переменная | Назначение |
|------------|------------|
| `DATABASE_URL` | Async URL SQLAlchemy для MySQL, например `mysql+aiomysql://user:pass@127.0.0.1:3306/support_tickets` |
| `API_KEY_USER` | Ключ для пользовательских эндпоинтов |
| `API_KEY_ADMIN` | Ключ для админских эндпоинтов |
| `UPLOAD_DIR` | Каталог для загрузок (должен быть доступен процессу на запись; сохраняйте на диске между перезапусками) |
| `CORS_ALLOWED_ORIGINS` | Список origin для WebSocket (через запятую, без пробелов после запятой или с trim). Пусто — без проверки Origin (удобно для скриптов, **нежелательно для публичного интернета**). Пример: `https://app.example.com,https://admin.example.com` |
| `WS_PORT` | Порт standalone WebSocket-процесса (`python web/server.py`), по умолчанию `8765` |

Сгенерировать ключи:

```bash
python -c "import uuid; print(uuid.uuid4())"
```

Убедитесь, что каталог `UPLOAD_DIR` существует или будет создан при старте API; для продакшена лучше заранее выделить отдельный путь (например `/var/lib/support-tickets/uploads`) и выставить права пользователю сервиса.

---

## Запуск REST API

Рекомендуется за reverse proxy (nginx, Caddy) с TLS.

**Вариант A — uvicorn напрямую (проще всего):**

```bash
source /opt/fastapi-support-tickets/.venv/bin/activate
cd /opt/fastapi-support-tickets
uvicorn main:app --host 0.0.0.0 --port 8000 --proxy-headers
```

`--proxy-headers` полезен, если TLS терминирует nginx и нужны корректные схема/клиент за `X-Forwarded-*`.

**Вариант B — Gunicorn + UvicornWorker (несколько воркеров для HTTP):**

```bash
gunicorn main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers 4
```

При необходимости добавьте те же флаги прокси, что поддерживает ваша обвязка (часто настраивается в `gunicorn`/`uvicorn` через переменные или конфиг).

Документация OpenAPI после запуска: `/docs`.

---

## Запуск WebSocket-сервера

Сервер реализован в `web/server.py`. Соответствия клиентов хранятся **в памяти процесса**, поэтому для корректной доставки сообщений между подключёнными клиентами нужен **один рабочий процесс** WebSocket (не запускайте несколько воркеров за одним балансировщиком без sticky-сессий и понимания ограничений).

**Вариант 1 — ASGI через uvicorn (удобно для единообразия с API):**

```bash
source /opt/fastapi-support-tickets/.venv/bin/activate
cd /opt/fastapi-support-tickets
uvicorn web.server:app --host 0.0.0.0 --port 8765 --proxy-headers
```

Порт можно заменить на другой; тогда обновите прокси и URL у клиентов.

**Вариант 2 — встроенный asyncio-сервер библиотеки `websockets`:**

```bash
python web/server.py
# или явный порт:
python web/server.py 8765
```

Порт по умолчанию берётся из `WS_PORT` в `.env`.

Для продакшена за HTTPS используйте **WSS** на стороне прокси (см. ниже).

---

## Nginx как reverse proxy (пример)

TLS и маршрутизация обычно на nginx. Отдельные `server` или `location` для API и WebSocket.

```nginx
# REST API
server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate     /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# WebSocket (отдельный хост или путь)
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

server {
    listen 443 ssl http2;
    server_name ws.example.com;

    ssl_certificate     /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8765;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

Клиенты в браузере подключаются к `wss://ws.example.com/`. Поле `Origin` должно попадать в `CORS_ALLOWED_ORIGINS`, если список задан.

---

## systemd (пример юнитов)

Пользователь сервиса должен иметь права на `UPLOAD_DIR` и чтение `.env`.

`/etc/systemd/system/support-tickets-api.service`:

```ini
[Unit]
Description=Support Tickets REST API
After=network.target mysql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/fastapi-support-tickets
EnvironmentFile=/opt/fastapi-support-tickets/.env
ExecStart=/opt/fastapi-support-tickets/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --proxy-headers
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

`/etc/systemd/system/support-tickets-ws.service`:

```ini
[Unit]
Description=Support Tickets WebSocket
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/fastapi-support-tickets
EnvironmentFile=/opt/fastapi-support-tickets/.env
ExecStart=/opt/fastapi-support-tickets/.venv/bin/uvicorn web.server:app --host 127.0.0.1 --port 8765 --proxy-headers
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now support-tickets-api.service support-tickets-ws.service
```

Пути и пользователя замените на свои.

---

## Supervisord

В репозитории есть пример `web/supervisord.conf` с путями от другого проекта — перед использованием **отредактируйте** `command`, `environment`, `user`, `stdout_logfile` под этот проект и виртуальное окружение. Запуск API добавьте отдельной секцией `[program:support-tickets-api]` по аналогии.

---

## Проверка после деплоя

- `GET https://api.example.com/` — ожидается JSON с сообщением о API.
- `GET https://api.example.com/docs` — Swagger.
- WebSocket: подключение с клиента к `wss://...` и проверка приветственного сообщения сервера.

---

## Краткий чеклист безопасности

- Сильные случайные `API_KEY_*`, не храните их в репозитории.
- MySQL только с локального хоста или приватной сети; отдельный пользователь БД с минимальными правами.
- TLS на публичных endpoint’ах.
- Для браузерных клиентов задайте явный `CORS_ALLOWED_ORIGINS`.
- Ограничьте доступ к портам `8000`/`8765` файрволом, наружу пусть смотрит только nginx (или аналог).
