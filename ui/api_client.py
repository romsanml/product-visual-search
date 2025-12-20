import requests
from ui.config import API_BASE


def post_file(endpoint: str, file_tuple):
    """
    Отправляет файл на API как multipart/form-data.
    
    :param endpoint: URL-путь, например "/search/by-image?top_k=10"
    :param file_tuple: Кортеж (filename, file_data, content_type), как в Streamlit
    :return: JSON-ответ от сервера или {"error": "..."}
    """
    url = API_BASE + endpoint
    files = {
        "file": file_tuple  # FastAPI ожидает параметр типа UploadFile с именем "file"
    }
    try:
        response = requests.post(url, files=files, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"HTTP {response.status_code}",
                "message": response.text,
                "results": []
            }
    except requests.exceptions.Timeout:
        return {"error": "Таймаут соединения с сервером", "results": []}
    except requests.exceptions.ConnectionError:
        return {"error": "Не удалось подключиться к серверу", "results": []}
    except Exception as e:
        return {"error": f"Ошибка: {str(e)}", "results": []}


def post_photo(endpoint: str, photo_tuple):
    """
    Аналогично post_file, но для фото (если используется отдельно).
    Можно объединить с post_file, но оставим отдельно для ясности.
    """
    url = API_BASE + endpoint
    files = {
        "photo": photo_tuple  # Предполагается, что endpoint ожидает поле `photo`
    }
    try:
        response = requests.post(url, files=files, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"HTTP {response.status_code}",
                "message": response.text,
                "results": []
            }
    except requests.exceptions.Timeout:
        return {"error": "Таймаут при обработке фото", "results": []}
    except requests.exceptions.ConnectionError:
        return {"error": "Нет соединения с сервером", "results": []}
    except Exception as e:
        return {"error": f"Ошибка: {str(e)}", "results": []}
