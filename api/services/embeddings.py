import numpy as np
import torch
import torch.nn.functional as F
from io import BytesIO
from PIL import Image
from transformers import CLIPProcessor, CLIPModel

class ImageEmbedder:

    def __init__(self, device: str = "cpu"):
        
        self.device = torch.device(device)
        self.model_name = "openai/clip-vit-base-patch32"
        self.model = CLIPModel.from_pretrained(self.model_name)
        self.model.to(self.device)
        self.model.eval()
        self.processor = CLIPProcessor.from_pretrained(self.model_name, use_fast=True)
        self.feature_extractor = self.model.get_image_features
        self.dim = 512 # Размер эмбеддинга для clip-vit-base-patch32

    @torch.no_grad()
    def embed_image(self, abs_path: str) -> np.ndarray:
        img = Image.open(abs_path).convert("RGB")
        inputs = self.processor(
            images=img,
            return_tensors="pt",  # Чтобы вернулся тензор, а не list
        )["pixel_values"]  # Это уже torch.Tensor [1, C, H, W]
        inputs = inputs.to(self.device)
        feats = self.feature_extractor(pixel_values=inputs)
        feats = F.normalize(feats, p=2, dim=1)  # L2 нормализация
        return feats.cpu().numpy().astype("float32")[0]

    @torch.no_grad()
    def embed_bytes(self, data: bytes) -> np.ndarray:
        img = Image.open(BytesIO(data)).convert("RGB")
        inputs = self.processor(
            images=img,
            return_tensors="pt",  # Чтобы вернулся тензор, а не list
        )["pixel_values"]  # Это уже torch.Tensor [1, C, H, W]
        inputs = inputs.to(self.device)
        feats = self.feature_extractor(pixel_values=inputs)
        feats = F.normalize(feats, p=2, dim=1)  # L2 нормализация
        return feats.cpu().numpy().astype("float32")[0]

    @torch.no_grad()
    def embed_text(self, text: str) -> np.ndarray:
        inputs = self.processor(
            text=[text],
            return_tensors="pt",
            padding=True,
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        text_feats = self.model.get_text_features(**inputs)
        text_feats = F.normalize(text_feats, p=2, dim=1)  # L2 нормализация
        return text_feats.cpu().numpy().astype("float32")[0]
