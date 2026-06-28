import streamlit as st
import mimetypes
import random
import tempfile
from streamlit_mic_recorder import mic_recorder
from pathlib import Path
from io import BytesIO
from PIL import Image
from ui.api_client import post_file, post_photo, get_json
from ui.modules.voice_input import load_asr, clear_text, append_text, get_asr_result

st.set_page_config(layout="wide")
st.title("🔎 Поиск")

tab1, tab2, tab3 = st.tabs(["По изображению", "По фото", "По тексту"])

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
            # Передаём top_k в запрос
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
    # Загрузка своего изображения
    photo = st.file_uploader("Загрузите фото", type=["jpg", "jpeg", "png", "webp"])

    # Проверяем, изменилось ли фото
    if 'current_photo_name' not in st.session_state:
        st.session_state.current_photo_name = None
        st.session_state.cropped_images = {}  # Инициализируем один раз

    if photo is not None:
        # Если выбрано новое фото — сбрасываем кэш вырезанных фрагментов
        if st.session_state.current_photo_name != photo.name:
            st.session_state.cropped_images = {}  # Очищаем кэш
            st.session_state.current_photo_name = photo.name

        st.image(photo, caption=photo.name, width='content')
        st.divider()

        data_photo = photo.getvalue()
        photo_tuple = (photo.name, data_photo, photo.type or "application/octet-stream")
        res = post_photo("/search/by-photo/", photo_tuple)
        results_boxes = res.get("results", [])

        # Открываем изображение
        image = Image.open(BytesIO(data_photo)).convert("RGB")

        # Параметры
        cols_5 = 5
        max_display=5
        padding_percent=0.2

        # Уникальный ключ для изображения
        cache_key = hash(data_photo)  # Лучше использовать hash байтов — гарантирует уникальность

        if cache_key not in st.session_state.cropped_images:
            cropped_list = []
            img_w, img_h = image.size
            for item in results_boxes:
                try:
                    box = item["box"]
                    label = item["label"]
                    score = item["score"]
                    
                    # Проверяем формат box: [x1, y1, x2, y2]
                    if len(box) != 4:
                        continue
                    x1, y1, x2, y2 = map(int, box)
                    
                    # Размеры текущего бокса
                    width = x2 - x1
                    height = y2 - y1
                    
                    # Вычисляем отступы (10% от ширины/высоты бокса)
                    pad_x = int(width * padding_percent)
                    pad_y = int(height * padding_percent)
                    
                    # Новые координаты с отступами
                    new_x1 = max(0, x1 - pad_x)
                    new_y1 = max(0, y1 - pad_y)
                    new_x2 = min(img_w, x2 + pad_x)
                    new_y2 = min(img_h, y2 + pad_y)
                    
                    # Обрезаем изображение с учётом отступов
                    cropped = image.crop((new_x1, new_y1, new_x2, new_y2))
                    cropped_list.append({
                        "image": cropped,
                        "label": label,
                        "score": score
                    })
                except (KeyError, ValueError, IndexError) as e:
                    st.warning(f"Пропущен бокс из-за ошибки: {e}")
                    continue
            
            st.session_state.cropped_images[cache_key] = cropped_list

        # Берём не более max_display первых
        displayed_items = st.session_state.cropped_images[cache_key][:max_display]

        # Отображаем по 5 в строке
        for i in range(0, len(displayed_items), cols_5):
            cols_container = st.columns(cols_5)
            for j in range(cols_5):
                idx = i + j
                if idx >= len(displayed_items):
                    break
                with cols_container[j]:
                    item = displayed_items[idx]
                    st.image(item["image"], caption=f"{item['label']}: {item['score']:.2f}", width='stretch')

        # Выбор одного из примеров
        if st.session_state.cropped_images:
            cache_key = next(iter(st.session_state.cropped_images))
            cropped_list = st.session_state.cropped_images[cache_key][:max_display]
        else:
            cropped_list = []

        if cropped_list:
            # Создаём список опций: "метка (score)"
            label_options = [f"{item['label']}: {item['score']:.2f}" for item in cropped_list]
            label_options = ["— Не выбран —"] + label_options

            # Выпадающий список для выбора фрагмента по метке
            selected_label = st.selectbox("Выберите вырезанный фрагмент по метке", label_options, index=0)

            if selected_label != "— Не выбран —":
                # Находим индекс выбранного элемента
                idx = label_options.index(selected_label) - 1
                chosen_item = cropped_list[idx]
                st.info(f"Выбран фрагмент: {chosen_item['label']}: {chosen_item['score']:.2f}")
                
                # Преобразуем PIL в байты
                img = chosen_item["image"]
                format = img.format or "PNG"
                img_byte_arr = BytesIO()
                img.save(img_byte_arr, format=format)
                img_byte_arr.seek(0)
                data = img_byte_arr.read()

        top_n = st.slider("Top-N", 1, 50, 10)

        if st.button("Искать предмет"):
            file_tuple = None

            if 'data' in locals() and data:
                file_tuple = (chosen_item['label'], data, format or "application/octet-stream")
            else:
                st.warning("Загрузите фото для поиска.")

            if file_tuple:
                # Передаём top_n в запрос
                res = post_file(f"/search/by-image?top_k={top_n}", file_tuple)
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

with tab3:
    if "text_input_3" not in st.session_state:
        st.session_state.text_input_3 = ""
    if "voice_input" not in st.session_state:
        st.session_state.voice_input = ""
    if "_last_asr_result" not in st.session_state:
        st.session_state._last_asr_result = ""
    if "_last_audio_sig" not in st.session_state:
        st.session_state._last_audio_sig = None
    if "_clear_audio_after" not in st.session_state:
        st.session_state._clear_audio_after = False

    col1, col2, col3 = st.columns([1, 8, 1], vertical_alignment="bottom")

    with col1:
        st.write("Голосовой ввод")
        asr = load_asr()
        audio = mic_recorder(
            start_prompt="🎙️ Записать",
            stop_prompt="⏹️ Остановить",
            key="rec",
            args=(),
            kwargs={}
        )

        if isinstance(audio, dict) and "bytes" in audio:
            audio_bytes = audio["bytes"]
            audio_sig = len(audio_bytes)

            if st.session_state._clear_audio_after:
                st.session_state._clear_audio_after = False
                st.session_state._last_audio_sig = audio_sig
            elif audio_sig != st.session_state._last_audio_sig:
                text = get_asr_result(asr, audio_bytes)
                st.session_state._last_audio_sig = audio_sig
                append_text(text)

    with col2:
        q = st.text_input("Текстовый ввод", key="text_input_3")

    with col3:
        st.button("Очистить", on_click=clear_text)

    limit = st.slider("Лимит результатов", 1, 50, 10)

    if q and st.button("Искать по тексту"):
        res = get_json(f"/search/by-text?limit={limit}", q=q)
        for r in res.get("results", []):
            cols = st.columns([1, 3])
            with cols[0]:
                if r["url"]:
                    st.image(f".{r['url']}", width=150)
            with cols[1]:
                st.write(f"{r['product_id']}: {r['title']}")
                st.caption(r["description"])