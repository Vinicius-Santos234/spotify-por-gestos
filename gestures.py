"""Transforma landmarks da mão em ações de player.

Gestos reconhecidos:
  - deslizar a mão para a direita   -> próxima faixa
  - deslizar a mão para a esquerda  -> faixa anterior
  - punho fechado e parado por ~0.8 s -> play/pause

A mão aberta não dispara nada: ela é a posição de descanso que "rearma" o
play/pause. É de propósito — a mão parada na mesa ou no braço da cadeira fica
com os dedos esticados, então qualquer comando ligado à palma aberta dispara
sozinho o tempo todo. Fechar a mão é deliberado; esticar os dedos não é.

Pelo mesmo motivo não se tenta distinguir palma de dorso: contando dedos
esticados os dois são idênticos, e com este mapeamento isso não faz diferença.
"""

import math
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Deque, List, Optional, Tuple

from config import Config
from hand_tracker import Hand

# Índices dos landmarks (padrão MediaPipe).
WRIST = 0
FINGER_PIPS = (6, 10, 14, 18)  # indicador, médio, anelar, mínimo
FINGER_TIPS = (8, 12, 16, 20)
THUMB_IP, THUMB_TIP, PINKY_MCP = 3, 4, 17

# Se a mão sumir por mais que isso, o histórico de movimento é descartado.
TRACK_GAP_S = 0.3
# Salto entre dois frames grande demais para ser movimento humano: é erro de
# detecção (ou a outra mão entrou em cena). Descarta o histórico.
MAX_JUMP = 0.25


class Pose(Enum):
    NONE = "sem mão"
    OPEN = "palma aberta"
    FIST = "punho fechado"
    OTHER = "indefinido"


class Action(Enum):
    PLAY_PAUSE = "play/pause"
    NEXT = "próxima"
    PREV = "anterior"
    SCROLL_UP = "rolar para cima"
    SCROLL_DOWN = "rolar para baixo"


POSE_POR_NOME = {"punho": Pose.FIST, "palma": Pose.OPEN}


