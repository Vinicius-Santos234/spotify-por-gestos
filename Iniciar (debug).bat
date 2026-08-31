@echo off
rem Mesmo programa, COM a janela de video e mostrando dedo por dedo o que a
rem camera reconhece. Use este para calibrar os limiares do src/config.py.
rem
rem E o unico atalho que abre janela, de proposito.
call "%~dp0_executar.bat" --debug %*
