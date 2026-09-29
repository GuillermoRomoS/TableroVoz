"""FEN -> descripción accesible en el formato de audio oficial de la ONCE.

Reglas aplicadas (steering chess-notation.md):
- R16/R17: orden Rey, Dama, Torres, Alfiles, Caballos, Peones (alfiles ANTES que caballos).
- R18: singular/plural según cantidad; enumeración con comas y "y" antes del último; se omiten los tipos sin piezas.
- R19: casilla = columna en MAYÚSCULA + número (E2); dentro del tipo, columna A→H y luego fila ascendente.
- R20: tras Negras, siempre el turno: "Juegan blancas." / "Juegan negras."
- R22: misma posición -> misma salida (determinista).

La función es pura y determinista: no depende de estado externo.
"""
from __future__ import annotations

from typing import Iterable

import chess

# Orden de tipos para AUDIO (R17): Rey, Dama, Torres, Alfiles, Caballos, Peones.
_AUDIO_ORDER: tuple[int, ...] = (
    chess.KING,
    chess.QUEEN,
    chess.ROOK,
    chess.BISHOP,
    chess.KNIGHT,
    chess.PAWN,
)

# Nombres en español, (singular, plural).
_NAMES: dict[int, tuple[str, str]] = {
    chess.KING: ("Rey", "Reyes"),
    chess.QUEEN: ("Dama", "Damas"),
    chess.ROOK: ("Torre", "Torres"),
    chess.BISHOP: ("Alfil", "Alfiles"),
    chess.KNIGHT: ("Caballo", "Caballos"),
    chess.PAWN: ("Peón", "Peones"),
}


def _board_from_fen(fen: str) -> chess.Board:
    """Acepta un FEN completo o solo el campo de posición."""
    fen = fen.strip()
    if " " not in fen:
        fen = f"{fen} w - - 0 1"
    return chess.Board(fen)


def _square_name(square: int) -> str:
    """Nombre de casilla en formato ONCE: columna en MAYÚSCULA + fila (p. ej. 'E2')."""
    return chess.square_name(square).upper()


def _squares_for(board: chess.Board, color: bool, piece_type: int) -> list[int]:
    """Casillas de un color y tipo, ordenadas por columna A→H y luego fila ascendente (R19)."""
    squares = board.pieces(piece_type, color)
    # square index = rank*8 + file. Ordenar por (file, rank) da columna A→H, fila 1→8.
    return sorted(squares, key=lambda s: (chess.square_file(s), chess.square_rank(s)))


def _join_es(items: list[str]) -> str:
    """Enumeración en español: 'A', 'A y B', 'A, B y C' (R18)."""
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return f"{', '.join(items[:-1])} y {items[-1]}"


def _phrase_for_type(board: chess.Board, color: bool, piece_type: int) -> str | None:
    """'Torres en C1 y H1' o None si no hay piezas de ese tipo (R18)."""
    squares = _squares_for(board, color, piece_type)
    if not squares:
        return None
    singular, plural = _NAMES[piece_type]
    name = singular if len(squares) == 1 else plural
    coords = _join_es([_square_name(s) for s in squares])
    return f"{name} en {coords}"


def _side_line(board: chess.Board, color: bool) -> str:
    label = "Blancas" if color == chess.WHITE else "Negras"
    phrases = [
        p
        for pt in _AUDIO_ORDER
        if (p := _phrase_for_type(board, color, pt)) is not None
    ]
    body = ", ".join(phrases)
    return f"{label}: {body}."


def _turn_line(turn: bool) -> str:
    return "Juegan blancas." if turn == chess.WHITE else "Juegan negras."


def describe(fen: str, mode: str = "compact", doubts: Iterable[str] | None = None) -> str:
    """Devuelve la descripción accesible de una posición.

    Args:
        fen: FEN completo o solo el campo de posición. El turno se toma del FEN
             (por defecto blancas si el FEN es solo posición).
        mode: "compact" (todo seguido), "spoken" (una frase por bando y turno en
              líneas separadas, para lectura hablada) o "ranks" (recorrido por filas
              de la 8 a la 1).
        doubts: lista opcional de casillas dudosas (p. ej. ["e4"]); se anuncian con
                texto al final (R05), nunca solo con color.

    La salida es determinista: misma posición + mismo turno -> misma cadena (R22).
    """
    board = _board_from_fen(fen)
    doubt_list = sorted({d.strip().upper() for d in (doubts or []) if d.strip()})

    if mode == "ranks":
        text = _describe_ranks(board)
    elif mode == "spoken":
        text = "\n".join(
            [
                _side_line(board, chess.WHITE),
                _side_line(board, chess.BLACK),
                _turn_line(board.turn),
            ]
        )
    elif mode == "compact":
        text = " ".join(
            [
                _side_line(board, chess.WHITE),
                _side_line(board, chess.BLACK),
                _turn_line(board.turn),
            ]
        )
    else:
        raise ValueError(f"modo no reconocido: {mode!r} (usa compact, spoken o ranks)")

    if doubt_list:
        text += " " + _doubts_line(doubt_list)
    return text


def _doubts_line(doubts: list[str]) -> str:
    coords = _join_es(doubts)
    if len(doubts) == 1:
        return f"Casilla dudosa: {coords}."
    return f"Casillas dudosas: {coords}."


def _describe_ranks(board: chess.Board) -> str:
    """Recorrido por filas, de la 8 a la 1; en cada fila, columnas A→H (R05/modo por filas)."""
    lines: list[str] = []
    for rank in range(7, -1, -1):  # fila 8 (índice 7) hasta fila 1 (índice 0)
        cells: list[str] = []
        for file in range(8):  # A→H
            square = chess.square(file, rank)
            piece = board.piece_at(square)
            if piece is None:
                continue
            color = "blanco" if piece.color == chess.WHITE else "negro"
            singular, _ = _NAMES[piece.piece_type]
            cells.append(f"{_square_name(square)} {singular.lower()} {color}")
        if cells:
            lines.append(f"Fila {rank + 1}: " + _join_es(cells) + ".")
        else:
            lines.append(f"Fila {rank + 1}: vacía.")
    lines.append(_turn_line(board.turn))
    return "\n".join(lines)