def _dist(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def extended_fingers(hand: Hand, margin: float) -> List[bool]:
    """Quais dedos estão esticados: [polegar, indicador, médio, anelar, mínimo].

    Usa distância até o pulso em vez de comparar alturas, para funcionar
    com a mão inclinada ou de lado.
    """
    px = hand.px
    wrist = px[WRIST]
    fingers = [
        _dist(px[THUMB_TIP], px[PINKY_MCP]) > _dist(px[THUMB_IP], px[PINKY_MCP]) * margin
    ]
    for pip, tip in zip(FINGER_PIPS, FINGER_TIPS):
        fingers.append(_dist(px[tip], wrist) > _dist(px[pip], wrist) * margin)
    return fingers


def classify_pose(hand: Hand, cfg: Config) -> Pose:
    fingers = extended_fingers(hand, cfg.finger_extended_margin)
    long_fingers = sum(fingers[1:])
    if long_fingers == 4:
        return Pose.OPEN
    if long_fingers == 0:
        return Pose.FIST
    return Pose.OTHER


@dataclass
class _Sample:
    t: float
    x: float
    y: float
    pose: Pose


class GestureEngine:
    """Consome um frame por vez e devolve a ação disparada, se houver."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        try:
            self.pose_alvo = POSE_POR_NOME[cfg.pose_play_pause]
        except KeyError:
            raise ValueError(
                f"config.pose_play_pause deve ser 'punho' ou 'palma', "
                f"não {cfg.pose_play_pause!r}"
            ) from None
        self._samples: Deque[_Sample] = deque()
        self.pose = Pose.NONE
        self._hold_start: Optional[float] = None
        self._armed = True  # play/pause só dispara com o gesto rearmado
        self._last_swipe = -999.0
        # Quanto dura o bloqueio depois do último swipe. Depende do eixo que
        # disparou: horizontal usa swipe_cooldown_s, vertical usa o de rolagem.
        self._swipe_cooldown = cfg.swipe_cooldown_s
        self._last_hold = -999.0
        self.hold_progress = 0.0
        self.swipe_dx = 0.0
        self.swipe_dy = 0.0
        self.swipe_progress = 0.0
        self.swipe_vertical_progress = 0.0

    def update(self, hand: Optional[Hand], now: float) -> Optional[Action]:
        if hand is None:
            self._samples.clear()
            self.pose = Pose.NONE
            self._hold_start = None
            self.hold_progress = 0.0
            self._armed = True
            return None

        self.pose = classify_pose(hand, self.cfg)

        x, y = hand.center

        # Reaparecimento depois de um sumiço, ou pulo de posição: começa do zero.
        if self._samples:
            prev = self._samples[-1]
            if now - prev.t > TRACK_GAP_S or math.hypot(x - prev.x, y - prev.y) > MAX_JUMP:
                self._samples.clear()

        self._samples.append(_Sample(now, x, y, self.pose))
        window = max(self.cfg.swipe_window_s, self.cfg.hold_duration_s)
        while self._samples and now - self._samples[0].t > window:
            self._samples.popleft()

        action = self._check_swipe(now)
        if action is not None:
            return action
        return self._check_hold(now)

    # --- swipe -------------------------------------------------------------

    def _check_swipe(self, now: float) -> Optional[Action]:
        cfg = self.cfg
        self.swipe_progress = 0.0
        self.swipe_vertical_progress = 0.0
        if now - self._last_swipe < self._swipe_cooldown:
            # Enquanto o cooldown corre, joga fora o movimento: é o retorno da
            # mão à posição inicial, que senão dispararia o swipe contrário.
            self._samples.clear()
            return None

        window = [s for s in self._samples if now - s.t <= cfg.swipe_window_s]
        if len(window) < 4:
            return None

        # Só o punho fechado ("mão guardada") não desliza — qualquer outra pose
        # vale. Exigir a mão aberta não funciona: no meio do movimento a mão
        # borra e inclina, e a pose vira "indefinido" bem quando o gesto está
        # acontecendo.
        aberta = sum(s.pose != Pose.FIST for s in window) / len(window)
        if aberta < 0.6:
            return None

        dx = window[-1].x - window[0].x
        dy = window[-1].y - window[0].y

        self.swipe_dx = dx
        self.swipe_dy = dy

        # Quanto do deslocamento necessário já foi feito, com sinal.
        # O HUD mostra isso como barra: sem ela não dá para saber se faltou
        # movimento, faltou velocidade ou a pose barrou o gesto.
        self.swipe_progress = max(-1.5, min(1.5, dx / cfg.swipe_min_dx))
        self.swipe_vertical_progress = max(-1.5, min(1.5, dy / cfg.swipe_min_dy))

        # Testar horizontal
        horiz_ok = (abs(dx) >= cfg.swipe_min_dx) and (abs(dx) >= abs(dy) * cfg.swipe_horizontal_ratio)

        # Testar vertical
        vert_ok = (abs(dy) >= cfg.swipe_min_dy) and (abs(dy) >= abs(dx) * cfg.swipe_vertical_ratio)

        # R2: Horizontal e vertical não se atropelam
        # Se os dois limiares forem atendidos ao mesmo tempo, ganha a direção
        # com maior deslocamento absoluto. Na prática não acontece: com as duas
        # proporções em 1.4, |dx| >= 1.4|dy| e |dy| >= 1.4|dx| não podem valer
        # juntas. O desempate existe para o caso de alguém baixar os limiares.
        if horiz_ok and vert_ok:
            if abs(dx) > abs(dy):
                vert_ok = False
            else:
                horiz_ok = False

        if horiz_ok:
            self._disparou(now, cfg.swipe_cooldown_s)
            return Action.NEXT if dx > 0 else Action.PREV

        if vert_ok:
            self._disparou(now, cfg.scroll_cooldown_s)
            # Coordenadas: y cresce para baixo. Mão descendo -> dy > 0 -> rola a página para baixo
            return Action.SCROLL_DOWN if dy > 0 else Action.SCROLL_UP

        return None

    def _disparou(self, now: float, cooldown: float) -> None:
        """Registra um swipe e arma o bloqueio pelo tempo do eixo que disparou."""
        self._last_swipe = now
        self._swipe_cooldown = cooldown
        self._samples.clear()
        self._hold_start = None
        self.hold_progress = 0.0

    # --- pose sustentada ---------------------------------------------------

    def _check_hold(self, now: float) -> Optional[Action]:
        cfg = self.cfg

        if self.pose != self.pose_alvo:
            # Qualquer outra pose = descanso: rearma o play/pause.
            self._hold_start = None
            self.hold_progress = 0.0
            self._armed = True
            return None

        blocked = (
            not self._armed
            or now - self._last_swipe < cfg.hold_lockout_after_swipe_s
            or now - self._last_hold < cfg.hold_cooldown_s
        )
        if blocked:
            self._hold_start = None
            self.hold_progress = 0.0
            return None

        if self._hold_start is None:
            self._hold_start = now

        if self._movement_since(self._hold_start) > cfg.hold_max_movement:
            # Mexeu no meio da contagem: recomeça.
            self._hold_start = now
            self.hold_progress = 0.0
            return None

        elapsed = now - self._hold_start
        self.hold_progress = min(1.0, elapsed / cfg.hold_duration_s)
        if elapsed < cfg.hold_duration_s:
            return None

        self._last_hold = now
        self._armed = False
        self._hold_start = None
        self.hold_progress = 0.0
        return Action.PLAY_PAUSE

    def _movement_since(self, start_t: float) -> float:
        pts = [s for s in self._samples if s.t >= start_t]
        if len(pts) < 2:
            return 0.0
        xs = [p.x for p in pts]
        ys = [p.y for p in pts]
        return max(max(xs) - min(xs), max(ys) - min(ys))
