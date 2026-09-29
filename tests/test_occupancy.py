"""Tests de occupancy.py — vacía/ocupada relativa al tablero (Cambio 1, R26)."""
from __future__ import annotations

from pathlib import Path

import pytest

from tablerovoz import board, occupancy, tiles

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "samples"

DEV = [
    "tablero1_digital", "tablero2_digital", "tablero3_digital",
    "tablero4_digital", "tablero5_digital",
    "libro_diag1_p15", "libro_diag2_p17", "libro_diag5_p24",
]


def test_is_light_square_a8_light_a1_dark():
    # a8 = índice 0 (clara); a1 = índice 56 (oscura).
    assert occupancy.is_light_square(0) is True
    assert occupancy.is_light_square(56) is False
    # h1 = índice 63 (clara)
    assert occupancy.is_light_square(63) is True


def test_estimate_background_light_gt_dark():
    img = board.load_image(SAMPLES / "tablero1_digital.png")
    tl, _ = board.board_to_tiles(img)
    bg = occupancy.estimate_background(tl)
    assert bg.light_bg > bg.dark_bg


def test_occupancy_returns_64_bools():
    img = board.load_image(SAMPLES / "tablero1_digital.png")
    tl, _ = board.board_to_tiles(img)
    occ = occupancy.occupancy(tl)
    assert len(occ) == 64
    assert all(isinstance(v, bool) for v in occ)


def test_occupancy_reasonable_on_empty_heavy_board():
    # tablero4: solo 2 reyes + 11 peones = 13 ocupadas; el resto vacías.
    img = board.load_image(SAMPLES / "tablero4_digital.png")
    tl, _ = board.board_to_tiles(img)
    occ = occupancy.occupancy(tl)
    truth = [lbl != "empty" for lbl in tiles.fen_to_labels(
        (SAMPLES / "tablero4_digital.fen").read_text(encoding="utf-8").strip().split()[0]
    )]
    agree = sum(1 for a, b in zip(truth, occ) if a == b)
    assert agree >= 55  # bastante mejor que el azar; el resto lo afina el clasificador


@pytest.mark.parametrize("stem", DEV)
def test_occupancy_beats_naive_all_empty(stem):
    # Debe acertar bastante mejor que "todo vacío".
    fen = (SAMPLES / f"{stem}.fen").read_text(encoding="utf-8").strip().split()[0]
    truth = [lbl != "empty" for lbl in tiles.fen_to_labels(fen)]
    img = board.load_image(SAMPLES / f"{stem}.png")
    tl, _ = board.board_to_tiles(img)
    occ = occupancy.occupancy(tl)
    agree = sum(1 for a, b in zip(truth, occ) if a == b)
    all_empty_agree = sum(1 for t in truth if not t)
    assert agree >= all_empty_agree  # nunca peor que asumir todo vacío
