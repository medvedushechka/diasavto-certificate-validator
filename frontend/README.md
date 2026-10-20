# Веб-интерфейс проверки сертификатов

React + TypeScript + Vite. Интерфейс принимает каталог CSV/XLSX и скачивает Excel-отчёт.

## Локальный запуск

В одном терминале:

```powershell
cd backend
python -m pip install -e ".[dev]"
python -m uvicorn app:app --reload
```

Во втором:

```powershell
cd frontend
npm install
npm run dev
```

Vite проксирует `/api` на `127.0.0.1:8000`.

## Развёртывание

До включения публичного доступа необходимо добавить авторизацию, ограничения запросов и решить вопрос маршрутизации `/api`. Не настраивайте публичный frontend на незащищённый API.

Рекомендуемая схема Vercel: два проекта из одного репозитория с root directories `frontend` и `backend`. При подключении production-контура настроить защищённую серверную маршрутизацию запросов.
