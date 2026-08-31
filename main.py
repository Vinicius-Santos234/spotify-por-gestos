"""Controle o Spotify com gestos da mão pela webcam.

Uso:
    python main.py                        # teclas de mídia (padrão)
    python main.py --controller spotify   # Web API oficial
    python main.py --no-preview           # roda sem a janela de vídeo

Gestos:
    deslizar a mão para a direita    -> próxima faixa
    deslizar a mão para a esquerda   -> faixa anterior
    punho fechado parado por ~0.8 s  -> play/pause
    mão aberta                       -> descanso (rearma o play/pause)
"""

import argparse
import sys
import time
import unicodedata
from typing import Optional

import cv2

from config import Config
from controllers import get_controller
from gestures import Action, GestureEngine, Pose, extended_fingers

# Qual método do controlador atende cada ação. Um controlador que não implementa
# o método simplesmente não atende aquela ação — ver controllers/base.py.
ACAO_PARA_METODO = {
    Action.PLAY_PAUSE: "play_pause",
    Action.NEXT: "next_track",
    Action.PREV: "previous_track",
    Action.SCROLL_UP: "scroll_up",
    Action.SCROLL_DOWN: "scroll_down",
}
from hand_tracker import HAND_CONNECTIONS, Hand, HandTracker

GREEN = (120, 220, 90)
GRAY = (170, 170, 170)
WHITE = (245, 245, 245)
ACCENT = (80, 200, 255)
FONT = cv2.FONT_HERSHEY_SIMPLEX


