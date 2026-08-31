from .base import Controller, PlayerController, ScrollController


def get_controller(kind: str) -> Controller:
    if kind == "media":
        from .media_keys import MediaKeysController

        return MediaKeysController()
    if kind == "spotify":
        from .spotify_api import SpotifyApiController

        return SpotifyApiController()
    if kind == "youtube":
        from .youtube import YouTubeController

        return YouTubeController()
    raise ValueError(f"controlador desconhecido: {kind}")


__all__ = ["Controller", "PlayerController", "ScrollController", "get_controller"]
