from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from typing import List
from api.db import SessionLocal
from api.models.orm import Product, ProductImage
from api.models.schemas import ProductCreate, ProductOut, ProductImageOut
from api.dependencies import get_storage, get_embedder, get_vdb


router = APIRouter(prefix="/products", tags=["products"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def image_url(rel_path: str) -> str:
    return f"/data/images/{rel_path}"


@router.post("", response_model=ProductOut)
def upsert_product(payload: ProductCreate, db: Session = Depends(get_db)):
    # Загружаем продукт с изображениями
    prod = db.execute(
        select(Product)
        .where(Product.product_id == payload.product_id)
        .options(selectinload(Product.images))
    ).scalar()

    if not prod:
        prod = Product(product_id=payload.product_id)
        db.add(prod)
    # Всегда обновляем данные полей из payload, даже при создании
    prod.category_id = payload.category_id
    prod.title = payload.title
    prod.description = payload.description
    prod.rating = payload.rating

    db.commit()
    db.refresh(prod)

    # Теперь prod.images гарантированно список (или пустой)
    image_outs = [
        ProductImageOut(
            image_id=im.image_id,
            url=image_url(im.rel_path)
        )
        for im in (prod.images or [])  # защита от None
    ]

    return ProductOut(
        product_id=prod.product_id,
        category_id=prod.category_id,
        title=prod.title,
        rating=prod.rating,
        description=prod.description,
        images=image_outs
    )


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: str, db: Session = Depends(get_db)):
    prod = db.get(Product, product_id)
    if not prod:
        raise HTTPException(404, "Product not found")
    images = [
        ProductImageOut(image_id=im.image_id, url=image_url(im.rel_path))
        for im in prod.images
    ]
    return ProductOut(
        product_id=prod.product_id,
        category_id=prod.category_id,
        title=prod.title,
        rating=prod.rating,
        description=prod.description,
        images=images
    )


@router.get("", response_model=List[ProductOut])
def list_products(limit: int = 50, db: Session = Depends(get_db)):
    prods = db.execute(select(Product).limit(limit)).scalars().all()
    out: List[ProductOut] = []
    for p in prods:
        imgs = [ProductImageOut(image_id=im.image_id, url=image_url(im.rel_path)) for im in p.images]
        out.append(ProductOut(product_id=p.product_id,
                              category_id=p.category_id,
                              title=p.title,
                              rating=p.rating,
                              description=p.description,
                              images=imgs))
    return out


@router.post("/{product_id}/images", response_model=ProductImageOut)
def add_product_image(
    product_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    storage=Depends(get_storage),
    embedder=Depends(get_embedder),
    vdb=Depends(get_vdb),
):

    prod = db.get(Product, product_id)
    if not prod:
        raise HTTPException(404, "Product not found")

    rel_path, abs_path = storage.read_product_image(product_id, file.filename)

    try:
        img = ProductImage(product_id=product_id, rel_path=rel_path)
    except Exception as e:
        raise HTTPException(500, "Failed to process image")

    try:
        db.add(img)
        db.commit()
        db.refresh(img)

        vec = embedder.embed_image(abs_path)
        vdb.upsert(vec, img.image_id)
        vdb.save()

    except Exception as e:
        db.rollback()
        raise HTTPException(500, "Failed to process image")

    return ProductImageOut(image_id=img.image_id, url=image_url(rel_path))
