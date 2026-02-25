# Windows — setup.bat
# Tworzy środowisko wirtualne i instaluje zależności.
# Uruchom jeden raz przed pierwszym użyciem aplikacji.
#
# Windows — setup.bat
# Creates a virtual environment and installs dependencies.
# Run once before the first use of the application.

@echo off
echo [BID] Tworzenie srodowiska wirtualnego (venv)...
python -m venv .venv

echo [BID] Aktywacja srodowiska...
call .venv\Scripts\activate.bat

echo [BID] Instalacja zaleznosci z requirements.txt...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo [BID] Gotowe! Aby uruchomic aplikacje:
echo   .venv\Scripts\activate.bat
echo   python main.py
echo.
pause
