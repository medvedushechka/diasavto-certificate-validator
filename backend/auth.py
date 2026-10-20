import os

import httpx
from fastapi import Header, HTTPException


async def require_user(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Требуется авторизация")

    token = authorization.removeprefix("Bearer ").strip()
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "")
    if not url or not key:
        raise HTTPException(status_code=503, detail="Авторизация не настроена")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{url}/auth/v1/user",
                headers={"apikey": key, "Authorization": f"Bearer {token}"},
            )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="Сервис авторизации недоступен") from exc
    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Сессия недействительна")
    subject = response.json().get("id")
    if not isinstance(subject, str) or not subject:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    return subject
