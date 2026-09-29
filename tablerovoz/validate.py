"""Validación ajedrecística de una posición (Requirement 3, steering R28).

Comprobaciones (R28):
- Exactamente un rey por bando.
- ≤ 8 peones por bando.
- Ningún peón en las filas 1 u 8.
- ≤ 16 piezas por bando.

Si una comprobación falla, se marcan como dudosas las casillas implicadas y se
devuelve un aviso en texto para anunciarlo al final de la descripción (R05, 3.2).
La función es pura y determinista: mismos datos -> mismo resultado.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import chess


@dataclass(frozen=True)
class ValidationResult:
    """Resultado de validar una posición.

    Attributes:
        ok: True si no se detectó ningún problema.
        warnings: mensajes en texto para anunciar al usuario (R05/3.2).
        doubts: casillas dudosas en minúscula ("e1"), ordenadas y sin duplicados.
    """

    ok: bool
    warnings: list[str] = field(default_factory=list)
    doubts: list[str] = field(default_factory=list)


def _board_from_fen(fen: str) -> chess.Board:
    fen = fen.strip()
    if " " not in fen:
        fen = f"{fen} w - - 0 1"
    # Construimos el tablero solo desde el campo de posición para no fallar por
    # un rey ausente (Board admite posiciones no estándar al fijar las casillas).
    board = chess.Board(None)
    board.set_board_fen(fen.split()[0])
    return board


def _side_name(color: bool) -> str:
    return "blancas" if color == chess.WHITE else "negras"


def validate(fen: str) -> ValidationResult:
    """Valida una posición dada por su FEN y devuelve avisos y casillas dudosas."""
    board = _board_from_fen(fen)
    warnings: list[str] = []
    doubts: set[str] = set()

    for color in (chess.WHITE, chess.BLACK):
        side = _side_name(color)

        # Un rey por bando.
        kings = list(board.pieces(chess.KING, color))
        if len(kings) == 0:
            warnings.append(f"No se ve el rey de las {side}.")
        elif len(kings) > 1:
            warnings.append(f"Hay {len(kings)} reyes de las {side}; debería haber uno.")
            doubts.update(chess.square_name(s) for s in kings)

        # ≤ 8 peones por bando.
        pawns = list(board.pieces(chess.PAWN, color))
        if len(pawns) > 8:
            warnings.append(
                f"Hay {len(pawns)} peones {side}; el máximo es 8."
            )
            doubts.update(chess.square_name(s) for s in pawns)

        # ≤ 16 piezas por bando.
        count = sum(
            1 for piece in board.piece_map().values() if piece.color == color
        )
        if count > 16:
            warnings.append(f"Hay {count} piezas {side}; el máximo es 16.")

    # Ningún peón en filas 1 u 8 (cualquier color).
    for square, piece in board.piece_map().items():
        if piece.piece_type == chess.PAWN:
            rank = chess.square_rank(square) + 1  # 1..8
            if rank in (1, 8):
                name = chess.square_name(square)
                side = _side_name(piece.color)
                warnings.append(
                    f"Hay un peón {side} en {name.upper()}; no puede haber peones en las filas 1 u 8."
                )
                doubts.add(name)

    return ValidationResult(
        ok=not warnings,
        warnings=warnings,
        doubts=sorted(doubts),
    )
