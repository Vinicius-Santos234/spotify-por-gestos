"""Interface comum dos controladores de player."""

from abc import ABC, abstractmethod


class Controller(ABC):
    name = "base"

    @abstractmethod
    def play_pause(self) -> str:
        """Alterna entre tocar e pausar. Devolve uma linha de status."""

    @abstractmethod
    def next_track(self) -> str: ...

    @abstractmethod
    def previous_track(self) -> str: ...

    def close(self) -> None:
        pass
