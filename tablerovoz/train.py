"""Entrenamiento del clasificador de casillas (R27, R-tech: < 1 min).

Fuentes de datos (todas con FEN conocido, R27):
- Diagramas sintéticos generados por synth.py (tablero + sprites de samples de
  desarrollo). Determinista por semilla.
- Recortes de casilla de los propios samples de desarrollo (tablero*_digital),
  vía board.py. NUNCA samples/holdout (R31).

Guarda el modelo en models/tiles.joblib.
"""
from __future__ import annotations

import random
from pathlib import Path

import numpy as np
from PIL import Image
from sklearn.calibration import CalibratedClassifierCV
from sklearn.svm import SVC

from tablerovoz import board, occupancy, shape, synth, tiles
from tablerovoz.shape import ShapeClassifier
from tablerovoz.tiles import TileClassifier

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "samples"

_DEV_SAMPLES = (
    "tablero1_digital",
    "tablero2_digital",
    "tablero3_digital",
    "tablero4_digital",
    "tablero5_digital",
)


def _pil_to_bgr(img: Image.Image) -> np.ndarray:
    import cv2

    arr = np.asarray(img.convert("RGB"))
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)


def _tiles_from_synth(n: int, seed: int, style: str) -> tuple[list[np.ndarray], list[str]]:
    """Genera diagramas sintéticos y devuelve (casillas, etiquetas)."""
    X: list[np.ndarray] = []
    y: list[str] = []
    sprites = synth.build_sprite_library()
    rng = random.Random(seed)
    for fen in synth.random_fens(n, seed=seed):
        img = synth.render_png(fen, size=512, style=style, sprites=sprites, rng=rng)
        bgr = _pil_to_bgr(img)
        # el sintético ya está rectificado: cortar directamente en 64.
        tile_list = board.split_tiles(bgr)
        labels = tiles.fen_to_labels(fen)
        X.extend(tile_list)
        y.extend(labels)
    return X, y


def _tiles_from_samples() -> tuple[list[np.ndarray], list[str]]:
    """Recorta casillas reales de los samples de desarrollo (con su FEN)."""
    X: list[np.ndarray] = []
    y: list[str] = []
    for stem in _DEV_SAMPLES:
        png = SAMPLES / f"{stem}.png"
        fen = (SAMPLES / f"{stem}.fen").read_text(encoding="utf-8").strip().split()[0]
        img = board.load_image(png)
        tile_list, _ = board.board_to_tiles(img)
        X.extend(tile_list)
        y.extend(tiles.fen_to_labels(fen))
    return X, y


def build_dataset(
    n_synth: int = 120, seed: int = 0, include_samples: bool = True
) -> tuple[np.ndarray, list[str]]:
    """Construye (X features, y labels) para entrenar."""
    X_tiles: list[np.ndarray] = []
    y: list[str] = []

    xs, ys = _tiles_from_synth(n_synth, seed=seed, style="digital")
    X_tiles.extend(xs)
    y.extend(ys)
    # una tanda estilo libro para robustez ante casillas rayadas
    xs, ys = _tiles_from_synth(max(n_synth // 3, 1), seed=seed + 1, style="libro")
    X_tiles.extend(xs)
    y.extend(ys)

    if include_samples:
        xs, ys = _tiles_from_samples()
        X_tiles.extend(xs)
        y.extend(ys)

    X = np.stack([tiles.features(t) for t in X_tiles])
    return X, y


def train(n_synth: int = 120, seed: int = 0, save: bool = True) -> TileClassifier:
    """Entrena el clasificador SVC y (opcional) lo guarda en models/tiles.joblib."""
    X, y = build_dataset(n_synth=n_synth, seed=seed)
    # SVC calibrado para obtener predict_proba sin la opción deprecada probability=True.
    base = SVC(kernel="rbf", C=10.0, gamma="scale", random_state=seed)
    model = CalibratedClassifierCV(base, ensemble=False, cv=3)
    model.fit(X, y)
    clf = TileClassifier(model=model)
    if save:
        path = clf.save()
        print(f"Modelo guardado en {path} (muestras={len(y)}, clases={len(set(y))}).")
    return clf


# --------------------------------------------------------------------------- #
# Cambio 2: entrenamiento del clasificador de FORMA (6 clases)
# --------------------------------------------------------------------------- #
def _shape_samples_from_board(
    tile_list: list[np.ndarray], fen: str
) -> tuple[list[np.ndarray], list[str]]:
    """De un tablero (64 casillas + FEN) extrae siluetas de las casillas OCUPADAS.

    Devuelve (features de forma, etiqueta de forma 'K'..'P'). Ignora el color: piezas
    blancas y negras del mismo tipo comparten clase.
    """
    bg = occupancy.estimate_background(tile_list)
    labels = tiles.fen_to_labels(fen)
    feats: list[np.ndarray] = []
    shapes: list[str] = []
    for i, label in enumerate(labels):
        if label == "empty":
            continue
        sq_light = occupancy.is_light_square(i)
        sil = shape.silhouette(tile_list[i], bg.light_bg, bg.dark_bg, sq_light)
        feats.append(shape.shape_features(sil))
        shapes.append(label[1])  # 'wN' -> 'N'
    return feats, shapes


def build_shape_dataset(
    n_synth: int = 120, seed: int = 0, include_samples: bool = True
) -> tuple[np.ndarray, list[str]]:
    feats: list[np.ndarray] = []
    shapes: list[str] = []
    sprites = synth.build_sprite_library()

    for style, s in (("digital", seed), ("libro", seed + 1)):
        rng = random.Random(s)
        count = n_synth if style == "digital" else max(n_synth // 3, 1)
        for fen in synth.random_fens(count, seed=s):
            img = synth.render_png(fen, size=512, style=style, sprites=sprites, rng=rng)
            tile_list = board.split_tiles(_pil_to_bgr(img))
            f, sh = _shape_samples_from_board(tile_list, fen)
            feats.extend(f)
            shapes.extend(sh)

    if include_samples:
        for stem in _DEV_SAMPLES:
            fen = (SAMPLES / f"{stem}.fen").read_text(encoding="utf-8").strip().split()[0]
            img = board.load_image(SAMPLES / f"{stem}.png")
            tile_list, _ = board.board_to_tiles(img)
            f, sh = _shape_samples_from_board(tile_list, fen)
            feats.extend(f)
            shapes.extend(sh)

    return np.stack(feats), shapes


def train_shape(n_synth: int = 120, seed: int = 0, save: bool = True) -> ShapeClassifier:
    """Entrena el clasificador de FORMA (6 clases) y lo guarda en models/shape.joblib."""
    X, y = build_shape_dataset(n_synth=n_synth, seed=seed)
    base = SVC(kernel="rbf", C=10.0, gamma="scale", random_state=seed)
    model = CalibratedClassifierCV(base, ensemble=False, cv=3)
    model.fit(X, y)
    clf = ShapeClassifier(model=model)
    if save:
        path = clf.save()
        print(f"Modelo de forma guardado en {path} (muestras={len(y)}, clases={len(set(y))}).")
    return clf


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Entrena los clasificadores de casilla.")
    parser.add_argument("--n", type=int, default=120, help="diagramas sintéticos")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--shape", action="store_true", help="entrenar también el de forma")
    parser.add_argument("--only-shape", action="store_true", help="entrenar solo el de forma")
    args = parser.parse_args()
    if not args.only_shape:
        train(n_synth=args.n, seed=args.seed)
    if args.shape or args.only_shape:
        train_shape(n_synth=args.n, seed=args.seed)
