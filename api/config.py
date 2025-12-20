import torch
from pydantic import BaseModel


class Settings(BaseModel):
    api_host: str = "0.0.0.0"
    api_port: int = 8008
    db_url: str = "sqlite:///data/app.db"
    storage_root: str = "data/images"
    faiss_index_path: str = "data/faiss.index"
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    top_k: int = 10

    class Config:
        env_prefix = "APP_"
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
