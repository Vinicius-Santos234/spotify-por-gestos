@echo off
rem Rolagem do YouTube por arrasto: junte polegar e indicador e arraste,
rem como no celular. Soltar os dedos e reposicionar nao rola nada.
rem
rem Sem janela de video: voce esta olhando o YouTube, e a propria pagina
rem rolando ja e o retorno de que a pinca funcionou.
rem Para calibrar a pinca vendo o circulo verde, use o "Iniciar (debug).bat".
call "%~dp0_executar.bat" --controller youtube --no-preview %*
