"""Camada fina em cima do MediaPipe HandLandmarker (Tasks API)."""

import os

# Silencia os logs nativos do MediaPipe/TFLite. Precisa vir antes do import.
os.environ.setdefault("GLOG_minloglevel", "2")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

import contextlib
import time
import urllib.request
from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python import vision

from config import MODEL_PATH, MODEL_URL, Config

# Conexões usadas para desenhar o esqueleto da mão.
HAND_CONNECTIONS = [
    (c.start, c.end) for c in vision.HandLandmarksConnections.HAND_CONNECTIONS
]


@dataclass
class Hand:
    """Uma mão detectada em um frame."""

    # Coordenadas normalizadas (0..1) em relação à imagem.
    norm: List[Tuple[float, float]]
    # Coordenadas em pixels — usadas para medir distâncias sem distorção.
    px: List[Tuple[float, float]]
    label: str  # "Left" / "Right"

    @property
    def center(self) -> Tuple[float, float]:
        """Base do dedo médio: ponto mais estável da palma."""
        return self.norm[9]


@contextlib.contextmanager
def _quiet_stderr():
    """Esconde os warnings nativos do MediaPipe.

    Eles são escritos direto no fd 2 antes do InitGoogle(), então escapam do
    GLOG_minloglevel. Usado só na inicialização, para não engolir erros reais.
    """
    saved = os.dup(2)
    devnull = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(devnull, 2)
        yield
    finally:
        os.dup2(saved, 2)
        os.close(devnull)
        os.close(saved)


def ensure_model() -> None:
    """Baixa o modelo do MediaPipe na primeira execução."""
    if MODEL_PATH.exists():
        return
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"Baixando modelo de mãos (~8 MB) para {MODEL_PATH}...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    print("Modelo baixado.")


class HandTracker:
    # Os warnings do MediaPipe saem na criação e na primeira mão detectada.
    QUIET_WARMUP_S = 3.0

    def __init__(self, cfg: Config, quiet: bool = True):
        ensure_model()
        self._quiet_until = time.monotonic() + self.QUIET_WARMUP_S if quiet else 0.0
        options = vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(MODEL_PATH)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=cfg.min_detection_confidence,
            min_hand_presence_confidence=cfg.min_presence_confidence,
            min_tracking_confidence=cfg.min_tracking_confidence,
        )
        with self._maybe_quiet():
            self._landmarker = vision.HandLandmarker.create_from_options(options)

    def _maybe_quiet(self):
        if time.monotonic() < self._quiet_until:
            return _quiet_stderr()
        return contextlib.nullcontext()

    def detect(self, frame_bgr, timestamp_ms: int) -> Optional[Hand]:
        h, w = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        with self._maybe_quiet():
            result = self._landmarker.detect_for_video(image, timestamp_ms)

        if not result.hand_landmarks:
            return None

        landmarks = result.hand_landmarks[0]
        norm = [(lm.x, lm.y) for lm in landmarks]
        px = [(lm.x * w, lm.y * h) for lm in landmarks]
        label = "?"
        if result.handedness and result.handedness[0]:
            label = result.handedness[0][0].category_name
        return Hand(norm=norm, px=px, label=label)

    def close(self) -> None:
        self._landmarker.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
