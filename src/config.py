"""Parâmetros ajustáveis do reconhecimento de gestos.

Se os gestos estiverem disparando demais, aumente os limiares.
Se estiverem difíceis de disparar, diminua.
"""

from dataclasses import dataclass
from pathlib import Path

# O codigo mora em src/, entao a raiz do projeto (onde ficam models/ e o .env)
# esta um nivel acima. Sem o segundo .parent, o modelo seria procurado em
# src/models e baixado de novo a cada execucao.
PROJECT_DIR = Path(__file__).parent.parent
MODEL_PATH = PROJECT_DIR / "models" / "hand_landmarker.task"
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)


@dataclass
class Config:
    # --- câmera ---
    camera_index: int = 0
    frame_width: int = 640
    frame_height: int = 480

    # --- detecção de mão ---
    min_detection_confidence: float = 0.6
    min_presence_confidence: float = 0.5
    min_tracking_confidence: float = 0.5

    # --- swipe (pular / voltar faixa) ---
    # Janela de tempo analisada para detectar o movimento. Aumente se você
    # desliza a mão devagar.
    swipe_window_s: float = 0.7
    # Deslocamento horizontal mínimo, em fração da largura da imagem.
    swipe_min_dx: float = 0.16
    # O movimento precisa ser N vezes mais horizontal do que vertical.
    swipe_horizontal_ratio: float = 1.4

    # Tempo mínimo entre dois swipes horizontais (pular/voltar faixa).
    swipe_cooldown_s: float = 1.0

    # --- rolagem por arrasto (pinça) ---
    # Distância entre polegar e indicador, como fração do tamanho da mão
    # (pulso -> base do médio), abaixo da qual conta como pinça fechada.
    # Menor = precisa encostar mais os dedos.
    pinca_ratio: float = 0.45
    # Quantos dos três dedos livres (médio, anelar, mínimo) precisam estar
    # esticados para contar como pinça. É o que distingue pinça de punho, que
    # também junta polegar e indicador. 0 desliga a distinção.
    pinca_dedos_livres: int = 1
    # Quantos "cliques" de roda um arrasto da altura inteira da tela produz.
    # É a sensibilidade: aumente se a rolagem estiver preguiçosa.
    scroll_ticks_por_tela: float = 25.0
    # True = conteúdo acompanha o dedo, como no celular (arrastar para baixo
    # mostra o que estava acima). False = sentido da roda do mouse.
    scroll_natural: bool = True

    # --- pose sustentada (play/pause) ---
    # Qual pose, mantida parada, dispara o play/pause: "punho" ou "palma".
    # O padrão é punho porque a mão em repouso (na mesa, no braço da cadeira)
    # fica naturalmente com os dedos esticados — com "palma" o play/pause
    # dispara sozinho o tempo todo.
    pose_play_pause: str = "punho"
    # Quanto tempo a pose precisa ficar parada.
    hold_duration_s: float = 0.8
    # Deslocamento máximo (fração da largura) para a mão contar como "parada".
    hold_max_movement: float = 0.06
    # Tempo mínimo entre dois play/pause.
    hold_cooldown_s: float = 1.2
    # Após um swipe, ignora o gesto de play/pause por este tempo.
    hold_lockout_after_swipe_s: float = 1.0

    # --- classificação de dedos ---
    # Margem para considerar um dedo esticado (1.0 = sem margem).
    finger_extended_margin: float = 1.05
