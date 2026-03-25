#!/usr/bin/env python3
"""Analizador rápido de CV para recomendaciones ATS usando Claude API."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import requests


def _error(msg: str) -> None:
    print(f"Error: {msg}", file=sys.stderr)


def extract_text_from_pdf(path: Path) -> str:
    try:
        import pdfplumber
    except ImportError as exc:
        raise RuntimeError("Falta dependencia 'pdfplumber'. Instálala con pip install -r requirements.txt") from exc

    pages = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            txt = page.extract_text() or ""
            if txt.strip():
                pages.append(txt)
    return "\n".join(pages).strip()


def extract_text_from_docx(path: Path) -> str:
    try:
        from docx import Document
    except ImportError as exc:
        raise RuntimeError("Falta dependencia 'python-docx'. Instálala con pip install -r requirements.txt") from exc

    doc = Document(path)
    lines = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
    return "\n".join(lines).strip()


def extract_text_from_image(path: Path) -> str:
    try:
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError(
            "Faltan dependencias OCR ('pytesseract' y 'Pillow'). Instálalas con pip install -r requirements.txt"
        ) from exc

    image = Image.open(path)
    return pytesseract.image_to_string(image, lang="spa+eng").strip()


def extract_text(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(path)
    if ext in {".docx", ".doc"}:
        # .doc requiere conversión previa, pero intentamos de todos modos.
        return extract_text_from_docx(path)
    if ext in {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}:
        return extract_text_from_image(path)
    raise ValueError("Formato no soportado. Usa PDF, DOCX/DOC o imagen (png/jpg/jpeg/tiff/bmp/webp).")


def build_prompt(cv_text: str) -> str:
    return (
        "Analiza el siguiente CV y devuelve un diagnóstico breve para mejorar su rendimiento en filtros ATS. "
        "Responde en español, con máximo 6 viñetas, y una sección final 'Versión optimizada sugerida' "
        "de no más de 120 palabras. Prioriza claridad, palabras clave, logros medibles y formato ATS.\n\n"
        f"CV:\n{cv_text}"
    )


def query_claude(api_key: str, model: str, prompt: str, max_tokens: int = 500) -> str:
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": 0.2,
        "messages": [{"role": "user", "content": prompt}],
    }

    response = requests.post(url, headers=headers, json=payload, timeout=45)
    response.raise_for_status()
    data = response.json()

    parts = data.get("content", [])
    text_chunks = [p.get("text", "") for p in parts if p.get("type") == "text"]
    result = "\n".join(text_chunks).strip()
    if not result:
        raise RuntimeError("Claude no devolvió texto en la respuesta.")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Analiza CV y sugiere mejoras ATS con Claude API")
    parser.add_argument("archivo", type=Path, help="Ruta del CV (PDF, DOCX/DOC o imagen)")
    parser.add_argument(
        "--model",
        default="claude-3-5-sonnet-latest",
        help="Modelo de Claude a usar (default: claude-3-5-sonnet-latest)",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("ANTHROPIC_API_KEY"),
        help="API key de Anthropic (si no se pasa, usa ANTHROPIC_API_KEY)",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=12000,
        help="Máximo de caracteres extraídos del CV para acelerar el diagnóstico",
    )
    args = parser.parse_args()

    if not args.archivo.exists():
        _error(f"No existe el archivo: {args.archivo}")
        return 1

    if not args.api_key:
        _error("Debes definir la API key con --api-key o la variable ANTHROPIC_API_KEY")
        return 1

    try:
        text = extract_text(args.archivo)
    except Exception as exc:
        _error(f"No se pudo leer el archivo: {exc}")
        return 1

    if not text:
        _error("No se pudo extraer texto del CV. Verifica formato/calidad del archivo.")
        return 1

    text = text[: args.max_chars]
    prompt = build_prompt(text)

    try:
        analysis = query_claude(args.api_key, args.model, prompt)
    except requests.HTTPError as exc:
        _error(f"Error HTTP en Claude API: {exc} - {exc.response.text if exc.response is not None else ''}")
        return 1
    except Exception as exc:
        _error(f"Falló el análisis: {exc}")
        return 1

    print("\n=== Diagnóstico ATS (rápido) ===\n")
    print(analysis)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
