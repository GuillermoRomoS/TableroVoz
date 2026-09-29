"""Tests de tiles.py — características, conversión FEN<->etiquetas (Requirement 2.2)."""
from __future__ import annotations

import numpy as np
import pytest

from tablerovoz import tiles
from tests.conftest import read_fen


def test_features_length_stable():
    tile = np.zeros((40, 40, 3), dtype=np.uint8)
    f = tiles.features(tile)
    # 1024 (32x32) + 16 (hog) + 4 (stats) + 7 (señales de pieza)
    assert f.shape == (1024 + 16 + 4 + 7,)


def test_labels_fen_roundtrip():
    fen = read_fen("tablero1_digital")
    labels = tiles.fen_to_labels(fen)
    assert len(labels) == 64
    assert tiles.labels_to_fen(labels) == fen


@pytest.mark.parametrize(
    "stem",
    ["tablero1_digital", "tablero2_digital", "tablero3_digital",
     "tablero4_digital", "tablero5_digital"],
)
def test_roundtrip_all_samples(stem):
    fen = read_fen(stem)
    assert tiles.labels_to_fen(tiles.fen_to_labels(fen)) == fen


def test_fen_to_labels_order_a8_first():
    # tablero4: k7/... -> a8 es rey negro, resto de la fila 8 vacío.
    labels = tiles.fen_to_labels(read_fen("tablero4_digital"))
    assert labels[0] == "bK"
    assert labels[1:8] == ["empty"] * 7


def test_labels_to_fen_bad_length():
    with pytest.raises(ValueError):
        tiles.labels_to_fen(["empty"] * 10)


def test_is_empty_by_template_on_uniform_tile():
    tile = np.full((32, 32, 3), 200, dtype=np.uint8)
    assert tiles.is_empty_by_template(tile) is True
    noisy = np.random.default_rng(0).integers(0, 255, (32, 32, 3), dtype=np.uint8)
    assert tiles.is_empty_by_template(noisy) is False
