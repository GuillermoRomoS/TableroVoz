"""Tests de shape.py — separación de forma (6 clases) y color por relleno oscuro (Cambio 2)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from tablerovoz import board, occupancy, shape, tiles

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "samples"


def test_silhouette_shape_and_binary():
    img = board.load_image(SAMPLES / "tablero1_digital.png")
    tl, _ = board.board_to_tiles(img)
    bg = occupancy.estimate_background(tl)
    sil = shape.silhouette(tl[0], bg.light_bg, bg.dark_bg, occupancy.is_light_square(0))
    assert sil.shape == (shape.SHAPE_SIZE, shape.SHAPE_SIZE)
    assert set(np.unique(sil)).issubset({0.0, 1.0})


def test_shape_features_length():
    sil = np.zeros((shape.SHAPE_SIZE, shape.SHAPE_SIZE), dtype=np.float32)
    f = shape.shape_features(sil)
    # pix + col_profile + row_profile + fill
    assert f.shape == (shape.SHAPE_SIZE * shape.SHAPE_SIZE + shape.SHAPE_SIZE * 2 + 1,)


def test_color_from_dark_fill_rule():
    assert shape.color_from_dark_fill(0.9, threshold=0.78) == "b"
    assert shape.color_from_dark_fill(0.2, threshold=0.78) == "w"


def test_dark_fill_black_higher_than_white():
    # En un tablero real, el relleno oscuro medio de las negras > el de las blancas.
    import chess

    stem = "tablero1_digital"
    fen = (SAMPLES / f"{stem}.fen").read_text(encoding="utf-8").strip().split()[0]
    truth = tiles.fen_to_labels(fen)
    img = board.load_image(SAMPLES / f"{stem}.png")
    tl, _ = board.board_to_tiles(img)
    bg = occupancy.estimate_background(tl)
    w, b = [], []
    for i, lbl in enumerate(truth):
        if lbl == "empty":
            continue
        sq_light = occupancy.is_light_square(i)
        sil = shape.silhouette(tl[i], bg.light_bg, bg.dark_bg, sq_light)
        r = shape.dark_fill_ratio(tl[i], sil, bg.light_bg, bg.dark_bg)
        (w if lbl[0] == "w" else b).append(r)
    assert np.mean(b) > np.mean(w)


@pytest.mark.skipif(
    not (ROOT / "models" / "shape.joblib").exists(),
    reason="requiere models/shape.joblib (entrenar con --only-shape)",
)
def test_shape_classifier_predicts_piece_label():
    sc = shape.ShapeClassifier.load()
    img = board.load_image(SAMPLES / "tablero1_digital.png")
    tl, _ = board.board_to_tiles(img)
    bg = occupancy.estimate_background(tl)
    # casilla 0 = a8 = torre negra en tablero1 (r...)
    label, conf = sc.predict_piece(tl[0], bg.light_bg, bg.dark_bg, occupancy.is_light_square(0))
    assert label[0] in ("w", "b")
    assert label[1] in shape.SHAPE_CLASSES
    assert 0.0 <= conf <= 1.0
