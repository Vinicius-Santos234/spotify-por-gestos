@echo off
rem Rolagem do YouTube por gestos verticais da mao.
rem O Iniciar.bat sem argumento usa --controller media, que controla musica e
rem NAO rola pagina: os gestos apareciam na tela e nada acontecia.
call "%~dp0Iniciar.bat" --controller youtube
