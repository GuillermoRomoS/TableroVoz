"""Utilidades compartidas para los tests: cargar los samples oficiales de la ONCE."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "samples"


def read_fen(stem: str) -> str:
    """Lee el FEN (solo el campo de posición) de samples/<stem>.fen."""
    text = (SAMPLES / f"{stem}.fen").read_text(encoding="utf-8").strip()
    return text.split()[0]


def read_braille(stem: str) -> str:
    """Lee el bloque braille oficial de samples/<stem>.braille.txt, sin líneas vacías al final."""
    return (SAMPLES / f"{stem}.braille.txt").read_text(encoding="utf-8").strip("\n")
