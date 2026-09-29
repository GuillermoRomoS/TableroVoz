"""Tests de validate.py — reglas del ajedrez (Requirement 3.1/3.2, steering R28)."""
from __future__ import annotations

import pytest

from tablerovoz.validate import validate
from tests.conftest import read_fen

VALID_SAMPLES = [
    "tablero1_digital",
    "tablero2_digital",
    "tablero3_digital",
    "tablero4_digital",
    "tablero5_digital",
    "libro_diag1_p15",
    "libro_diag2_p17",
    "libro_diag5_p24",
]


@pytest.mark.parametrize("stem", VALID_SAMPLES)
def test_official_samples_are_valid(stem):
    result = validate(read_fen(stem))
    assert result.ok, result.warnings
    assert result.warnings == []
    assert result.doubts == []


def test_missing_king_flagged():
    # Sin reyes: falta el rey de ambos bandos.
    result = validate("8/8/8/8/8/8/8/8")
    assert not result.ok
    assert any("rey de las blancas" in w for w in result.warnings)
    assert any("rey de las negras" in w for w in result.warnings)


def test_two_white_kings_flagged_and_squares_doubtful():
    # Dos reyes blancos (e1, e2) y un rey negro (e8).
    result = validate("4k3/8/8/8/8/8/4K3/4K3")
    assert not result.ok
    assert any("2 reyes de las blancas" in w for w in result.warnings)
    assert "e1" in result.doubts and "e2" in result.doubts


def test_too_many_pawns_flagged():
    # 9 peones blancos en la fila 2 (a2..h2) + uno en a3.
    result = validate("4k3/8/8/8/8/P7/PPPPPPPP/4K3")
    assert not result.ok
    assert any("9 peones blancas" in w for w in result.warnings)


def test_pawn_on_back_rank_flagged():
    # Peón blanco en a1 (fila 1) y peón negro en h8 (fila 8): imposibles.
    result = validate("4k2P/8/8/8/8/8/8/P3K3")
    assert not result.ok
    assert any("A1" in w and "filas 1 u 8" in w for w in result.warnings)
    assert any("H8" in w and "filas 1 u 8" in w for w in result.warnings)
    assert "a1" in result.doubts and "h8" in result.doubts


def test_too_many_pieces_flagged():
    # 17 piezas blancas: rey + dama + 15 peones repartidos (fila 2 llena + 7 en fila 3).
    fen = "4k3/8/8/8/8/PPPPPPP1/PPPPPPPP/Q3K3"
    result = validate(fen)
    assert not result.ok
    assert any("piezas blancas" in w and "16" in w for w in result.warnings)


def test_deterministic():
    fen = read_fen("tablero5_digital")
    assert validate(fen) == validate(fen)


def test_result_shape():
    result = validate(read_fen("tablero1_digital"))
    assert isinstance(result.warnings, list)
    assert isinstance(result.doubts, list)
    assert isinstance(result.ok, bool)
