@echo off
title Costeo DCM - Inicialización del sistema
echo ===============================================
echo   🧾  INICIALIZANDO BASE DE DATOS DEL SISTEMA
echo ===============================================
echo.

:: Ejecutar init_db.exe para crear base y tablas si no existen
if exist init_db.exe (
    echo Ejecutando inicializador de base de datos...
    init_db.exe
) else (
    echo ⚠️  No se encontró el archivo init_db.exe
    echo Asegúrate de que esté en la misma carpeta que este script.
    pause
    exit /b
)

echo.
echo ===============================================
echo   🚀  INICIANDO SERVIDOR API COSTEO DCM
echo ===============================================
echo.

:: Ejecutar main.exe (el backend FastAPI)
if exist main.exe (
    echo Ejecutando servidor backend...
    start cmd /k main.exe
    echo.
    echo ✅ Servidor iniciado correctamente.
    echo 🌐 Puedes abrir tu aplicación o ir a:
    echo    http://127.0.0.1:8001/docs
    echo.
) else (
    echo ❌ No se encontró el archivo main.exe
    pause
    exit /b
)

echo.
echo Presiona cualquier tecla para cerrar este instalador.
pause >nul
