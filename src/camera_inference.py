# camera_inference.py (root)
import torch
from torchvision import models, transforms
import cv2

class CameraInference:
    """
    Solo CLASIFICACIÓN (sin YOLO).
    """

    AVAILABLE_MODELS = ['swinv2']
    _instance: 'CameraInference' = None

    def __init__(self, model_name: str = 'swinv2', model_weights: str = '',
                 num_classes: int = 2, pretrained: bool = True,
                 device: torch.device = None, labels: list = ['no_smoke', 'smoke'],
                 half: bool = False):
        if device is None:
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            device = torch.device(device)

        self.device = device
        self.half = half

        if model_name not in self.AVAILABLE_MODELS:
            raise ValueError(f"Model {model_name} is not available, Try: {self.AVAILABLE_MODELS}.")

        if model_name == 'swinv2':
            self.model = models.swin_v2_b(weights=None)
            self.model.head = torch.nn.Linear(
                in_features=self.model.head.in_features,
                out_features=num_classes
            )

        self.model.to(self.device)
        self.model.load_state_dict(torch.load(model_weights, map_location=device))
        if self.half and self.device.type == "cuda":
            self.model.half()
        self.model.eval()

        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((256, 256), transforms.InterpolationMode.BICUBIC),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

        self.labels = labels

    @classmethod
    def get_instance(cls, model_name: str = 'swinv2', model_weights: str = '',
                     num_classes: int = 2, pretrained: bool = True,
                     device: torch.device = None, labels: list = ['no_smoke', 'smoke'],
                     half: bool = False) -> 'CameraInference':
        if cls._instance is None:
            cls._instance = cls(
                model_name=model_name,
                model_weights=model_weights,
                num_classes=num_classes,
                pretrained=pretrained,
                device=device,
                labels=labels,
                half=half
            )
        return cls._instance

    def predict(self, image):
        rgb_frame = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        img_tensor = self.transform(rgb_frame).unsqueeze(0).to(self.device)
        if self.half and self.device.type == "cuda":
            img_tensor = img_tensor.half()

        with torch.no_grad():
            outputs = self.model(img_tensor)
            probs = torch.nn.functional.softmax(outputs, dim=1)[0].cpu().numpy()
            pred_idx = int(probs.argmax())
            confidence = float(probs[pred_idx])
            label = self.labels[pred_idx]

        return label, confidence

