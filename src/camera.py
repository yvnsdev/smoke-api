# src/camera_inference.py
import os
import torch
from torchvision import models, transforms
import numpy as np
import cv2
import logging

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO),
                    format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("camera-inference")


class CameraInference:
    """
    Camera-based smoke classification ONLY (detección deshabilitada).
    - Clasificador: Swin V2 (torchvision)
    """

    AVAILABLE_MODELS = ['swinv2']
    _instance: 'CameraInference' = None

    def __init__(
        self,
        model_name: str = 'swinv2',
        model_weights: str = '',
        num_classes: int = 2,
        pretrained: bool = True,
        device: torch.device | str | None = None,
        labels: list = ('no_smoke', 'smoke'),
        half: bool = False,
        # det_model_weights: str = '.best.pt',   # ← eliminado (solo cls)
    ):
        if device is None:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.device = torch.device(device)
        self.half = bool(half)

        # --- SOLO CLASIFICACIÓN ---
        if model_name not in self.AVAILABLE_MODELS:
            raise ValueError(f"Model {model_name} is not available, try one of: {self.AVAILABLE_MODELS}")

        if model_name == 'swinv2':
            self.model = models.swin_v2_b(weights=None)
            self.model.head = torch.nn.Linear(
                in_features=self.model.head.in_features,
                out_features=num_classes
            )

        self.model.to(self.device)
        state = torch.load(model_weights, map_location=self.device)
        self.model.load_state_dict(state)
        if self.half and self.device.type == "cuda":
            self.model.half()
        self.model.eval()

        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((256, 256), transforms.InterpolationMode.BICUBIC),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])

        self.labels = list(labels)
        log.info("CameraInference listo (SOLO CLASIFICACIÓN) | device=%s | cls=%s",
                 self.device, model_name)

    @classmethod
    def get_instance(
        cls,
        model_name: str = 'swinv2',
        model_weights: str = '',
        num_classes: int = 2,
        pretrained: bool = True,
        device: torch.device | str | None = None,
        labels: list = ('no_smoke', 'smoke'),
        half: bool = False,
        # det_model_weights: str = '.best.pt',
    ) -> 'CameraInference':
        if cls._instance is None:
            cls._instance = cls(
                model_name=model_name,
                model_weights=model_weights,
                num_classes=num_classes,
                pretrained=pretrained,
                device=device,
                labels=labels,
                half=half,
            )
        return cls._instance

    def predict(self, image):
        """
        image: BGR (cv2)
        return:
          label (str), confidence (float)
        """
        rgb_frame = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        img_tensor = self.transform(rgb_frame).unsqueeze(0).to(self.device)
        if self.half and self.device.type == "cuda":
            img_tensor = img_tensor.half()

        with torch.no_grad():
            outputs = self.model(img_tensor)
            probs = torch.nn.functional.softmax(outputs, dim=1)[0].detach().cpu().numpy()
            pred_idx = int(probs.argmax())
            confidence = float(probs[pred_idx])
            label = self.labels[pred_idx] if pred_idx < len(self.labels) else str(pred_idx)

        return label, confidence

