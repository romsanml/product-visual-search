import os
import pandas as pd
import streamlit as st
from ui.api_client import post_json, post_file


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_CSV = os.path.join(PROJECT_ROOT, "data", "products.csv")
DEFAULT_IMAGES = os.path.join(PROJECT_ROOT, "data", "images")

st.set_page_config(layout="wide")
st.title("📦 Товары")

with st.expander("Создать/обновить товар (вручную)"):
    pid = st.text_input("product_id")
    category = st.text_input("category_id")
    title = st.text_input("title")
    rating = st.number_input("rating")
    description = st.text_area("description")
    if pid and st.button("Сохранить"):
        payload = {
            "product_id": pid,
            "category_id": category,
            "title": title,
            "rating": rating,
            "description": description
        }
        st.json(post_json("/products", payload))

with st.expander("Пакетная загрузка из CSV и папки с изображениями"):
    st.write("Укажите путь к CSV и к папке с изображениями. Имена файлов изображений соответствуют колонке product_id (например, 123.jpg).")

    csv_path = st.text_input(
        "Путь к CSV со списком товаров",
        value=DEFAULT_CSV,
        help="Ожидаемые колонки: product_id, category_id, title, description"
    )

    images_dir = st.text_input(
        "Путь к папке с изображениями",
        value=DEFAULT_IMAGES,
        help="Файлы: product_id.jpg|jpeg|png|webp"
    )

    st.caption(f"CSV: {csv_path}")
    st.caption(f"Папка с изображениями: {images_dir}")

    allowed_exts = [".jpg", ".jpeg", ".png", ".webp"]

    if st.button("Загрузить товары из CSV"):
        # Проверки путей
        if not os.path.isfile(csv_path):
            st.error(f"CSV не найден: {csv_path}")
        else:
            if not os.path.isdir(images_dir):
                st.warning(f"Папка с изображениями не найдена или недоступна: {images_dir}")

            # Чтение CSV
            try:
                df = pd.read_csv(csv_path)
            except Exception as e:
                st.exception(e)
                df = None

            if df is not None:
                if "product_id" not in df.columns:
                    st.error("В CSV отсутствует обязательная колонка 'product_id'")
                else:
                    total = len(df)
                    progress = st.progress(0.0)
                    ok_products = 0
                    ok_images = 0

                    # Итерация по строкам
                    for i, row in enumerate(df.itertuples(index=False)):  # index=False — проще работать
                        # Извлекаем product_id и приводим к строке
                        product_id = str(getattr(row, "product_id", "")).strip()
                        if not product_id:
                            st.warning(f"[{i+1}] Пропущена строка: пустой product_id")
                            continue

                        payload = {
                            "product_id": product_id,
                            "category_id": str(getattr(row, "category_id", "")).strip() or None,
                            "title": str(getattr(row, "shop_title", "")).strip() or None,
                            "rating": str(getattr(row, "rating", "")).strip() or None,
                            "description": str(getattr(row, "description", "")).strip() or None,
                        }

                        # Создание/обновление товара
                        try:
                            post_json("/products", payload)
                            ok_products += 1
                        except Exception as e:
                            st.warning(f"[{product_id}] Ошибка при сохранении товара: {e}")

                        # Поиск и загрузка изображения по product_id.*
                        image_path = None
                        for ext in allowed_exts:
                            candidate = os.path.join(images_dir, f"{product_id}{ext}")
                            if os.path.isfile(candidate):
                                image_path = candidate
                                break

                        if image_path:
                            try:
                                with open(image_path, "rb") as f:
                                    data = f.read()
                                filename = os.path.basename(image_path)
                                ext = os.path.splitext(filename)[1].lower()
                                mime_types = {
                                    ".jpg": "image/jpeg",
                                    ".jpeg": "image/jpeg",
                                    ".png": "image/png",
                                    ".webp": "image/webp"
                                }
                                mime = mime_types.get(ext, "application/octet-stream")

                                post_file(f"/products/{product_id}/images", (filename, data, mime))
                                ok_images += 1
                            except Exception as e:
                                st.warning(f"[{product_id}] Не удалось загрузить изображение {image_path}: {e}")

                        progress.progress((i + 1) / max(total, 1))

                    st.success(f"Готово: товаров сохранено {ok_products} из {total}, изображений прикреплено {ok_images}")
