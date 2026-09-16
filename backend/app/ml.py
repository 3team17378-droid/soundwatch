import hashlib
from pathlib import Path
from typing import Protocol

import numpy as np

from app.core.config import settings

CLASSES = [
    "자동차 경적",
    "엔진 및 차량",
    "공사 및 드릴",
    "사이렌",
    "개 짖는 소리",
    "음악",
    "사람 대화",
    "총성 또는 폭발음",
    "빗소리",
    "기타 환경음",
]


class Predictor(Protocol):
    name: str
    version: str
    mode: str

    def predict(self, y: np.ndarray, features: dict) -> np.ndarray: ...


class DemoPredictor:
    name = "soundwatch-feature-demo"
    version = "1.0.0"
    mode = "DEMO"

    def predict(self, y, features):
        # Hand-designed prototypes, not learned weights or calibrated likelihoods.
        # Feature-dependent and deterministic; scores must never be sold as model accuracy.
        vector = np.array(
            [
                features["centroid"] / 8000,
                features["zcr"],
                min(features["modulation"], 2) / 2,
                features["silence_ratio"],
            ]
        )
        prototypes = np.array(
            [
                [0.12, 0.08, 0.1, 0],
                [0.04, 0.02, 0.08, 0],
                [0.38, 0.32, 0.3, 0.05],
                [0.2, 0.14, 0.3, 0],
                [0.15, 0.12, 0.65, 0.3],
                [0.22, 0.18, 0.2, 0.05],
                [0.12, 0.12, 0.5, 0.2],
                [0.4, 0.3, 0.9, 0.7],
                [0.48, 0.48, 0.05, 0],
                [0.3, 0.25, 0.4, 0.4],
            ]
        )
        logits = -6 * np.sum((prototypes - vector) ** 2, axis=1)
        scores = np.exp(logits - logits.max())
        return scores / scores.sum()


class OnnxPredictor:
    mode = "MODEL"

    def __init__(self):
        import onnxruntime as ort

        path = Path(settings.model_path)
        if not settings.model_path or not path.is_file():
            raise ValueError("MODEL 모드의 ONNX 모델 파일이 없습니다.")
        self.name, self.version = settings.model_name, settings.model_version
        self.sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        self.session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
        inputs = self.session.get_inputs()
        if len(inputs) != 1 or inputs[0].type != "tensor(float)" or len(inputs[0].shape) != 2:
            raise ValueError("모델 입력은 float32 [batch, 160000] 파형이어야 합니다.")
        self.input_name = inputs[0].name

    def predict(self, y, features):
        windows = []
        width = 160000
        for start in range(0, len(y), width):
            clip = np.pad(y[start : start + width], (0, max(0, width - len(y[start : start + width]))))
            raw = np.asarray(self.session.run(None, {self.input_name: clip[None].astype(np.float32)})[0])
            if raw.shape != (1, 10) or not np.isfinite(raw).all():
                raise ValueError("모델 출력은 유한한 float [1, 10] logits이어야 합니다.")
            scores = np.exp(raw[0] - raw.max())
            windows.append(scores / scores.sum())
        return np.mean(windows, axis=0)


def get_predictor() -> Predictor:
    return DemoPredictor() if settings.inference_mode == "DEMO" else OnnxPredictor()


def model_status():
    try:
        model = get_predictor()
        return {
            "mode": model.mode,
            "name": model.name,
            "version": model.version,
            "ready": True,
            "sha256": getattr(model, "sha256", None),
            "notice": "포트폴리오용 특징 기반 데모: 확률은 보정되지 않은 시연 점수입니다."
            if model.mode == "DEMO"
            else "호환 ONNX 모델 추론: 모델 카드와 검증 데이터 확인이 필요합니다.",
        }
    except Exception:
        return {
            "mode": "MODEL",
            "name": settings.model_name,
            "version": settings.model_version,
            "ready": False,
            "notice": "모델을 로드할 수 없습니다. 서버는 계속 동작하며 분석은 실패로 기록됩니다.",
        }
