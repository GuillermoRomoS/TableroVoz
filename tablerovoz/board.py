"""Detección y rectificación del tablero + corte en 64 casillas (Requirement 2.1, R24-R26).

Pipeline (R24):
  imagen -> escala de grises -> umbral adaptativo -> contornos -> mayor cuadrilátero
  ≈ cuadrado -> warpPerspective a 512x512 -> 64 casillas.
Si no se encuentra un cuadrilátero claro, fallback por proyecciones (bordes casi
uniformes) para recortar el área del tablero.

Todas las funciones trabajan sobre arrays de OpenCV (BGR o gris) y son deterministas.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

BOARD_SIZE = 512  # lado del tablero rectificado
INNER_MARGIN = 0.08  # margen interior por casilla al recortar (R24)


@dataclass(frozen=True)
class BoardResult:
    """Resultado de localizar el tablero."""

    warped: np.ndarray  # imagen BGR rectificada BOARD_SIZE x BOARD_SIZE
    found_quad: bool  # True si se detectó por cuadrilátero; False si se usó fallback
    quad: np.ndarray | None  # 4 esquinas en la imagen original (o None)


def load_image(path: str | Path) -> np.ndarray:
    """Carga una imagen en BGR. Lanza FileNotFoundError si no existe."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    data = np.fromfile(str(path), dtype=np.uint8)  # soporta rutas con acentos en Windows
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"No se pudo decodificar la imagen: {path}")
    return img


def _order_corners(pts: np.ndarray) -> np.ndarray:
    """Ordena 4 puntos como [top-left, top-right, bottom-right, bottom-left]."""
    pts = pts.reshape(4, 2).astype(np.float32)
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1).reshape(-1)
    return np.array(
        [
            pts[np.argmin(s)],  # TL: menor x+y
            pts[np.argmin(diff)],  # TR: menor y-x
            pts[np.argmax(s)],  # BR: mayor x+y
            pts[np.argmax(diff)],  # BL: mayor y-x
        ],
        dtype=np.float32,
    )


def _largest_square_quad(gray: np.ndarray) -> np.ndarray | None:
    """Busca el mayor cuadrilátero ≈ cuadrado usando umbral adaptativo + contornos."""
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 31, 5
    )
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    h, w = gray.shape[:2]
    img_area = float(h * w)
    best: np.ndarray | None = None
    best_area = 0.0
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 0.20 * img_area:  # el tablero ocupa buena parte de la imagen
            continue
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
        if len(approx) != 4 or not cv2.isContourConvex(approx):
            continue
        x, y, ww, hh = cv2.boundingRect(approx)
        aspect = ww / float(hh) if hh else 0
        if not (0.75 <= aspect <= 1.33):  # aproximadamente cuadrado
            continue
        if area > best_area:
            best_area = area
            best = approx
    return best


def _fallback_box(gray: np.ndarray) -> np.ndarray:
    """Recorte por proyecciones: descarta bordes casi uniformes (márgenes/coordenadas)."""
    h, w = gray.shape[:2]
    g = gray.astype(float)

    def run(is_uniform, limit) -> int:
        n = 0
        while n < limit and is_uniform(n):
            n += 1
        return n

    lim_v = h // 4
    lim_h = w // 4
    top = run(lambda i: g[i, :].std() < 6, lim_v)
    bottom = run(lambda i: g[h - 1 - i, :].std() < 6, lim_v)
    left = run(lambda i: g[:, i].std() < 6, lim_h)
    right = run(lambda i: g[:, w - 1 - i].std() < 6, lim_h)
    x0, y0, x1, y1 = left, top, w - right, h - bottom
    return np.array(
        [[x0, y0], [x1, y0], [x1, y1], [x0, y1]], dtype=np.float32
    )


def _frame_box(gray: np.ndarray) -> np.ndarray | None:
    """Marco de diagrama de libro: líneas oscuras largas (≥50 % del lado) horizontales y verticales.

    Cubre libros cuyo marco no cierra un contorno limpio (p. ej. número del diagrama pegado
    al borde). Devuelve None si no hay marco claro o no es aproximadamente cuadrado.
    """
    h, w = gray.shape[:2]
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    horiz = cv2.morphologyEx(th, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (max(3, int(w * 0.5)), 1)))
    vert = cv2.morphologyEx(th, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(3, int(h * 0.5)))))
    ys = np.where(horiz.sum(axis=1) > 0)[0]
    xs = np.where(vert.sum(axis=0) > 0)[0]
    if len(ys) < 2 or len(xs) < 2:
        return None
    x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
    bw, bh = x1 - x0, y1 - y0
    if bw < 0.5 * w or bh < 0.5 * h or not (0.8 <= bw / float(bh) <= 1.25):
        return None
    return np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], dtype=np.float32)


def detect_board(img: np.ndarray) -> BoardResult:
    """Localiza y rectifica el tablero a BOARD_SIZE x BOARD_SIZE."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    quad = _largest_square_quad(gray)
    if quad is None:
        quad = _frame_box(gray)  # libros con marco que no cierra contorno
    found = quad is not None
    if quad is None:
        quad = _fallback_box(gray)

    src = _order_corners(np.asarray(quad, dtype=np.float32))
    dst = np.array(
        [[0, 0], [BOARD_SIZE - 1, 0], [BOARD_SIZE - 1, BOARD_SIZE - 1], [0, BOARD_SIZE - 1]],
        dtype=np.float32,
    )
    matrix = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, matrix, (BOARD_SIZE, BOARD_SIZE))
    return BoardResult(warped=warped, found_quad=found, quad=src)


def split_tiles(warped: np.ndarray, margin: float = INNER_MARGIN) -> list[np.ndarray]:
    """Divide el tablero rectificado en 64 casillas, en orden a8..h8, a7..h7, ..., a1..h1.

    Cada casilla se recorta con un margen interior (R24) para evitar bordes de rejilla.
    El orden coincide con el FEN (fila 8 primero, columnas a→h).
    """
    tiles: list[np.ndarray] = []
    cell = warped.shape[0] / 8.0
    m = int(round(cell * margin))
    for row in range(8):  # 0 arriba = fila 8
        for col in range(8):  # 0 = columna a
            y0 = int(round(row * cell)) + m
            y1 = int(round((row + 1) * cell)) - m
            x0 = int(round(col * cell)) + m
            x1 = int(round((col + 1) * cell)) - m
            tiles.append(warped[y0:y1, x0:x1].copy())
    return tiles


def board_to_tiles(img: np.ndarray) -> tuple[list[np.ndarray], BoardResult]:
    """Atajo: detecta el tablero y devuelve las 64 casillas + el resultado de detección."""
    result = detect_board(img)
    return split_tiles(result.warped), result
