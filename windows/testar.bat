@echo off
chcp 65001 >nul
echo.
echo ============================================
echo   Mission Brasil -- Rodando testes
echo ============================================
echo.

:: Ativa ambiente virtual
if not exist "venv\Scripts\activate.bat" (
    echo [ERRO] Ambiente virtual nao encontrado.
    echo Execute iniciar.bat primeiro.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo [1/2] Rodando testes unitarios...
python test_api.py
echo.

echo [2/2] Rodando teste de integracao end-to-end...
python integration_test.py
echo.

pause
