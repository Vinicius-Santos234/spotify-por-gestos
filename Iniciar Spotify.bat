@echo off
rem Controle do Spotify pela Web API oficial (precisa de Premium e do .env).
rem
rem E o modo que FUNCIONA COM JOGO ABERTO: fala HTTP com o Spotify em vez de
rem injetar tecla no Windows, entao foco e privilegio da janela em primeiro
rem plano nao importam. O modo de teclas de midia falha nesse caso.
rem
rem Exige o app do Spotify aberto e tendo tocado algo: a Web API comanda um
rem dispositivo ativo, e sem isso responde 404.
call "%~dp0_executar.bat" --controller spotify --no-preview %*
