# Gemini2MD

Tool to convert Gemini conversations to Markdown/HTML

## Features
- Converts Gemini chats to well-formatted Markdown
- Optional HTML output
- Preserves conversation structure

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

## Development

This project uses Poetry for dependency management. To set up:

```bash
poetry install
poetry run python main.py --help  # Test installation
```

## License
MIT