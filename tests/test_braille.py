"""Tests de braille.py — reproducción carácter a carácter de los samples ONCE.

Requirements 8.1, 8.2, 8.3 / steering R08-R13. Los samples digitales tablero1..5
traen su .braille.txt oficial; el test exige coincidencia exacta a partir del .fen.
"""
from __future__ import annotations

import chess
import pytest

from tablerovoz.braille import to_braille
from tests.conftest import read_braille, read_fen

BRAILLE_SAMPLES = [
    "tablero1_digital",
    "tablero2_digital",
    "tablero3_digital",
    "tablero4_digital",
    "tablero5_digital",
]


@pytest.mark.parametrize("stem", BRAILLE_SAMPLES)
def test_braille_matches_official_sample_exactly(stem):
    # R08: coincidencia carácter a carácter con el sample oficial.
    fen = read_fen(stem)
    expected = read_braille(stem)
    assert to_braille(fen) == expected


def test_structure_three_lines_without_turn_by_default():
    # Los samples oficiales tienen exactamente 3 líneas (sin turno).
    out = to_braille(read_fen("tablero1_digital"))
    lines = out.splitlines()
    assert len(lines) == 3
    assert lines[0] == "Tablero:"
    assert lines[1].startswith("Blancas: ")
    assert lines[2].startswith("Negras: ")


def test_pawns_have_no_letter():
    # R10: peones sin letra. En tablero4 blancas: 'Rh⠂ a⠲ b⠒ c⠆ f⠒ g⠲ h⠒'.
    out = to_braille(read_fen("tablero4_digital"))
    white = out.splitlines()[1]
    # tras el rey, los peones aparecen como columna+fila, sin 'P'.
    assert "P" not in white
    assert "a⠲" in white  # peón blanco en a4


def test_knights_before_bishops_in_braille_order():
    # R12: caballos ANTES que alfiles. En tablero1 blancas: '... Cc⠒ Cf⠒ Ac⠲ Ag⠒ ...'
    white = to_braille(read_fen("tablero1_digital")).splitlines()[1]
    assert white.index("Cc⠒") < white.index("Ac⠲")


def test_row_braille_symbols():
    # R11: fila 1 -> ⠂, fila 8 -> ⠦. Rey blanco e1 y rey negro e8 en tablero1.
    out = to_braille(read_fen("tablero1_digital"))
    assert "Re⠂" in out.splitlines()[1]  # rey blanco e1
    assert "Re⠦" in out.splitlines()[2]  # rey negro e8


def test_optional_turn_line():
    # R09: la línea de turno es opcional y se puede activar.
    out = to_braille(read_fen("tablero1_digital"), include_turn=True)
    lines = out.splitlines()
    assert len(lines) == 4
    assert lines[3] == "Juegan blancas."
    black_fen = read_fen("tablero1_digital") + " b - - 0 1"
    assert to_braille(black_fen, include_turn=True).splitlines()[3] == "Juegan negras."


def test_deterministic():
    fen = read_fen("tablero5_digital")
    assert to_braille(fen) == to_braille(fen)
