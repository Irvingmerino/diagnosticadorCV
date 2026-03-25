# Diagnosticador ATS de CV (Claude API)

Programa en Python para revisar un CV en **PDF**, **Word** o **imagen**, y generar una recomendación breve de mejora para filtros **ATS**.

## Características
- Diagnóstico rápido y conciso (respuesta breve).
- Soporte para `pdf`, `docx/doc`, `png/jpg/jpeg/tiff/bmp/webp`.
- Prompt orientado a optimización ATS: palabras clave, logros medibles y formato compatible.

## Requisitos
- Python 3.10+
- Dependencias:

```bash
pip install -r requirements.txt
```

> Para OCR en imágenes, necesitas tener **Tesseract** instalado en el sistema.

## Uso
1. Exporta tu API key de Claude (Anthropic):

```bash
export ANTHROPIC_API_KEY="TU_API_KEY"
```

2. Ejecuta el análisis:

```bash
python cv_ats_analyzer.py /ruta/a/tu_cv.pdf
```

Opciones útiles:

```bash
python cv_ats_analyzer.py cv.docx --model claude-3-5-sonnet-latest --max-chars 12000
```

## Nota sobre velocidad y longitud
El script limita el texto del CV con `--max-chars` para mantener tiempos de respuesta rápidos y un diagnóstico corto.
