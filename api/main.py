import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .config import settings
from .db import engine
from .models.orm import Base
from .routers import health, products, search
import uvicorn

def create_app() -> FastAPI:

    app = FastAPI(title="Product API", version="1.0.0")

    # Создать таблицы
    Base.metadata.create_all(bind=engine)

    # Маршруты
    app.include_router(health.router)
    app.include_router(products.router)
    app.include_router(search.router)

    # Статика для изображений
    os.makedirs(settings.storage_root, exist_ok=True)
    app.mount("/static/images", StaticFiles(directory=settings.storage_root), name="images")

    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("api.main:app", host=settings.api_host, port=settings.api_port, reload=True)
