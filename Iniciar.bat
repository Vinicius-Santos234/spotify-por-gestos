@echo off
title Spotify por Gestos
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
"%PYTHON%" -u main.py %*

echo.
echo ---------------------------------------------
echo Programa encerrado. Pressione uma tecla para fechar.
pause >nul
