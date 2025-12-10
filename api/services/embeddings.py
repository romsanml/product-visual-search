import numpy as np
import torch
from io import BytesIO
from PIL import Image
from typing import Callable
from transformers import CLIPProcessor, CLIPModel

class ImageEmbedder:

    def __init__(self, device: str = "cpu"):
        
        self.device = torch.device(device)
        self.model_name = "openai/clip-vit-base-patch32"
        self.model = CLIPModel.from_pretrained(self.model_name)
        self.model.to(self.device)
        self.model.eval()  # <-- Правильное место для .eval()
        self.processor = CLIPProcessor.from_pretrained(self.model_name)
        self.feature_extractor = self.model.get_image_features
        self.tf: Callable[[Image.Image], torch.Tensor] = lambda img: self.processor(
            images=img,
            return_tensors="pt"
        )["pixel_values"]
        self.dim = 512 # Размер эмбеддинга для clip-vit-base-patch32

    @torch.no_grad()
    def embed_image(self, abs_path: str) -> np.ndarray:
        img = Image.open(abs_path).convert("RGB")
        inputs = self.tf(img).to(self.device)
        feats = self.feature_extractor(pixel_values=inputs)
        feats = torch.nn.functional.normalize(feats, p=2, dim=1)  # L2 нормализация
        return feats.cpu().numpy().astype("float32")[0]

    @torch.no_grad()
    def embed_bytes(self, data: bytes) -> np.ndarray:
        img = Image.open(BytesIO(data)).convert("RGB")
        inputs = self.tf(img).to(self.device)
        feats = self.feature_extractor(pixel_values=inputs)
        feats = torch.nn.functional.normalize(feats, p=2, dim=1)  # L2 нормализация
        return feats.cpu().numpy().astype("float32")[0]
