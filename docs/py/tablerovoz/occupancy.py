"""Vacía vs. ocupada RELATIVA a cada tablero (Cambio 1, R26).

En vez de un umbral absoluto, se estima el fondo de ESTE tablero:
- mediana del anillo exterior de las casillas CLARAS -> fondo claro
- mediana del anillo exterior de las casillas OSCURAS -> fondo oscuro (soporta rayado)

Una casilla se marca OCUPADA si su anillo central se aleja de su propio fondo
(claro u oscuro según su color de casilla) más de un umbral relativo.

Trabaja sobre las 64 casillas en orden FEN (a8..h1) que produce board.split_tiles.
Funciones puras y deterministas.
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

TILE = 32


@dataclass(frozen=True)
class BoardBackground:
    """Fondo estimado del tablero, en gris [0,1]."""

    light_bg: float
    dark_bg: float


def _gray(tile: np.ndarray) -> np.ndarray:
    if tile.ndim == 3:
        g = cv2.cvtColor(tile, cv2.COLOR_BGR2GRAY)
    else:
        g = tile
    return cv2.resize(g, (TILE, TILE), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0


def _outer_ring(g: np.ndarray) -> np.ndarray:
    """Píxeles del borde (anillo exterior) de la casilla: fondo aunque haya pieza en el centro."""
    mask = np.ones((TILE, TILE), dtype=bool)
    mask[6:26, 6:26] = False  # quitar el centro (donde estaría la pieza)
    return g[mask]


def _center_ring(g: np.ndarray) -> np.ndarray:
    """Región central donde se dibuja la pieza."""
    return g[8:24, 8:24]


def is_light_square(index: int) -> bool:
    """True si la casilla `index` (orden FEN a8..h1) es clara.

    a8 es clara. index = row*8 + col, row 0 = fila 8.
    Color de casilla: clara si (file + rank) es impar, con file=col, rank=7-row.
    """
    row, col = divmod(index, 8)
    rank = 7 - row
    return (col + rank) % 2 == 1


def estimate_background(tiles: list[np.ndarray]) -> BoardBackground:
    """Estima el fondo claro y oscuro del tablero con la mediana del anillo exterior.

    Usa TODAS las casillas de cada color (aunque algunas tengan pieza: el anillo
    exterior sigue siendo fondo), lo que da una estimación robusta incluido el rayado.
    """
    light_vals: list[float] = []
    dark_vals: list[float] = []
    for i, tile in enumerate(tiles):
        ring = _outer_ring(_gray(tile))
        med = float(np.median(ring))
        if is_light_square(i):
            light_vals.append(med)
        else:
            dark_vals.append(med)
    light_bg = float(np.median(light_vals)) if light_vals else 1.0
    dark_bg = float(np.median(dark_vals)) if dark_vals else 0.0
    return BoardBackground(light_bg=light_bg, dark_bg=dark_bg)


def occupancy(
    tiles: list[np.ndarray],
    bg: BoardBackground | None = None,
    rel_threshold: float = 0.16,
    frac_threshold: float = 0.06,
) -> list[bool]:
    """Devuelve, por casilla, True si está OCUPADA (relativo al fondo del tablero).

    Combina dos señales para ser robusto ante casillas oscuras rayadas (libro):
    1. Global: el centro se aleja del fondo del tablero de su propio color.
    2. Local: el centro se aleja del anillo exterior de la PROPIA casilla. En una
       casilla vacía (aunque esté rayada), centro y borde comparten la misma textura,
       así que su diferencia de nivel medio es pequeña; una pieza rompe esa igualdad.

    Se marca ocupada si AMBAS señales coinciden, lo que reduce los falsos positivos
    del rayado sin perder piezas reales.
    """
    if bg is None:
        bg = estimate_background(tiles)
    result: list[bool] = []
    lo = min(bg.light_bg, bg.dark_bg)
    hi = max(bg.light_bg, bg.dark_bg)
    for i, tile in enumerate(tiles):
        g = _gray(tile)
        base = bg.light_bg if is_light_square(i) else bg.dark_bg
        center = _center_ring(g)

        # "Tinta" = píxeles del centro que:
        #  (a) se alejan del fondo de su propia casilla, o
        #  (b) caen fuera de la banda de grises del tablero [dark_bg, light_bg].
        # (b) capta piezas blancas (más claras que el fondo oscuro / con contorno
        # negro) y negras (más oscuras que el fondo claro) aunque el contraste con
        # su propia casilla sea bajo.
        dev_own = np.abs(center - base) > rel_threshold
        out_band = (center < lo - rel_threshold) | (center > hi + rel_threshold)
        ink = (dev_own | out_band).astype(np.uint8)

        # El rayado del libro son líneas finas: desaparecen con una apertura
        # morfológica (erosión+dilatación). Una pieza es una mancha conexa que
        # sobrevive. Medimos la masa que queda tras quitar las líneas finas.
        opened = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        solid_frac = float(opened.mean())
        result.append(solid_frac > frac_threshold)
    return result
