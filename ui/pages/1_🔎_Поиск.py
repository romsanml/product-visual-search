import streamlit as st
import mimetypes
import random
from pathlib import Path
from ui.api_client import post_file

st.set_page_config(layout="wide")
st.title("🔎 Поиск")

tab1, tab2 = st.tabs(["По изображению", "По фото"])

with tab1:
    # Инициализация session state для хранения примеров
    if 'example_paths' not in st.session_state:
        base_dir = Path("./ui/pages")
        ex_dir = base_dir / "images2search"
        example_paths = []
        if ex_dir.exists():
            all_images = [p for p in ex_dir.glob("*") if p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]]
            random.shuffle(all_images)
            if len(all_images) >= 5:
                example_paths.extend(all_images[:5])
            else:
                example_paths.extend(all_images)
        st.session_state.example_paths = example_paths

    # Используем сохранённые пути
    example_paths = st.session_state.example_paths

    # Отображаем изображения, например:
    if example_paths:
        st.subheader("Выберите один из примеров")
        cols = st.columns(len(example_paths))
        for col, img_path in zip(cols, example_paths):
            col.image(str(img_path), caption=img_path.name, width='stretch')

        # Выбор одного из примеров
        ex_options = ["— Не выбран —"] + [p.name for p in example_paths]
        ex_choice = st.selectbox("Примеры", ex_options, index=0)
        chosen_example = None
        if ex_choice != "— Не выбран —":
            idx = ex_options.index(ex_choice) - 1
            chosen_example = example_paths[idx]
            st.info(f"Выбран пример: {chosen_example.name}")
    else:
        st.warning("Папка с изображениями не найдена или пуста. Добавьте до 5 изображений (.jpg/.jpeg/.png/.webp).")
        chosen_example = None

    # Загрузка своего изображения
    img = st.file_uploader("Загрузите изображение", type=["jpg", "jpeg", "png", "webp"])

    top_k = st.slider("Top-K", 1, 50, 10)

    if st.button("Искать"):
        file_tuple = None

        if img is not None:
            data = img.getvalue()
            file_tuple = (img.name, data, img.type or "application/octet-stream")
        elif chosen_example is not None:
            data = chosen_example.read_bytes()
            mime = mimetypes.guess_type(chosen_example.name)[0] or "image/jpeg"
            file_tuple = (chosen_example.name, data, mime)
        else:
            st.warning("Выберите пример или загрузите изображение для поиска.")

        if file_tuple:
            # Передаём top_k в query
            res = post_file(f"/search/by-image?top_k={top_k}", file_tuple)
            results = res.get("results", [])
            if not results:
                st.info("Ничего не найдено.")
            for r in results:
                cols = st.columns([1, 1, 4])
                with cols[0]:
                    st.image(f".{r['url']}", width='stretch')
                with cols[1]:
                    st.write(f"product_id: {r['product_id']}")
                    st.write(f"image_id: {r['image_id']}")
                    st.write(f"score: {r['score']:.4f}")
                    st.write(f"title: {r['title']}")
                    st.write(f"rating: {r['rating']:.1f}")
                with cols[2]:
                    st.write(f"description: {r['description']}")


# with tab2:
#     q = st.text_input("Текстовый запрос")
#     if q and st.button("Искать по тексту"):
#         res = get_json("/search/by-text", q=q)
#         for r in res.get("results", []):
#             cols = st.columns([1, 3])
#             with cols[0]:
#                 if r["preview_url"]:
#                     st.image(f".{r['preview_url']}", width=150)
#             with cols[1]:
#                 st.write(f"{r['product_id']}: {r['title']}")
#                 st.caption(r["description"])
