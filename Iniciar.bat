@echo off
rem Modo padrao: teclas de midia do sistema (Spotify, YouTube, qualquer player).
rem Nao precisa de login nem de Premium.
rem
rem Sem janela de video: e o modo para usar por cima de outra coisa. A camera
rem continua ligada, porque e ela que detecta os gestos.
rem Para ver o video, use o "Iniciar (debug).bat".
rem
rem AVISO: teclas de midia nao chegam quando a janela em foco roda como
rem administrador (jogos com anticheat, por exemplo) - o Windows bloqueia.
rem Nesse caso use o "Iniciar Spotify.bat", que fala HTTP e nao depende disso.
call "%~dp0_executar.bat" --no-preview %*
