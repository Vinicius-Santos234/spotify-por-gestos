"""Interface comum dos controladores de player."""

from abc import ABC, abstractmethod


class Controller(ABC):
    name = "base"

    def play_pause(self) -> str:
        """Alterna entre tocar e pausar. Devolve uma linha de status."""
        return ""

    def next_track(self) -> str:
        return ""

    def previous_track(self) -> str:
        return ""

    def scroll_up(self) -> str:
        return ""

    def scroll_down(self) -> str:
        return ""

    def close(self) -> None:
        pass
