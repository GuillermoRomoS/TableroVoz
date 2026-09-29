"""FEN -> salida braille en el formato oficial ONCE / Ebrai.

Reglas aplicadas (steering braille.md, basado en samples/REFERENCIA_ONCE.txt):
- R08: la salida debe coincidir carácter a carácter con samples/tablero*_digital.braille.txt.
- R09: estructura `Tablero:` / `Blancas: …` / `Negras: …` y, opcionalmente, `Juegan blancas.`/`Juegan negras.`
- R10: pieza = letra en tinta R, D, T, C, A (sin signo braille); peones SIN letra.
- R11: casilla = columna en tinta a–h + fila en braille en posición baja.
- R12: orden braille R, D, T, C, A, peones (caballos ANTES que alfiles); dentro del tipo,
       columna a→h y luego fila ascendente.
- R13: un espacio entre piezas.

Los sample .braille.txt NO incluyen la línea de turno (solo 3 líneas), así que la línea
`Juegan…` es opcional y por defecto NO se emite, para reproducir los samples exactamente.
"""
from __future__ import annotations

import chess

# Números de fila en braille, posición baja (R11). Índice 0 -> fila 1.
_ROW_BRAILLE: dict[int, str] = {
    1: "⠂",
    2: "⠆",
    3: "⠒",
    4: "⠲",
    5: "⠢",
    6: "⠖",
    7: "⠶",
    8: "⠦",
}

# Orden de tipos para BRAILLE (R12): Rey, Dama, Torres, Caballos, Alfiles, Peones.
_BRAILLE_ORDER: tuple[int, ...] = (
    chess.KING,
    chess.QUEEN,
    chess.ROOK,
    chess.KNIGHT,
    chess.BISHOP,
    chess.PAWN,
)

# Letra en tinta de cada pieza (R10). El peón NO lleva letra.
_LETTER: dict[int, str] = {
    chess.KING: "R",
    chess.QUEEN: "D",
    chess.ROOK: "T",
    chess.KNIGHT: "C",
    chess.BISHOP: "A",
    chess.PAWN: "",
}


def _board_from_fen(fen: str) -> chess.Board:
    """Acepta un FEN completo o solo el campo de posición."""
    fen = fen.strip()
    if " " not in fen:
        fen = f"{fen} w - - 0 1"
    return chess.Board(fen)


def _square_braille(square: int) -> str:
    """Casilla en formato braille: columna en tinta a–h + fila braille (p. ej. 'e⠲')."""
    file_letter = chess.FILE_NAMES[chess.square_file(square)]  # 'a'..'h'
    row = chess.square_rank(square) + 1  # 1..8
    return f"{file_letter}{_ROW_BRAILLE[row]}"


def _squares_for(board: chess.Board, color: bool, piece_type: int) -> list[int]:
    """Casillas de un color y tipo, ordenadas columna a→h y luego fila ascendente (R12)."""
    squares = board.pieces(piece_type, color)
    return sorted(squares, key=lambda s: (chess.square_file(s), chess.square_rank(s)))


def _token(piece_type: int, square: int) -> str:
    """Token braille de una pieza: letra (o vacío para peón) + casilla."""
    return f"{_LETTER[piece_type]}{_square_braille(square)}"


def _side_line(board: chess.Board, color: bool) -> str:
    label = "Blancas" if color == chess.WHITE else "Negras"
    tokens: list[str] = []
    for piece_type in _BRAILLE_ORDER:
        for square in _squares_for(board, color, piece_type):
            tokens.append(_token(piece_type, square))
    return f"{label}: " + " ".join(tokens)


def to_braille(fen: str, include_turn: bool = False) -> str:
    """Convierte un FEN a la salida braille oficial de la ONCE.

    Args:
        fen: FEN completo o solo el campo de posición.
        include_turn: si True, añade la línea `Juegan blancas.`/`Juegan negras.`
                      (R09). Por defecto False para reproducir carácter a carácter
                      los samples oficiales, que no la incluyen (R08).

    Returns:
        Texto con las líneas `Tablero:`, `Blancas: …`, `Negras: …` separadas por '\\n'.
    """
    board = _board_from_fen(fen)
    lines = [
        "Tablero:",
        _side_line(board, chess.WHITE),
        _side_line(board, chess.BLACK),
    ]
    if include_turn:
        lines.append("Juegan blancas." if board.turn == chess.WHITE else "Juegan negras.")
    return "\n".join(lines)
