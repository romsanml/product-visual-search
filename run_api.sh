#!/usr/bin/env bash
export APP_DB_URL="sqlite:///data/app.db"
export APP_STORAGE_ROOT="data/images"
export APP_FAISS_INDEX_PATH="data/faiss.index"
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
