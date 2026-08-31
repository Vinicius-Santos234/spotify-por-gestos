"""Controle pela Web API oficial do Spotify (requer conta Premium).

Configuração:
  1. Crie um app em https://developer.spotify.com/dashboard
  2. Adicione http://127.0.0.1:8888/callback como Redirect URI
  3. Copie .env.example para .env e preencha client id/secret
"""

import os

from .base import PlayerController

SCOPE = "user-modify-playback-state user-read-playback-state"
CACHE_PATH = ".spotify_token_cache"


class SpotifyApiController(PlayerController):
    name = "Spotify Web API"

    def __init__(self):
        from dotenv import load_dotenv

        load_dotenv()
        client_id = os.getenv("SPOTIPY_CLIENT_ID")
        client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
        redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8888/callback")

        if not client_id or not client_secret:
            raise RuntimeError(
                "SPOTIPY_CLIENT_ID / SPOTIPY_CLIENT_SECRET não encontrados.\n"
                "Copie .env.example para .env e preencha, ou use --controller media."
            )

        import spotipy
        from spotipy.oauth2 import SpotifyOAuth

        self._spotipy = spotipy
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=SCOPE,
                cache_path=CACHE_PATH,
            )
        )
        # Falha cedo, com o navegador aberto, em vez de no meio de um gesto.
        self.sp.current_user()

    def _device_id(self):
        """Se nada estiver ativo, usa o primeiro dispositivo disponível."""
        devices = self.sp.devices().get("devices", [])
        if not devices:
            return None
        for d in devices:
            if d.get("is_active"):
                return d["id"]
        return devices[0]["id"]

    def _call(self, fn, *args, **kwargs) -> str:
        try:
            return fn(*args, **kwargs)
        except self._spotipy.SpotifyException as exc:
            if exc.http_status == 404:
                return "Erro: nenhum dispositivo Spotify ativo (abra o app e toque algo)"
            if exc.http_status == 403:
                return "Erro: ação bloqueada (a Web API exige Premium)"
            return f"Erro do Spotify: {exc.msg or exc}"
        except Exception as exc:  # rede caindo não deve derrubar o loop de vídeo
            return f"Erro: {exc}"

    def play_pause(self) -> str:
        def run():
            playback = self.sp.current_playback()
            device = None if playback else self._device_id()
            if playback and playback.get("is_playing"):
                self.sp.pause_playback()
                return "Pausado"
            self.sp.start_playback(device_id=device)
            return "Tocando"

        return self._call(run)

    def next_track(self) -> str:
        def run():
            self.sp.next_track()
            return "Próxima faixa"

        return self._call(run)

    def previous_track(self) -> str:
        def run():
            self.sp.previous_track()
            return "Faixa anterior"

        return self._call(run)