def _setup_console() -> None:
    """Evita acentos quebrados no terminal do Windows."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def _ascii(text: str) -> str:
    """cv2.putText não desenha acentos — tira antes de mostrar na janela."""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()


def open_camera(cfg: Config):
    backend = cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY
    cap = cv2.VideoCapture(cfg.camera_index, backend)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cfg.frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.frame_height)
    if not cap.isOpened():
        sys.exit(
            f"Não consegui abrir a câmera {cfg.camera_index}. "
            "Feche outros programas que a usem ou tente --camera 1."
        )
    return cap


def draw_hand(frame, hand: Hand) -> None:
    pts = [(int(x), int(y)) for x, y in hand.px]
    for start, end in HAND_CONNECTIONS:
        cv2.line(frame, pts[start], pts[end], GREEN, 2)
    for p in pts:
        cv2.circle(frame, p, 3, WHITE, -1)


def draw_hud(frame, pose: Pose, engine: GestureEngine, controller_name: str,
             last_event: Optional[str], last_event_t: float, fps: float,
             debug_text: str = "") -> None:
    h, w = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 62), (25, 25, 25), -1)
    cv2.rectangle(overlay, (0, h - 30), (w, h), (25, 25, 25), -1)
    cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)

    cv2.putText(frame, _ascii(f"Pose: {pose.value}"), (12, 25), FONT, 0.6, WHITE, 2)
    cv2.putText(frame, _ascii(f"Controle: {controller_name}"), (12, 50), FONT, 0.5, GRAY, 1)
    cv2.putText(frame, f"{fps:4.1f} fps", (w - 90, 25), FONT, 0.5, GRAY, 1)

    # Barra de carregamento do play/pause.
    if engine.hold_progress > 0:
        bar_w = int(220 * engine.hold_progress)
        cv2.rectangle(frame, (w - 240, 38), (w - 240 + 220, 50), (70, 70, 70), 1)
        cv2.rectangle(frame, (w - 240, 38), (w - 240 + bar_w, 50), ACCENT, -1)

    # Barra do swipe: cresce do centro para o lado do movimento e fica verde
    # quando o deslocamento já dá para pular a faixa.
    if abs(engine.swipe_progress) > 0.05:
        cx, y0, y1, meia = w // 2, 72, 84, 150
        preenchido = int(meia * min(1.0, abs(engine.swipe_progress)))
        cor = GREEN if abs(engine.swipe_progress) >= 1.0 else ACCENT
        cv2.rectangle(frame, (cx - meia, y0), (cx + meia, y1), (70, 70, 70), 1)
        if engine.swipe_progress > 0:
            cv2.rectangle(frame, (cx, y0), (cx + preenchido, y1), cor, -1)
        else:
            cv2.rectangle(frame, (cx - preenchido, y0), (cx, y1), cor, -1)

    # Barra do swipe vertical: cresce do centro para cima ou para baixo
    if abs(engine.swipe_vertical_progress) > 0.05:
        cy, x0, x1, meia_v = h // 2, 20, 32, 100
        preenchido_v = int(meia_v * min(1.0, abs(engine.swipe_vertical_progress)))
        cor_v = GREEN if abs(engine.swipe_vertical_progress) >= 1.0 else ACCENT
        cv2.rectangle(frame, (x0, cy - meia_v), (x1, cy + meia_v), (70, 70, 70), 1)
        if engine.swipe_vertical_progress > 0:
            cv2.rectangle(frame, (x0, cy), (x1, cy + preenchido_v), cor_v, -1)
        else:
            cv2.rectangle(frame, (x0, cy - preenchido_v), (x1, cy), cor_v, -1)

    if last_event and time.monotonic() - last_event_t < 2.0:
        cv2.putText(frame, _ascii(last_event), (12, h - 55), FONT, 0.9, ACCENT, 2)

    alvo = "punho" if engine.pose_alvo is Pose.FIST else "palma"
    footer = f"Deslize <- -> pular faixa | {alvo} parado = play/pause | Q = sair"
    cv2.putText(frame, _ascii(debug_text or footer), (12, h - 10), FONT, 0.5, GRAY, 1)


def main() -> None:
    _setup_console()
    parser = argparse.ArgumentParser(description="Controle o Spotify com gestos da mão.")
    parser.add_argument("--controller", choices=["media", "spotify", "youtube"], default="media",
                        help="media = teclas de mídia do sistema (padrão); "
                             "spotify = Web API oficial (precisa de Premium e .env); "
                             "youtube = scroll na janela em foco")
    parser.add_argument("--camera", type=int, default=0, help="índice da webcam")
    parser.add_argument("--no-preview", action="store_true", help="roda sem janela de vídeo")
    parser.add_argument("--no-mirror", action="store_true",
                        help="não espelha a imagem (por padrão a imagem é espelhada)")
    parser.add_argument("--debug", action="store_true", help="mostra dedos detectados")
    parser.add_argument("--verbose", action="store_true",
                        help="mostra os logs internos do MediaPipe")
    args = parser.parse_args()

    cfg = Config(camera_index=args.camera)

    try:
        controller = get_controller(args.controller)
    except RuntimeError as exc:
        sys.exit(str(exc))

    cap = open_camera(cfg)
    engine = GestureEngine(cfg)

    alvo = "punho fechado" if engine.pose_alvo is Pose.FIST else "palma aberta"
    print(f"Controle: {controller.name}")
    avisadas = set()  # ações que este controlador não atende, já reportadas
    print("Gestos: deslizar a mao -> proxima faixa / <- faixa anterior")
    print(f"        {alvo} parado por {cfg.hold_duration_s:.1f}s = play/pause")
    print("Sair: Q na janela de video, ou Ctrl+C aqui.\n")

    last_event: Optional[str] = None
    last_event_t = 0.0
    fps = 0.0
    t_start = time.monotonic()
    last_t = t_start

    try:
        with HandTracker(cfg, quiet=not args.verbose) as tracker:
            while True:
                ok, frame = cap.read()
                if not ok:
                    print("Falha ao ler da câmera.")
                    break

                if not args.no_mirror:
                    frame = cv2.flip(frame, 1)

                now = time.monotonic()
                hand = tracker.detect(frame, int((now - t_start) * 1000))
                action = engine.update(hand, now)

                if action is not None:
                    metodo = getattr(controller, ACAO_PARA_METODO[action], None)
                    if metodo is None:
                        # Este controlador não atende esta ação — o de música não
                        # rola, o de rolagem não toca. Avisa uma vez e segue: em
                        # silêncio, ficaria indistinguível de gesto não detectado.
                        if action not in avisadas:
                            avisadas.add(action)
                            print(f"[{controller.name}] não atende '{action.value}' — gesto ignorado")
                    else:
                        status = metodo()
                        last_event, last_event_t = status, now
                        print(f"[{time.strftime('%H:%M:%S')}] {action.value} -> {status}")

                fps = 0.9 * fps + 0.1 / max(1e-3, now - last_t)
                last_t = now

                if not args.no_preview:
                    if hand is not None:
                        draw_hand(frame, hand)
                    debug_text = ""
                    if args.debug and hand is not None:
                        names = ["pol", "ind", "med", "ane", "min"]
                        flags = extended_fingers(hand, cfg.finger_extended_margin)
                        dedos = " ".join(
                            f"{n}:{'1' if f else '0'}" for n, f in zip(names, flags)
                        )
                        debug_text = (
                            f"{dedos} | dx {engine.swipe_dx:+.2f} "
                            f"(precisa {cfg.swipe_min_dx:.2f})"
                        )
                    draw_hud(frame, engine.pose, engine, controller.name,
                             last_event, last_event_t, fps, debug_text)
                    cv2.imshow("Spotify por gestos", frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key in (ord("q"), ord("Q"), 27):
                        break
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        cv2.destroyAllWindows()
        controller.close()
        print("Encerrado.")


if __name__ == "__main__":
    main()
