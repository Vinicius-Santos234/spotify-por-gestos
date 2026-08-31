from .base import Controller


def get_controller(kind: str) -> Controller:
    if kind == "media":
        from .media_keys import MediaKeysController

        return MediaKeysController()
    if kind == "spotify":
        from .spotify_api import SpotifyApiController

        return SpotifyApiController()
    raise ValueError(f"controlador desconhecido: {kind}")


__all__ = ["Controller", "get_controller"]
