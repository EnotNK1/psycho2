# Настройки

Все настройки находятся в `.env`, который создаётся `python scripts/init_env.py`. Файл читается относительно корня compas, независимо от рабочей папки процесса.

| Переменная | Значение / назначение |
|---|---|
| MODE | LOCAL, TEST, PROD |
| DB_HOST / DB_PORT | localhost:5544 при запуске Python; Compose подставляет db:5432 |
| DB_USER / DB_NAME | compas / compas |
| DB_PASS | Независимый случайный пароль |
| DB_POOL_SIZE / DB_MAX_OVERFLOW | По умолчанию 5 / 5 **на процесс** |
| JWT_SECRET_KEY / JWT_REFRESH_SECRET_KEY | Разные случайные ключи, минимум 32 символа |
| DATA_ENCRYPTION_KEY | Отдельный Fernet-ключ результатов |
| ACCESS_TOKEN_EXPIRE_MINUTES | 30 |
| REFRESH_TOKEN_EXPIRE_DAYS | 7 |
| COOKIE_SECURE | false локально, true при HTTPS |
| ALLOWED_ORIGINS | JSON-массив точных адресов фронтенда, например `["http://localhost:3000"]` |
| SMTP_HOST / SMTP_PORT | Адрес SMTP, порт STARTTLS (по умолчанию 587) |
| SMTP_USER / SMTP_PASSWORD / SMTP_FROM | Учётные данные и адрес отправителя |
| PASSWORD_RESET_URL | Реальный URL формы сброса пароля на фронтенде |

Сохраните копию ключа шифрования отдельно от БД в защищённом хранилище. Смена или потеря ключа делает старые зашифрованные результаты нечитаемыми. Не используйте секреты «Одеяло» для новой пустой БД.

Перед публикацией настройте HTTPS и reverse proxy, COOKIE_SECURE=true и точные ALLOWED_ORIGINS. Compose по умолчанию слушает только loopback. Лимиты запросов и мониторинг инфраструктуры настраиваются при развёртывании.
