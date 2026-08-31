"""Controle por teclas de mídia globais do sistema.

Funciona com o Spotify desktop, o web player, YouTube — qualquer coisa que
responda às teclas de mídia. Não precisa de login nem de conta Premium.
"""

import ctypes
import platform
import sys

from .base import Controller

VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_PLAY_PAUSE = 0xB3

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
INPUT_KEYBOARD = 1

ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong


class _KeyBdInput(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ULONG_PTR),
    ]


class _MouseInput(ctypes.Structure):
    """Não é usada, mas é o maior membro da union: sem ela sizeof(INPUT) fica
    errado e o SendInput rejeita tudo silenciosamente."""

    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ULONG_PTR),
    ]


class _HardwareInput(ctypes.Structure):
    _fields_ = [
        ("uMsg", ctypes.c_ulong),
        ("wParamL", ctypes.c_ushort),
        ("wParamH", ctypes.c_ushort),
    ]


class _InputUnion(ctypes.Union):
    _fields_ = [("mi", _MouseInput), ("ki", _KeyBdInput), ("hi", _HardwareInput)]


class _Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("union", _InputUnion)]


class _WindowsKeys:
    def send(self, vk: int) -> bool:
        user32 = ctypes.windll.user32
        events = (_Input * 2)()
        for i, flags in enumerate((KEYEVENTF_EXTENDEDKEY, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP)):
            events[i].type = INPUT_KEYBOARD
            events[i].union.ki = _KeyBdInput(wVk=vk, wScan=0, dwFlags=flags, time=0, dwExtraInfo=0)
        sent = user32.SendInput(2, ctypes.byref(events), ctypes.sizeof(_Input))
        return sent == 2


class _PynputKeys:
    """Fallback para Linux/macOS."""

    def __init__(self):
        from pynput.keyboard import Controller as KbController, Key

        self._kb = KbController()
        self._map = {
            VK_MEDIA_PLAY_PAUSE: Key.media_play_pause,
            VK_MEDIA_NEXT_TRACK: Key.media_next,
            VK_MEDIA_PREV_TRACK: Key.media_previous,
        }

    def send(self, vk: int) -> bool:
        self._kb.tap(self._map[vk])
        return True


class MediaKeysController(Controller):
    name = "teclas de mídia"

    def __init__(self):
        if platform.system() == "Windows":
            self._backend = _WindowsKeys()
        else:
            try:
                self._backend = _PynputKeys()
            except ImportError:
                sys.exit(
                    "Fora do Windows este modo precisa do pynput: pip install pynput\n"
                    "Ou use --controller spotify."
                )

    def _send(self, vk: int, label: str) -> str:
        if self._backend.send(vk):
            return label
        # Acontece quando a janela em foco roda como administrador: o Windows
        # bloqueia entrada vinda de um processo com privilégio menor.
        return f"{label}: falha ao enviar a tecla (janela em foco é de administrador?)"

    def play_pause(self) -> str:
        return self._send(VK_MEDIA_PLAY_PAUSE, "Play/Pause")

    def next_track(self) -> str:
        return self._send(VK_MEDIA_NEXT_TRACK, "Próxima faixa")

    def previous_track(self) -> str:
        return self._send(VK_MEDIA_PREV_TRACK, "Faixa anterior")
