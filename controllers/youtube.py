"""Controle do YouTube por entrada de sistema (scroll e setas)."""

import ctypes
import platform
import sys

from .base import Controller
from .media_keys import _Input, _MouseInput, ULONG_PTR

INPUT_MOUSE = 0
MOUSEEVENTF_WHEEL = 0x0800

class _WindowsMouse:
    def send_wheel(self, dy: int) -> bool:
        user32 = ctypes.windll.user32
        event = _Input()
        event.type = INPUT_MOUSE
        event.union.mi = _MouseInput(
            dx=0,
            dy=0,
            mouseData=dy,
            dwFlags=MOUSEEVENTF_WHEEL,
            time=0,
            dwExtraInfo=0
        )
        sent = user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(_Input))
        return sent == 1

class _PynputMouse:
    """Fallback para Linux/macOS."""
    def __init__(self):
        from pynput.mouse import Controller as MouseController
        self._mouse = MouseController()

    def send_wheel(self, dy: int) -> bool:
        # pynput scroll usa dy positivo para cima e negativo para baixo, ou o inverso?
        # dy>0 no windows = pra frente/pra cima. No pynput, scroll(dx, dy).
        # Vamos passar os valores aproximados (no Windows mouseData = 120 por tick).
        # Convertendo 120 para 1 "tick" do pynput.
        ticks = dy // 120 if dy else 0
        if ticks == 0:
            ticks = 1 if dy > 0 else -1
        self._mouse.scroll(0, ticks)
        return True

class YouTubeController(Controller):
    name = "youtube"

    def __init__(self):
        if platform.system() == "Windows":
            self._backend = _WindowsMouse()
        else:
            try:
                self._backend = _PynputMouse()
            except ImportError:
                sys.exit(
                    "Fora do Windows este modo precisa do pynput: pip install pynput\n"
                )

    def scroll_up(self) -> str:
        if self._backend.send_wheel(120):  # 120 = WHEEL_DELTA (para cima)
            return "Rolou para cima"
        return "Falha ao rolar para cima"

    def scroll_down(self) -> str:
        if self._backend.send_wheel(-120): # -120 = -WHEEL_DELTA (para baixo)
            return "Rolou para baixo"
        return "Falha ao rolar para baixo"
