"""Pipeline de reconocimiento: imagen -> FEN + confianza + dudas (une board + tiles + validate).

Es la pieza que comparten cli.py y api.py. No contiene lógica de presentación.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from tablerovoz import board, occupancy, tiles
from tablerovoz.tiles import TileClassifier
from tablerovoz.validate import ValidationResult, validate

# Umbral de confianza por debajo del cual una casilla se marca como dudosa.
LOW_CONF = 0.55


@dataclass(frozen=True)
class Recognition:
    fen: str  # campo de posición
    confidence: dict[str, float]  # por casilla ("e4" -> 0.9)
    doubts: list[str]  # casillas dudosas (baja confianza o validación)
    validation: ValidationResult
    found_quad: bool
    flipped: bool = False  # True si se rotó 180° por orientación detectada


def _looks_flipped(labels: list[str]) -> bool:
    """Heurística de orientación: ¿está el tablero girado (negras abajo)?

    `labels` está en orden a8..h1 (fila 8 = índice 0..7). La "altura" de una casilla
    es su fila: fila 8 arriba. En orientación normal los peones/rey blancos están
    abajo (filas bajas) y los negros arriba. Si de media los blancos están MÁS ARRIBA
    que los negros (o el rey blanco cae en la mitad superior), el tablero está girado.
    """
    def rank_of(index: int) -> int:
        return 8 - (index // 8)  # fila 1..8

    white_ranks = [rank_of(i) for i, l in enumerate(labels) if l == "wP"]
    black_ranks = [rank_of(i) for i, l in enumerate(labels) if l == "bP"]

    # Señal principal (la más fiable): altura media de los peones. En orientación
    # normal los peones blancos están abajo (filas bajas) y los negros arriba.
    # Solo se rota si hay suficientes peones y la separación es CLARA (>1 fila), para
    # no girar por ruido de clasificación en diagramas difíciles.
    if len(white_ranks) >= 3 and len(black_ranks) >= 3:
        gap = (sum(white_ranks) / len(white_ranks)) - (sum(black_ranks) / len(black_ranks))
        return gap > 1.0

    # Sin peones de ambos colores, usar la posición de los reyes como respaldo.
    wk = [rank_of(i) for i, l in enumerate(labels) if l == "wK"]
    bk = [rank_of(i) for i, l in enumerate(labels) if l == "bK"]
    if wk and bk:
        return wk[0] > bk[0]  # rey blanco más arriba que el negro -> girado
    if wk:
        return wk[0] >= 5  # rey blanco en la mitad superior
    if bk:
        return bk[0] <= 4
    return False


def _rotate_labels_180(labels: list[str]) -> list[str]:
    """Rota la posición 180°: la casilla i pasa a la 63-i."""
    return list(reversed(labels))


def _square_names() -> list[str]:
    import chess

    names: list[str] = []
    for row in range(8):  # fila 8 arriba
        rank = 7 - row
        for col in range(8):
            names.append(chess.square_name(chess.square(col, rank)))
    return names


def recognize_image(
    img: np.ndarray, classifier: TileClassifier, flipped: str | bool = "auto"
) -> Recognition:
    """Reconoce una posición a partir de una imagen BGR ya cargada.

    Args:
        flipped: orientación del tablero:
            "auto" (por defecto) -> detectar y rotar 180° si parece girado (negras abajo);
            True / "si" / "yes"  -> forzar rotación 180°;
            False / "no"          -> asumir blancas abajo, sin rotar.
    """
    tile_list, board_result = board.board_to_tiles(img)
    # Cambio 1: compuerta vacía/ocupada relativa a ESTE tablero.
    occupied = occupancy.occupancy(tile_list)
    labels, confs = classifier.predict_board(tile_list, occupied=occupied)

    # Orientación. Medido en samples reales, el auto-giro por altura de peones es
    # ruidoso en diagramas difíciles (giraba de más en libro impreso, que SIEMPRE va
    # con blancas abajo). Decisión: NO rotar automáticamente por defecto; se confía en
    # el parámetro "Tablero girado" y, cuando los peones sugieren giro, se AVISA.
    suggests_flip = _looks_flipped(labels)
    mode = str(flipped).lower() if not isinstance(flipped, bool) else ("si" if flipped else "no")
    if mode in ("si", "yes", "true"):
        do_flip = True
    else:  # "no" y "auto" -> no rotar (auto solo avisa)
        do_flip = False

    if do_flip:
        labels = _rotate_labels_180(labels)
        confs = list(reversed(confs))

    fen = tiles.labels_to_fen(labels)

    names = _square_names()
    confidence = {names[i]: confs[i] for i in range(64)}
    doubts = {names[i] for i in range(64) if confs[i] < LOW_CONF}

    result = validate(fen)
    doubts.update(result.doubts)
    warnings = list(result.warnings)
    # Aviso de posible giro: peones que lo sugieren, o un desequilibrio imposible de
    # piezas (síntoma frecuente de tablero al revés). Solo se avisa; no se rota.
    if mode == "auto" and not do_flip and (suggests_flip or not result.ok):
        warnings.append(
            "El diagrama podría estar girado. Si el resultado no cuadra, "
            'activa "Tablero girado".'
        )

    result = ValidationResult(ok=result.ok, warnings=warnings, doubts=result.doubts)
    return Recognition(
        fen=fen,
        confidence=confidence,
        doubts=sorted(doubts),
        validation=result,
        found_quad=board_result.found_quad,
        flipped=do_flip,
    )


def recognize_path(
    path: str | Path, classifier: TileClassifier, flipped: str | bool = "auto"
) -> Recognition:
    """Reconoce una posición a partir de la ruta de una imagen."""
    img = board.load_image(path)
    return recognize_image(img, classifier, flipped=flipped)
