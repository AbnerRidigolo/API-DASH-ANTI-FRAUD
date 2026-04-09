@echo off
chcp 65001 >nul
echo.
echo ============================================
echo   Mission Brasil -- Anti-Fraud API
echo   Setup Windows
echo ============================================
echo.

:: Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado.
    echo Baixe em: https://python.org/downloads
    echo Marque "Add Python to PATH" durante a instalacao.
    pause
    exit /b 1
)

echo [OK] Python encontrado:
python --version
echo.

:: Cria ambiente virtual se nao existir
if not exist "venv\" (
    echo [1/4] Criando ambiente virtual...
    python -m venv venv
    echo [OK] Ambiente virtual criado.
) else (
    echo [1/4] Ambiente virtual ja existe, pulando...
)
echo.

:: Ativa ambiente virtual
echo [2/4] Ativando ambiente virtual...
call venv\Scripts\activate.bat
echo [OK] Ambiente ativado.
echo.

:: Instala dependencias
echo [3/4] Instalando dependencias...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias.
    pause
    exit /b 1
)
echo [OK] Dependencias instaladas.
echo.

:: Sobe o servidor
echo [4/4] Subindo servidor...
echo.
echo ============================================
echo   API rodando em:
echo   http://localhost:8000
echo.
echo   Documentacao (Swagger):
echo   http://localhost:8000/docs
echo.
echo   Para parar: Ctrl+C
echo ============================================
echo.

uvicorn app:app --reload --port 8000

pause
