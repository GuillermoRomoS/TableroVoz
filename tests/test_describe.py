"""Tests de describe.py — formato audio oficial ONCE (chess-notation.md, Requirements 5.1-5.3).

Nota sobre el sample de test: la tarea 3 menciona `libro_diag23_p44`, pero ese
diagrama vive en `samples/holdout/` y R31 lo reserva para el Sprint 3. Para no
tocar el hold-out durante el desarrollo usamos `libro_diag1_p15` (disponible en
`samples/`) como caso principal contra el texto de audio oficial de la ONCE, más
los diagramas digitales tablero1..tablero5 como casos deterministas adicionales.
"""
from __future__ import annotations

import chess
import pytest

from tablerovoz.describe import describe
from tests.conftest import read_fen

# Texto de audio oficial de la ONCE para el Diagrama 1 (pág. 15),
# copiado de samples/REFERENCIA_ONCE.txt. La imagen coincide con este texto
# (meta.json: "Coincide con el texto de audio.").
DIAG1_WHITE = (
    "Blancas: Rey en E2, Dama en A4, Torres en C1 y H1, Alfil en B5, "
    "Caballos en C3 y F3, Peones en A2, B2, D2, F2, G2 y H2."
)
DIAG1_BLACK = (
    "Negras: Rey en E8, Dama en D7, Torres en A8 y H8, Alfiles en F8 y G4, "
    "Caballo en C6, Peones en A7, B7, C5, E7, F7, G7 y H7."
)


def test_diag1_compact_matches_once_reference():
    fen = read_fen("libro_diag1_p15")
    result = describe(fen, mode="compact")
    expected = f"{DIAG1_WHITE} {DIAG1_BLACK} Juegan blancas."
    assert result == expected


def test_diag1_spoken_is_three_lines():
    fen = read_fen("libro_diag1_p15")
    result = describe(fen, mode="spoken")
    assert result == f"{DIAG1_WHITE}\n{DIAG1_BLACK}\nJuegan blancas."


def test_order_is_king_queen_rook_bishop_knight_pawn():
    # R17: alfiles ANTES que caballos en audio.
    fen = read_fen("libro_diag1_p15")
    white = describe(fen, mode="spoken").splitlines()[0]
    assert white.index("Alfil") < white.index("Caballo")
    assert white.index("Rey") < white.index("Dama") < white.index("Torre")


def test_singular_plural_and_omit_empty_types():
    fen = read_fen("libro_diag1_p15")
    white = describe(fen, mode="spoken").splitlines()[0]
    black = describe(fen, mode="spoken").splitlines()[1]
    assert "Alfil en B5" in white  # singular
    assert "Torres en C1 y H1" in white  # plural con "y"
    assert "Caballo en C6" in black  # singular (una sola pieza)
    # tablero4 no tiene damas ni torres para blancas -> se omiten esos tipos.
    t4 = describe(read_fen("tablero4_digital"), mode="spoken").splitlines()[0]
    assert "Dama" not in t4 and "Torre" not in t4 and "Alfil" not in t4


def test_squares_sorted_column_then_rank():
    # R19: dentro del tipo, columna A→H y luego fila ascendente.
    # Peones blancos de diag1: A2, B2, D2, F2, G2, H2.
    fen = read_fen("libro_diag1_p15")
    white = describe(fen, mode="spoken").splitlines()[0]
    assert "Peones en A2, B2, D2, F2, G2 y H2." in white


def test_turn_from_fen_black():
    fen = read_fen("libro_diag1_p15") + " b - - 0 1"
    assert describe(fen, mode="compact").endswith("Juegan negras.")


def test_turn_defaults_to_white_for_position_only_fen():
    assert describe(read_fen("tablero1_digital"), mode="compact").endswith(
        "Juegan blancas."
    )


def test_deterministic():
    # R22: misma posición -> misma salida.
    fen = read_fen("tablero5_digital")
    assert describe(fen, mode="compact") == describe(fen, mode="compact")
    assert describe(fen, mode="ranks") == describe(fen, mode="ranks")


def test_ranks_mode_lists_rows_8_to_1():
    fen = read_fen("tablero4_digital")
    result = describe(fen, mode="ranks")
    lines = result.splitlines()
    assert lines[0].startswith("Fila 8:")
    assert lines[7].startswith("Fila 1:")
    assert lines[-1] in ("Juegan blancas.", "Juegan negras.")
    # tablero4: rey negro en a8.
    assert "A8 rey negro" in lines[0]


def test_doubts_announced_with_text():
    # R05: las dudas se dicen con texto.
    fen = read_fen("tablero1_digital")
    one = describe(fen, mode="compact", doubts=["e4"])
    assert one.endswith("Casilla dudosa: E4.")
    many = describe(fen, mode="compact", doubts=["e4", "a1"])
    assert many.endswith("Casillas dudosas: A1 y E4.")


def test_invalid_mode_raises():
    with pytest.raises(ValueError):
        describe(read_fen("tablero1_digital"), mode="nope")


@pytest.mark.parametrize(
    "stem",
    [
        "tablero1_digital",
        "tablero2_digital",
        "tablero3_digital",
        "tablero4_digital",
        "tablero5_digital",
        "libro_diag1_p15",
        "libro_diag2_p17",
        "libro_diag5_p24",
    ],
)
def test_all_samples_describe_without_error_and_end_with_turn(stem):
    result = describe(read_fen(stem), mode="compact")
    assert result.startswith("Blancas: ")
    assert " Negras: " in result
    assert result.endswith("Juegan blancas.")
