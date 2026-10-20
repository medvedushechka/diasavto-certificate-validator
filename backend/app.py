from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from auth import require_user
from diasavto_validator.certificates import (
    MAX_CERTIFICATE_BYTES,
    CertificateFormatError,
    extract_masks,
)
from diasavto_validator.pdf_certificates import MAX_PDF_BYTES, PdfCertificateError, extract_pdf_masks
from diasavto_validator.rule_registry import supplier_rules

app = FastAPI(title="DiasAvto Certificate Validator", docs_url=None, redoc_url=None)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/rules/hi-lex")
def approved_hi_lex_masks(user_id: str = Depends(require_user)) -> JSONResponse:
    rules = supplier_rules("hi-lex")
    return JSONResponse(
        {
            "supplier": rules.code,
            "version": rules.version,
            "masks": sorted(rules.masks),
            "count": len(rules.masks),
        },
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


async def _certificate_masks(certificate: UploadFile) -> tuple[str, ...]:
    if not certificate.filename:
        raise HTTPException(status_code=400, detail="Не указано имя сертификата")
    suffix = certificate.filename.lower().rsplit(".", 1)[-1]
    limit = MAX_PDF_BYTES if suffix == "pdf" else MAX_CERTIFICATE_BYTES
    payload = await certificate.read(limit + 1)
    await certificate.close()
    try:
        if suffix == "pdf":
            return extract_pdf_masks(payload)
        return extract_masks(payload, certificate.filename)
    except (PdfCertificateError, CertificateFormatError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/generation/plan")
async def generation_plan(
    certificate: UploadFile = File(...),
    user_id: str = Depends(require_user),
) -> JSONResponse:
    """Извлечь разрешённые маски сертификата без генерации артикулов."""
    masks = await _certificate_masks(certificate)
    return JSONResponse(
        {"masks": masks, "mask_count": len(masks)},
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


@app.post("/api/rules/check")
async def check_article(
    article: str = Form(min_length=1, max_length=128),
    certificate: UploadFile = File(...),
    user_id: str = Depends(require_user),
) -> JSONResponse:
    # Маски определяются сервером из сертификата, а не передаются клиентом.
    masks = await _certificate_masks(certificate)
    rules = supplier_rules("hi-lex")
    matched = rules.matches(article, masks)
    return JSONResponse(
        {"matches": matched, "supplier": rules.code, "rules_version": rules.version},
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )
