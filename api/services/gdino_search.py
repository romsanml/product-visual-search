import torch
from typing import List, Dict, Any
from io import BytesIO
from PIL import Image
# import numpy as np
from transformers import GroundingDinoProcessor, GroundingDinoForObjectDetection
# from transformers import SamModel, SamProcessor


class GroundingDINOSearcher:

    def __init__(self, device: str = "cpu"):

        self.device = torch.device(device)
        self.box_threshold = float(0.05)
        self.text_threshold = float(0.05)
        self.score_threshold = float(0.15)

        # Загрузка Grounding DINO
        self.model_id = "IDEA-Research/grounding-dino-base"
        self.processor = GroundingDinoProcessor.from_pretrained(self.model_id)
        self.model = GroundingDinoForObjectDetection.from_pretrained(self.model_id)
        self.model.to(self.device)
        self.model.eval()

        # # Загрузка SAM
        # self.sam_model_id = "facebook/sam-vit-huge"
        # self.sam_processor = SamProcessor.from_pretrained(self.sam_model_id)
        # self.sam_model = SamModel.from_pretrained(self.sam_model_id)
        # self.sam_model.to(self.device)
        # self.sam_model.eval()

    @torch.inference_mode()
    def detect(
            self,
            data: bytes,
            prompt: str,
        ) -> List[Dict[str, Any]]:
        """Обнаружение объектов по текстовому запросу."""
        image = Image.open(BytesIO(data)).convert("RGB")

        inputs = self.processor(images=image, text=prompt, return_tensors="pt")
        inputs = {k: v.to(self.device) if hasattr(v, "to") else v for k, v in inputs.items()}

        outputs = self.model(**inputs)

        w, h = image.size
        target_sizes = [(h, w)]

        results = self.processor.post_process_grounded_object_detection(
            outputs=outputs,
            input_ids=inputs["input_ids"],
            threshold=self.box_threshold,
            text_threshold=self.text_threshold,
            target_sizes=target_sizes
        )[0]

        boxes = results["boxes"]
        scores = results["scores"]
        labels = results["text_labels"]

        out: List[Dict[str, Any]] = []
        for box, score, label in zip(boxes, scores, labels):
            x1, y1, x2, y2 = [float(v) for v in box.tolist()]
            if score >= self.score_threshold:
                out.append({
                    "box": [int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2))],
                    "score": float(score),
                    "label": str(label),
                })
        return out

    # @torch.inference_mode()
    # def remove_background_in_box(self, image, box_xyxy, limit_to_box=True, invert=False):
    #     """
    #     image: путь к файлу, PIL.Image или np.ndarray (H,W,3)
    #     box_xyxy: [x1, y1, x2, y2] в пикселях относительно исходного изображения
    #     limit_to_box: если True — маска обрезается по рамке (вне бокса прозрачность = 0)
    #     invert: если True — инвертировать маску (убрать объект, оставить фон)
    #     return: PIL.Image RGBA
    #     """
    #     # 1) Прочитать изображение как PIL RGB
    #     if isinstance(image, str):
    #         pil_img = Image.open(image).convert("RGB")
    #     elif isinstance(image, Image.Image):
    #         pil_img = image.convert("RGB")
    #     else:
    #         arr = np.asarray(image)
    #     if arr.ndim == 2:
    #         arr = np.stack([arr]*3, axis=-1)
    #     if arr.shape[2] == 4:
    #         arr = arr[..., :3]
    #     pil_img = Image.fromarray(arr.astype(np.uint8))

    #     w, h = pil_img.size

    #     # # 2) Клэмп координат бокса в границы изображения
    #     x1, y1, x2, y2 = map(float, box_xyxy)
    #     # x1, y1 = max(0.0, min(x1, w - 1)), max(0.0, min(y1, h - 1))
    #     # x2, y2 = max(0.0, min(x2, w)),     max(0.0, min(y2, h))
    #     # if x2 <= x1 or y2 <= y1:
    #     #     raise ValueError("Некорректный бокс: x2<=x1 или y2<=y1")

    #     # device = next(self.sam_model.parameters()).device if any(p.is_cuda for p in self.sam_model.parameters()) else (torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu"))
    #     # self.sam_model.to(device)

    #     # 3) Препроцесс и прогон SAM (одна маска на бокс)
    #     inputs = self.sam_processor(
    #         pil_img,
    #         input_boxes=[[[x1, y1, x2, y2]]],   # список боксов для одного изображения
    #         return_tensors="pt"
    #     ).to(self.device)

    #     outputs = self.sam_model(**inputs, multimask_output=False)
    #     # 4) Маска к исходному размеру
    #     masks = self.sam_processor.post_process_masks(
    #         outputs.pred_masks,               # [B, num_masks, 256, 256]
    #         inputs["original_sizes"],         # [(H_orig, W_orig)]
    #         inputs["reshaped_input_sizes"],   # [(H_in,   W_in)]
    #     )[0]  # -> [num_masks, H, W]
    #     mask = masks[0].clamp(0, 1).cpu().numpy()  # [H, W], float32 0..1

    #     # 5) Ограничить маску рамкой при необходимости
    #     if limit_to_box:
    #         box_mask = np.zeros((h, w), dtype=bool)
    #         box_mask[int(y1):int(y2), int(x1):int(x2)] = True
    #         mask = np.logical_and(mask > 0.0, box_mask)
    #     else:
    #         mask = mask > 0.0

    #     if invert:
    #         mask = ~mask

    #     # 6) Собрать RGBA
    #     rgb = np.array(pil_img)
    #     alpha = (mask.astype(np.uint8) * 255)
    #     rgba = np.dstack([rgb, alpha])
    #     return Image.fromarray(rgba, mode="RGBA")
