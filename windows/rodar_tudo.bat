@echo off
chcp 65001 >nul
echo ============================================
1: echo   Mission Brasil -- Anti-Fraud SENTINELA
2: echo   Iniciando API + Dashboard...
echo ============================================
echo.

:: Verifica ambiente virtual
if not exist "venv\Scripts\activate.bat" (
    echo [ERRO] Ambiente virtual não encontrado. 
    echo Execute iniciar.bat primeiro para instalar dependências.
    pause
    exit /b 1
)

:: Sobe a API em uma janela separada
echo [1/2] Iniciando API Anti-Fraude (Porta 8000)...
start "SENTINELA -- API" cmd /k "venv\Scripts\activate.bat && uvicorn app:app --reload --port 8000"

:: Aguarda 3 segundos para a API subir
timeout /t 3 /nobreak >nul

:: Sobe o Dashboard em outra janela separada
echo [2/2] Iniciando Dashboard SENTINELA (Streamlit)...
start "SENTINELA -- Dashboard" cmd /k "venv\Scripts\activate.bat && streamlit run dashboard.py"

echo.
echo ============================================
echo   Tudo pronto! 
echo   API: http://localhost:8000/docs
echo   Dashboard: Abrirá automaticamente no navegador.
echo ============================================
echo.
