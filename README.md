# ДиасАвто+ — проверка масок сертификатов

Веб-приложение распознаёт маски артикулов HI-LEX CORPORATION из сертификатов и позволяет скачать список распознанных разрешённых масок (CSV). Каталог товаров не загружается и все возможные комбинации артикулов не генерируются.

## Возможности

- Сертификаты PDF с текстовым слоем, DOCX и TXT (без OCR).
- Проверка по 38 утверждённым маскам HI-LEX, сортировка и удаление повторов.
- Выгрузка масок в CSV.
- Проверка отдельного артикула по маскам загруженного сертификата.
- Авторизация через Supabase.

## Разработка

Backend: Python 3.11+, FastAPI. Frontend: React, TypeScript, Vite.

```bash
python -m pip install -e './backend[dev]'
PYTHONPATH=backend:backend/src pytest backend/tests -q
ruff check backend

cd frontend
npm install
npm run build
```

Для локального frontend задайте переменные по примеру `frontend/.env.example`. Ключ Supabase должен быть только **publishable**, никогда не service_role.

## Публикация

- Backend: Vercel, `https://diasavto-validator-api.vercel.app/api/health`.
- Frontend: GitHub Pages, `https://medvedushechka.github.io/diasavto-certificate-validator/` после настройки Pages.
- Workflow: `.github/workflows/pages.yml`. В репозитории GitHub нужно выбрать **Settings → Pages → Build and deployment → GitHub Actions**.
- Backend должен быть развёрнут с CORS для `https://medvedushechka.github.io` до проверки формы через GitHub Pages.

## Безопасность

Не публикуйте реальные закрытые сертификаты, данные клиентов, пароли, токены или приватные API-ключи. Соответствие маске не подтверждает существование артикула у производителя.
