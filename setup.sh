#!/usr/bin/env bash
# Linux / macOS — setup.sh
# Tworzy środowisko wirtualne i instaluje zależności.
# Uruchom jeden raz przed pierwszym użyciem aplikacji.

set -e

echo "[BID] Tworzenie środowiska wirtualnego (venv)..."
python3 -m venv .venv

echo "[BID] Aktywacja środowiska..."
# shellcheck source=/dev/null
source .venv/bin/activate

echo "[BID] Instalacja zależności z requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

# Fedora / RHEL: tkinter jest osobnym pakietem systemowym
if command -v dnf &>/dev/null; then
    echo ""
    echo "[BID] Wykryto Fedorę/RHEL."
    echo "      Jeśli tkinter nie działa, zainstaluj go komendą systemową:"
    echo "      sudo dnf install python3-tkinter"
fi

echo ""
echo "[BID] Gotowe! / Done!"
echo "  Aktywacja środowiska / Activate:"
echo "    source .venv/bin/activate"
echo "  Uruchomienie / Run:"
echo "    python main.py"
