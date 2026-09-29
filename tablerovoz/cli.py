"""CLI de TableroVoz: imagen -> braille ONCE + audio ONCE + FEN.

Uso:
    python -m tablerovoz.cli <imagen> [--turn w|b] [--model ruta.joblib]

Imprime, en este orden:
    1. El FEN reconocido (con el turno).
    2. La salida braille oficial ONCE.
    3. La salida de audio oficial ONCE.
    4. Avisos de validación y casillas dudosas, si los hay.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tablerovoz import braille, describe
from tablerovoz.recognize import recognize_path
from tablerovoz.tiles import DEFAULT_MODEL_PATH, TileClassifier


def _turn_to_fen_field(turn: str) -> str:
    return "w" if turn.lower().startswith("w") else "b"


def run(
    image: str,
    turn: str = "w",
    model_path: str | Path = DEFAULT_MODEL_PATH,
    flipped: str = "auto",
) -> int:
    if not Path(image).exists():
        print(f"No encuentro la imagen: {image}", file=sys.stderr)
        return 2
    if not Path(model_path).exists():
        print(
            f"No hay modelo entrenado en {model_path}. "
            "Ejecuta primero: python -m tablerovoz.train",
            file=sys.stderr,
        )
        return 3

    classifier = TileClassifier.load(model_path)
    rec = recognize_path(image, classifier, flipped=flipped)

    turn_field = _turn_to_fen_field(turn)
    full_fen = f"{rec.fen} {turn_field} - - 0 1"

    if rec.flipped:
        print("(Tablero girado detectado: posición rotada 180°.)", file=sys.stderr)
    print("=== FEN ===")
    print(full_fen)
    print("\n=== Braille (ONCE / Ebrai) ===")
    print(braille.to_braille(full_fen, include_turn=True))
    print("\n=== Audio (ONCE) ===")
    print(describe.describe(full_fen, mode="compact", doubts=rec.doubts))

    if not rec.found_quad:
        print(
            "\nAviso: no detecté un tablero claro; usé un recorte aproximado. "
            "Si el resultado no cuadra, recorta la imagen al diagrama.",
            file=sys.stderr,
        )
    if rec.validation.warnings:
        print("\n=== Avisos de validación ===", file=sys.stderr)
        for w in rec.validation.warnings:
            print(f"- {w}", file=sys.stderr)
    if rec.doubts:
        print(f"\nCasillas dudosas: {', '.join(rec.doubts)}", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tablerovoz.cli",
        description="Reconoce un diagrama de ajedrez y produce braille ONCE, audio ONCE y FEN.",
    )
    parser.add_argument("image", help="ruta de la imagen del diagrama (PNG/JPG)")
    parser.add_argument(
        "--turn",
        default="w",
        choices=["w", "b", "white", "black", "blancas", "negras"],
        help="turno: w (blancas, por defecto) o b (negras)",
    )
    parser.add_argument("--model", default=str(DEFAULT_MODEL_PATH), help="ruta del modelo")
    parser.add_argument(
        "--flipped",
        default="auto",
        choices=["auto", "si", "no"],
        help="tablero girado: auto (avisa, no rota), si (rota 180°), no",
    )
    args = parser.parse_args(argv)
    return run(args.image, turn=args.turn, model_path=args.model, flipped=args.flipped)


if __name__ == "__main__":
    raise SystemExit(main())
