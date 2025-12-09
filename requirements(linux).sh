#!/bin/bash
# Título (solo para mostrar en terminal)
echo "=== Descargar videos de YouTube ==="

# Actualizar pip
python3 -m pip install --upgrade pip

# Instalar o actualizar dependencias
pip install --upgrade Flask
pip install --upgrade waitress
pip install --upgrade gunicorn
pip install --upgrade daemon
pip install --upgrade yt-dlp

# Verificar versión de Python
python3 --version

# Esperar entrada del usuario antes de cerrar
# read -p "Presiona Enter para salir..."
