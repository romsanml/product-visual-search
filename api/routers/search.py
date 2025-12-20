from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Dict, Optional, List
from api.db import SessionLocal
from api.models.orm import ProductImage, Product
from api.dependencies import get_embedder, get_vdb, get_searcher
from api.config import settings


router = APIRouter(prefix="/search", tags=["search"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def to_out(img: ProductImage, score: float, product: Optional[Product] = None) -> Dict:
    out = {
        "image_id": img.image_id,
        "product_id": img.product_id,
        "url": f"/data/images/{img.rel_path}",
        "score": float(score),
    }
    if product:
        out.update({
            "title": product.title,
            "rating": product.rating,
            "description": product.description,
        })
    return out


@router.post("/by-image")
def search_by_image(
        file: UploadFile = File(...),
        top_k: int = settings.top_k,
        embedder=Depends(get_embedder),
        vdb=Depends(get_vdb),
        db: Session = Depends(get_db),
    ):
    data = file.file.read()
    vec = embedder.embed_bytes(data)
    ids, scores = vdb.search(vec, top_k=top_k)
    if not ids:
        return {"results": []}

    imgs = db.execute(select(ProductImage).where(ProductImage.image_id.in_(ids))).scalars().all()
    img_by_id = {im.image_id: im for im in imgs}
    # Получаем все уникальные product_id из найденных картинок
    product_ids = list(im.product_id for im in imgs)
    products = db.execute(select(Product).where(Product.product_id.in_(product_ids))).scalars().all()
    product_by_id = {p.product_id: p for p in products}
    results = [
        to_out(img_by_id[i], s, product_by_id.get(img_by_id[i].product_id))
        for i, s in zip(ids, scores) if i in img_by_id
    ]
    return {"results": results}


def build_prompt(phrases: List[str]) -> str:
    # Для GroundingDINO фразы лучше разделять точкой и пробелом
    return " . ".join(phrases) + " ."


@router.post("/by-photo")
def search_by_photo(
    photo: UploadFile = File(...),
    searcher=Depends(get_searcher),
    DEFAULT_PROMPT_PHRASES: List[str] = settings.DEFAULT_PROMPT_PHRASES,
):
    data = photo.file.read()
    prompt = build_prompt(DEFAULT_PROMPT_PHRASES)
    results = searcher.detect(data=data, prompt=prompt) # список {box, score, label}
    return {"results": results}


# @router.get("/by-text")
# def search_by_text(q: str, limit: int = 20, db: Session = Depends(get_db)):
#     # Простой текстовый поиск по title/description
#     stmt = f"%{q}%"
#     rows = db.execute(
#         select(Product).where((Product.title.ilike(stmt)) | (Product.description.ilike(stmt))).limit(limit)
#     ).scalars().all()

#     out = []
#     for p in rows:
#         url = f"/static/images/{p.images[0].rel_path}" if p.images else None
#         out.append({
#             "product_id": p.id,
#             "title": p.title,
#             "rating": p.rating,
#             "description": p.description,
#             "preview_url": url,
#         })
#     return {"results": out}
