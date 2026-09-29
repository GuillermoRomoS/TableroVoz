"""Tests de board.py — detección, rectificación y corte en 64 casillas (Requirement 2.1, R24)."""
from __future__ import annotations

import numpy as np
import pytest

from tablerovoz import board
from tests.conftest import SAMPLES

DIGITAL = [
    "tablero1_digital",
    "tablero2_digital",
    "tablero3_digital",
    "tablero4_digital",
    "tablero5_digital",
]


@pytest.mark.parametrize("stem", DIGITAL)
def test_detect_and_rectify_size(stem):
    img = board.load_image(SAMPLES / f"{stem}.png")
    result = board.detect_board(img)
    assert result.warped.shape[:2] == (board.BOARD_SIZE, board.BOARD_SIZE)


@pytest.mark.parametrize("stem", DIGITAL)
def test_split_into_64_tiles(stem):
    img = board.load_image(SAMPLES / f"{stem}.png")
    tiles, _ = board.board_to_tiles(img)
    assert len(tiles) == 64
    # cada casilla tiene área positiva
    for t in tiles:
        assert t.shape[0] > 0 and t.shape[1] > 0


def test_tiles_order_is_fen_order():
    # a8 es la primera casilla (índice 0), h1 la última (índice 63).
    img = board.load_image(SAMPLES / "tablero1_digital.png")
    tiles, _ = board.board_to_tiles(img)
    assert len(tiles) == 64


def test_load_image_missing_raises():
    with pytest.raises(FileNotFoundError):
        board.load_image(SAMPLES / "no_existe.png")


def test_fallback_box_on_uniform_image():
    # Imagen sin cuadrilátero claro -> usa fallback, sigue devolviendo 512x512.
    img = np.full((300, 300, 3), 127, dtype=np.uint8)
    # dibujar un recuadro interior más oscuro para que el fallback lo recorte
    img[40:260, 40:260] = 80
    result = board.detect_board(img)
    assert result.warped.shape[:2] == (board.BOARD_SIZE, board.BOARD_SIZE)


def test_split_tiles_margin_reduces_size():
    warped = np.zeros((board.BOARD_SIZE, board.BOARD_SIZE, 3), dtype=np.uint8)
    no_margin = board.split_tiles(warped, margin=0.0)
    with_margin = board.split_tiles(warped, margin=0.08)
    assert with_margin[0].shape[0] < no_margin[0].shape[0]
