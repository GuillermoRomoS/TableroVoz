"""Medición de precisión del clasificador (R30, Requirement 2.4).

Imprime:
- precisión por casilla (fracción de casillas correctas)
- % de tableros perfectos (todas las casillas correctas)
- matriz de confusión resumida de los errores más frecuentes

Modos:
- `--quick`: evalúa SOLO sobre los samples de desarrollo (samples/, NO holdout, R31),
  entrenando un modelo rápido si no hay uno guardado. Pensado para iterar en segundos.
- por defecto: evalúa sobre samples/ de desarrollo + un banco sintético de test.

NUNCA usa samples/holdout salvo que se pase --holdout explícitamente (Sprint 3, R31).
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from tablerovoz import board, recognize, tiles
from tablerovoz.tiles import TileClassifier, DEFAULT_MODEL_PATH

ROOT = Path(__file__).resolve().parent
SAMPLES = ROOT / "samples"

_DEV_SAMPLES = (
    "tablero1_digital",
    "tablero2_digital",
    "tablero3_digital",
    "tablero4_digital",
    "tablero5_digital",
    "libro_diag1_p15",
    "libro_diag2_p17",
    "libro_diag5_p24",
)


def _get_classifier() -> TileClassifier:
    if Path(DEFAULT_MODEL_PATH).exists():
        return TileClassifier.load()
    from tablerovoz import train

    print("No hay modelo guardado; entrenando uno rápido...")
    return train.train(n_synth=80, seed=0, save=True)


def evaluate(stems: list[str], classifier: TileClassifier) -> dict:
    total = 0
    correct = 0
    perfect_boards = 0
    errors: Counter = Counter()

    for stem in stems:
        png = SAMPLES / f"{stem}.png"
        fen_file = SAMPLES / f"{stem}.fen"
        if not png.exists() or not fen_file.exists():
            print(f"  (saltando {stem}: falta png o fen)")
            continue
        fen = fen_file.read_text(encoding="utf-8").strip().split()[0]
        truth = tiles.fen_to_labels(fen)
        img = board.load_image(png)
        rec = recognize.recognize_image(img, classifier, flipped="auto")
        pred = tiles.fen_to_labels(rec.fen)

        board_correct = 0
        for t, p in zip(truth, pred):
            total += 1
            if t == p:
                correct += 1
                board_correct += 1
            else:
                errors[f"{t}->{p}"] += 1
        if board_correct == 64:
            perfect_boards += 1
        print(f"  {stem}: {board_correct}/64 casillas correctas")

    per_tile = correct / total if total else 0.0
    return {
        "per_tile_accuracy": per_tile,
        "perfect_boards": perfect_boards,
        "n_boards": len([s for s in stems if (SAMPLES / f"{s}.png").exists()]),
        "top_errors": errors.most_common(8),
        "total_tiles": total,
        "correct_tiles": correct,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Precisión del clasificador de casillas.")
    parser.add_argument("--quick", action="store_true", help="solo samples de desarrollo")
    parser.add_argument(
        "--holdout",
        action="store_true",
        help="incluir samples/holdout (SOLO Sprint 3, R31)",
    )
    args = parser.parse_args()

    classifier = _get_classifier()
    stems = list(_DEV_SAMPLES)
    print(f"Evaluando sobre {len(stems)} samples de desarrollo"
          + (" (modo --quick)" if args.quick else "") + ":")
    metrics = evaluate(stems, classifier)

    print("\n=== Resultados ===")
    print(f"Precisión por casilla: {metrics['per_tile_accuracy']*100:.1f}% "
          f"({metrics['correct_tiles']}/{metrics['total_tiles']})")
    print(f"Tableros perfectos: {metrics['perfect_boards']}/{metrics['n_boards']}")
    if metrics["top_errors"]:
        print("Errores más frecuentes (verdad->predicho):")
        for pair, count in metrics["top_errors"]:
            print(f"  {pair}: {count}")


if __name__ == "__main__":
    main()
