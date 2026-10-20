from io import BytesIO

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile

from auth import require_user
from fastapi.responses import StreamingResponse

from diasavto_validator.catalog_io import (
    MAX_UPLOAD_BYTES,
    CatalogFormatError,
    create_report,
    parse_catalog,
)
from diasavto_validator.hi_lex import validate_catalog

app = FastAPI(title="DiasAvto Certificate Validator", docs_url=None, redoc_url=None)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/validate", response_class=StreamingResponse)
async def validate(
    file: UploadFile = File(...), user_id: str = Depends(require_user)
) -> StreamingResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Не указано имя файла")
    if file.content_type not in (
        "text/csv",
        "application/csv",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/octet-stream",
    ):
        raise HTTPException(status_code=415, detail="Ожидается CSV или XLSX")
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    await file.close()
    try:
        catalog = parse_catalog(content, file.filename)
    except CatalogFormatError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    report = create_report(validate_catalog(catalog))
    if len(report) > 4 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Отчёт слишком большой")
    return StreamingResponse(
        BytesIO(report),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": 'attachment; filename="validation-report.xlsx"',
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )
