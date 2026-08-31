@echo off
rem Controle do Spotify pela Web API oficial (precisa de Premium e do .env).
rem
rem Sem janela de video de proposito: este e o modo para usar com jogo aberto,
rem e uma janela a mais so atrapalharia. A camera continua ligada, porque e
rem ela que detecta os gestos. Para ver o video, use o "Iniciar (debug).bat".
rem
rem Este modo funciona em segundo plano, ao contrario das teclas de midia: fala
rem HTTP com o Spotify em vez de injetar tecla no Windows, entao foco e
rem privilegio da janela em primeiro plano nao importam.
rem
rem Exige o app do Spotify aberto e tendo tocado algo: a Web API comanda um
rem dispositivo ativo, e sem isso responde 404.
call "%~dp0Iniciar.bat" --controller spotify --no-preview
