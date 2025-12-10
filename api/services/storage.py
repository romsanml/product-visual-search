from typing import Tuple, Optional
import os

class Storage:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    def read_product_image(self, product_id: str, filename: Optional[str] = None) -> Tuple[str, str]:

        product_id = os.path.basename(str(product_id))  # защита от путей
        if filename:
            ext_candidates = [os.path.splitext(filename)[1].lower() or ".jpg"]
        else:
            ext_candidates = [".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff"]

        for ext in ext_candidates:
            rel_path = f"{product_id}{ext}"
            abs_path = os.path.join(self.root_dir, rel_path)
            if os.path.isfile(abs_path):
                return rel_path, abs_path

        raise FileNotFoundError(f"Image for product {product_id} not found in {self.root_dir}")
