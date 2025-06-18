# Gemini2MD

Conversor de chats Gemini (Google) a Markdown, preservando formato y estructura.  
*(Gemini chat to Markdown converter, preserving formatting and structure)*

## Características principales / Features
- Convierte chats Gemini a Markdown bien formateado  
  *Converts Gemini chats to well-formatted Markdown*
- Opción de salida HTML  
  *Optional HTML output*
- Preserva la estructura de la conversación  
  *Preserves conversation structure*

## Installation
```bash
pip install -r requirements.txt
```

## System Requirements (Linux)

```bash
# Essential
sudo apt-get install pandoc

# For development
sudo apt-get install python3-venv python3-dev

# Optional
sudo apt-get install git build-essential
```

## Input Requirements

This tool processes HTML files saved with [SingleFile](https://www.getsinglefile.com/) Chrome extension.

### How to prepare input:
1. Install SingleFile extension
2. Save Gemini conversation as `.html` using SingleFile
3. Process with:
```bash
python gemini2md.py conversation.html output.md
```

## Usage
```bash
# Procesar carpeta input/ (por defecto)
poetry run python main.py

# Procesar carpeta específica
poetry run python main.py mi_carpeta_conversaciones

# Ayuda
poetry run python main.py --help
```

## Examples
See `examples/` directory for valid input/output samples.

## ⚠️ Privacidad

Los archivos incluidos en `example/` son muestras sintéticas. Al usar tus propias conversaciones:
1. Revisa que no contengan información personal
2. Considera usar el modo incógnito al exportar
3. El script no filtra automáticamente datos sensibles

## Desarrollo

Este proyecto usa Poetry para gestión de dependencias. Para configurar:

```bash
poetry install
poetry run python main.py --help  # Probar instalación
```

## Licencia
MIT