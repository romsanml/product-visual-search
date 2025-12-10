import requests
from .config import API_BASE

def get_json(path: str, **params):
    r = requests.get(f"{API_BASE}{path}", params=params, timeout=60)
    r.raise_for_status()
    return r.json()

def post_json(path: str, payload: dict):
    r = requests.post(f"{API_BASE}{path}", json=payload, timeout=60)
    r.raise_for_status()
    return r.json()

def post_file(path: str, file_tuple):
    r = requests.post(f"{API_BASE}{path}", files={"file": file_tuple}, timeout=120)
    r.raise_for_status()
    return r.json()
