@echo off
rem Encanamento compartilhado pelos atalhos Iniciar*.bat.
rem Nao use este arquivo direto: use um dos "Iniciar ....bat".
rem
rem Existe para que cada atalho passe as SUAS proprias flags. Se o --no-preview
rem morasse no Iniciar.bat, o "Iniciar (debug).bat" herdaria e ficaria sem a
rem janela de video, que e a unica razao dele existir.
cd /d "%~dp0"

rem Chama o Python 3.10 explicitamente: o duplo clique em .py usa o py.exe,
rem que escolhe o Python 3.14 desta maquina - e as bibliotecas estao no 3.10.
set PYTHON=C:\Python310\python.exe

if not exist "%PYTHON%" (
    echo Nao encontrei o Python em %PYTHON%
    echo Edite este arquivo e corrija a linha "set PYTHON=".
    echo.
    pause
    exit /b 1
)

rem -u = saida sem buffer, para as mensagens aparecerem na hora
"%PYTHON%" -u src\main.py %*

echo.
echo ---------------------------------------------
echo Programa encerrado. Pressione uma tecla para fechar.
pause >nul
