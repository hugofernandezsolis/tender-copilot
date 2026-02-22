# tender-copilot

Módulo sencillo para acceder y descargar licitaciones del Gobierno de Canarias.

## Uso rápido

```bash
python canarias_tenders.py --dry-run --max 10
```

Muestra por consola las licitaciones/documentos detectados en formato JSON.

```bash
python canarias_tenders.py --output-dir downloads/canarias --max 10
```

Descarga los documentos detectados en la carpeta indicada.

## Opciones CLI

- `--source-url`: URL de origen a analizar (por defecto el perfil del contratante de Canarias).
- `--output-dir`: carpeta destino de las descargas.
- `--max`: máximo de documentos a procesar.
- `--dry-run`: no descarga, solo lista resultados.

## Test

```bash
python -m pytest -q
```
