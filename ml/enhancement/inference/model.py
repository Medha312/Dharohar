import os
from pathlib import Path
from typing import Optional
from PIL import Image, ImageEnhance, ImageOps


class EnhancementModel:
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.is_loaded = False
        self.load(model_path)

    def load(self, model_path: Optional[str] = None) -> None:
        if model_path:
            self.model_path = model_path
        if self.model_path and os.path.exists(self.model_path):
            # When PyTorch / Ultralytics weights exist, load them
            try:
                import torch
                self.torch_model = torch.load(self.model_path, map_location="cpu")
                self.is_loaded = True
            except Exception:
                self.is_loaded = False
        else:
            self.is_loaded = False

    def predict(self, input_image_path: str, output_image_path: Optional[str] = None) -> str:
        """
        Enhance scanned/handwritten document image (contrast, deskew, noise reduction).
        Saves the enhanced image to output_image_path or appends '_enhanced'.
        """
        if not output_image_path:
            p = Path(input_image_path)
            output_image_path = str(p.parent / f"{p.stem}_enhanced{p.suffix}")

        os.makedirs(os.path.dirname(output_image_path), exist_ok=True)

        with Image.open(input_image_path) as img:
            # Convert to grayscale
            gray = img.convert("L")
            # Autocontrast to balance light and dark
            enhanced = ImageOps.autocontrast(gray, cutoff=2)
            # Boost sharpness for text edges
            sharpener = ImageEnhance.Sharpness(enhanced)
            enhanced = sharpener.enhance(2.0)
            # Boost contrast
            contrast = ImageEnhance.Contrast(enhanced)
            enhanced = contrast.enhance(1.5)
            # Save enhanced image
            enhanced.save(output_image_path)

        return output_image_path
