import torch
from typing import List, Dict, Any
from io import BytesIO
from PIL import Image
from transformers import GroundingDinoProcessor, GroundingDinoForObjectDetection

class GroundingDINOSearcher:

    def __init__(self, device: str = "cpu"):

        self.device = torch.device(device)
        self.model_id = "IDEA-Research/grounding-dino-base"
        self.box_threshold = float(0.30)
        self.text_threshold = float(0.25)
        self.processor = GroundingDinoProcessor.from_pretrained(self.model_id)
        self.model = GroundingDinoForObjectDetection.from_pretrained(self.model_id)
        self.model.to(self.device)
        self.model.eval()

    @torch.inference_mode()
    def detect(
            self,
            data: bytes,
            prompt: str,
        ) -> List[Dict[str, Any]]:

        image = Image.open(BytesIO(data)).convert("RGB")

        inputs = self.processor(images=image, text=prompt, return_tensors="pt")
        inputs = {k: v.to(self.device) if hasattr(v, "to") else v for k, v in inputs.items()}

        outputs = self.model(**inputs)

        # Подготовка размеров для постпроцесса (h, w)
        w, h = image.size
        target_sizes = [(h, w)] # torch.tensor([[h, w]], device=self.device)

        results = self.processor.post_process_grounded_object_detection(
            outputs=outputs,
            input_ids=inputs["input_ids"],
            threshold=self.box_threshold,
            text_threshold=self.text_threshold,
            target_sizes=target_sizes
        )[0]

        boxes = results["boxes"]  # (N, 4) xyxy в пикселях
        scores = results["scores"]  # (N,)
        labels = results["labels"]  # список строк с фразами

        out: List[Dict[str, Any]] = []
        for box, score, label in zip(boxes, scores, labels):
            x1, y1, x2, y2 = [float(v) for v in box.tolist()]
            out.append({
                "box": [int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2))],
                "score": float(score),
                "label": str(label),
            })
        return out