"""Controle do YouTube por entrada de sistema (scroll e setas)."""

import ctypes
import platform
import sys

from .base import ScrollController
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
        # No pynput, assim como no Windows, dy positivo rola para cima (frente)
        # e negativo para baixo (trás).
        # Convertendo 120 de mouseData (padrão do Windows) para 1 "tick" do pynput.
        ticks = dy // 120 if dy else 0
        if ticks == 0:
            ticks = 1 if dy > 0 else -1
        self._mouse.scroll(0, ticks)
        return True

class YouTubeController(ScrollController):
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

    def scroll_by(self, ticks: int) -> str:
        # WHEEL_DELTA = 120 é um "clique" de roda.
        if self._backend.send_wheel(ticks * 120):
            sentido = "cima" if ticks > 0 else "baixo"
            return f"Rolou {abs(ticks)} para {sentido}"
        return "Falha ao rolar"
