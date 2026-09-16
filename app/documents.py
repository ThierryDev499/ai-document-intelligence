from io import BytesIO

from fastapi import HTTPException
from pypdf import PdfReader


def extract(data: bytes):
    if not data.startswith(b'%PDF-'):
        raise HTTPException(422, 'O arquivo nao possui uma assinatura PDF valida.')
    try:
        reader = PdfReader(BytesIO(data))
        if reader.is_encrypted:
            raise HTTPException(422, 'PDF protegido por senha nao e suportado.')
        if not 1 <= len(reader.pages) <= 50:
            raise HTTPException(422, 'Envie um PDF com 1 a 50 paginas.')
        pages = [page.extract_text() or '' for page in reader.pages]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(422, 'Nao foi possivel ler este PDF.') from exc
    if not any(p.strip() for p in pages):
        raise HTTPException(422, 'PDF sem camada de texto. OCR nao esta incluido nesta versao.')
    if sum(map(len, pages)) > 100_000:
        raise HTTPException(422, 'Limite de 100 mil caracteres excedido.')
    chunks = []
    for page, text in enumerate(pages, 1):
        text = ' '.join(text.split())
        for start in range(0, len(text), 750):
            fragment = text[start:start + 900]
            if fragment.strip():
                chunks.append({'page': page, 'text': fragment})
            if start + 900 >= len(text):
                break
    return pages, chunks
