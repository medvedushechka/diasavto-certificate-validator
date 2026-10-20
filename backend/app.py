from io import BytesIO

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from auth import require_user
from fastapi.responses import StreamingResponse, JSONResponse

from diasavto_validator.catalog_io import (
    MAX_UPLOAD_BYTES,
    CatalogFormatError,
    create_report,
    parse_catalog,
)
from diasavto_validator.hi_lex import validate_catalog
from diasavto_validator.models import ValidationResult
from diasavto_validator.rule_registry import supplier_rules
from diasavto_validator.pdf_certificates import extract_pdf_masks, PdfCertificateError, MAX_PDF_BYTES
from diasavto_validator.certificates import (
    MAX_CERTIFICATE_BYTES,
    CertificateFormatError,
    extract_masks,
)

app = FastAPI(title="DiasAvto Certificate Validator", docs_url=None, redoc_url=None)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


async def _process_upload(
    file: UploadFile = File(...),
    certificate: UploadFile | None = File(default=None),
    user_id: str = Depends(require_user),
) -> list[ValidationResult]:
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
    allowed_masks = None
    if certificate is not None:
        certificate_content = await certificate.read(MAX_CERTIFICATE_BYTES + 1)
        await certificate.close()
        try:
            allowed_masks = extract_masks(certificate_content, certificate.filename or "")
        except CertificateFormatError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    return validate_catalog(catalog, allowed_masks)


@app.post("/api/preview")
async def preview(
    file: UploadFile = File(...),
    certificate: UploadFile | None = File(default=None),
    user_id: str = Depends(require_user),
) -> JSONResponse:
    results = await _process_upload(file, certificate, user_id)
    exceptions = [
        {
            "article": result.item.article,
            "manufacturer": result.item.manufacturer,
            "product_group": result.item.product_group,
            "search_key": result.search_key,
            "reason": result.rejection_reason.value,
        }
        for result in results
        if result.rejection_reason is not None
    ]
    return JSONResponse(
        {
            "total": len(results),
            "accepted": len(results) - len(exceptions),
            "rejected": len(exceptions),
            "exceptions": exceptions,
        },
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


@app.post("/api/validate", response_class=StreamingResponse)
async def validate(
    file: UploadFile = File(...),
    certificate: UploadFile | None = File(default=None),
    user_id: str = Depends(require_user),
) -> StreamingResponse:
    results = await _process_upload(file, certificate, user_id)
    report = create_report(results)
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


@app.post("/api/generation/plan")
async def generation_plan(
    certificate: UploadFile = File(...),
    user_id: str = Depends(require_user),
) -> JSONResponse:
    """Предварительный расчёт объёма выгрузки без генерации миллионов строк."""
    if not certificate.filename:
        raise HTTPException(status_code=400, detail="Не указано имя сертификата")
    suffix = certificate.filename.lower().rsplit(".", 1)[-1]
    limit = MAX_PDF_BYTES if suffix == "pdf" else MAX_CERTIFICATE_BYTES
    payload = await certificate.read(limit + 1)
    await certificate.close()
    try:
        if suffix == "pdf":
            masks = extract_pdf_masks(payload)
        else:
            masks = extract_masks(payload, certificate.filename)
    except (PdfCertificateError, CertificateFormatError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return JSONResponse(
        {"masks": masks, "mask_count": len(masks)},
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


class ArticleCheckRequest(BaseModel):
    supplier: str = "hi-lex"
    article: str = Field(min_length=1, max_length=128)
    masks: list[str] = Field(min_length=1, max_length=100)


@app.post("/api/rules/check")
def check_article(
    request: ArticleCheckRequest,
    user_id: str = Depends(require_user),
) -> JSONResponse:
    try:
        rules = supplier_rules(request.supplier)
        matched = rules.matches(request.article, tuple(request.masks))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return JSONResponse(
        {"matches": matched, "supplier": rules.code, "rules_version": rules.version},
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )
