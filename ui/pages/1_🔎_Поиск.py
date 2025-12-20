import streamlit as st
import mimetypes
import random
from pathlib import Path
from ui.api_client import post_file, post_photo

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
    img = st.file_uploader(
        "Загрузите изображение", 
        type=["jpg", "jpeg", "png", "webp"], 
        accept_multiple_files=False,
        key="file_uploader_image"
    )
    if img:
        st.image(img, caption=img.name, width='content')
    
    top_k = st.slider("Top-K", 1, 50, 10)

    if st.button("Искать пример"):
        file_tuple = None

        if img is not None:
            # Явно определяем MIME-тип по расширению
            mime_type = mimetypes.guess_type(f"file.{img.name.split('.')[-1].lower()}")[0]
            if not mime_type:
                mime_type = "application/octet-stream"
            data = img.getvalue()
            file_tuple = (img.name, data, mime_type)
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
            errors = res.get("error", [])
            messages = res.get("message", [])
            if errors:
                st.write("Ошибки:", errors)
            if messages:
                st.write("Сообщения:", messages)
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

with tab2:
    # Инициализация session state для хранения примеров
    # if 'example_paths' not in st.session_state:
    #     base_dir = Path("./ui/pages")
    #     ex_dir = base_dir / "images2search"
    #     example_paths = []
    #     if ex_dir.exists():
    #         all_images = [p for p in ex_dir.glob("*") if p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]]
    #         random.shuffle(all_images)
    #         if len(all_images) >= 5:
    #             example_paths.extend(all_images[:5])
    #         else:
    #             example_paths.extend(all_images)
    #     st.session_state.example_paths = example_paths

    # # Используем сохранённые пути
    # example_paths = st.session_state.example_paths

    # Загрузка своего изображения
    photo = st.file_uploader("Загрузите фото", type=["jpg", "jpeg", "png", "webp"])

    if photo is not None:
        st.write("Обработка изображения")
        data_photo = photo.getvalue()
        photo_tuple = (photo.name, data_photo, photo.type or "application/octet-stream")
        res = post_photo("/search/by-photo/", photo_tuple)
        results_boxes = res.get("results", [])
        st.write(results_boxes)

    # top_n = st.slider("Top-N", 1, 50, 10)

    # if st.button("Искать предмет"):
    #     file_tuple = None

    #     if img is not None:
    #         data = img.getvalue()
    #         file_tuple = (img.name, data, img.type or "application/octet-stream")
    #     else:
    #         st.warning("Загрузите фото для поиска.")

    #     if file_tuple:
    #         # Передаём top_k в query
    #         res = post_file(f"/search/by-image?top_k={top_n}", file_tuple)
    #         results = res.get("results", [])
    #         if not results:
    #             st.info("Ничего не найдено.")
    #         for r in results:
    #             cols = st.columns([1, 1, 4])
    #             with cols[0]:
    #                 st.image(f".{r['url']}", width='stretch')
    #             with cols[1]:
    #                 st.write(f"product_id: {r['product_id']}")
    #                 st.write(f"image_id: {r['image_id']}")
    #                 st.write(f"score: {r['score']:.4f}")
    #                 st.write(f"title: {r['title']}")
    #                 st.write(f"rating: {r['rating']:.1f}")
    #             with cols[2]:
    #                 st.write(f"description: {r['description']}")


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
