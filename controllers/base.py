"""Interfaces dos controladores.

São duas, de propósito. Um controlador de player não rola página e um
controlador de rolagem não toca música — obrigar os dois a implementar os
cinco métodos produziria métodos vazios, que é justamente o que esconde
esquecimento.

Cada controlador herda a interface do que ele faz, e ali os métodos são
`@abstractmethod` de verdade: esquecer um vira `TypeError` na hora de
instanciar, não silêncio em tempo de execução.

Quem descobre se um controlador atende uma ação é o `main.py`, procurando o
método pelo nome. Ver `ACAO_PARA_METODO` lá.
"""

from abc import ABC, abstractmethod


class Controller(ABC):
    """O que todo controlador tem, independente do que ele controla."""

    name = "base"

    def close(self) -> None:
        pass


class PlayerController(Controller):
    """Controla reprodução de mídia."""

    @abstractmethod
    def play_pause(self) -> str:
        """Alterna entre tocar e pausar. Devolve uma linha de status."""

    @abstractmethod
    def next_track(self) -> str: ...

    @abstractmethod
    def previous_track(self) -> str: ...


class ScrollController(Controller):
    """Rola a página, por quantidade."""

    @abstractmethod
    def scroll_by(self, ticks: int) -> str:
        """Rola `ticks` cliques de roda. Positivo sobe o conteúdo, negativo desce."""
