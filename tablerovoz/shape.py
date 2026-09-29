"""Cambio 2: separar FORMA y COLOR de la pieza.

- FORMA: clasificador de 6 clases (K, Q, R, B, N, P) sobre la SILUETA binarizada y
  centrada de la pieza. La silueta es invariante al color, así que piezas blancas y
  negras del mismo tipo comparten datos de entrenamiento.
- COLOR: se decide por la PROPORCIÓN de relleno oscuro dentro de la silueta. Una pieza
  blanca es clara por dentro con contorno oscuro (poco relleno oscuro); una negra está
  rellena de oscuro (mucho relleno oscuro).

Esto ataca la confusión de color del clasificador de 13 clases (bP->wP, wP->bP).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

SHAPE_SIZE = 40  # silueta normalizada
SHAPE_CLASSES = ("K", "Q", "R", "B", "N", "P")

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SHAPE_MODEL = ROOT / "models" / "shape.joblib"


def _gray01(tile: np.ndarray) -> np.ndarray:
    if tile.ndim == 3:
        g = cv2.cvtColor(tile, cv2.COLOR_BGR2GRAY)
    else:
        g = tile
    return cv2.resize(g, (64, 64), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0


def silhouette(tile: np.ndarray, light_bg: float, dark_bg: float, square_is_light: bool) -> np.ndarray:
    """Silueta binaria (0/1) de la pieza, centrada y normalizada a SHAPE_SIZE.

    La pieza = píxeles que se apartan del fondo de su casilla (contorno oscuro y/o
    cuerpo, sea blanca o negra). Se recorta al bounding box de la silueta y se centra,
    para que la forma no dependa de dónde caiga la pieza dentro de la casilla.
    """
    g = _gray01(tile)
    base = light_bg if square_is_light else dark_bg
    lo = min(light_bg, dark_bg)
    hi = max(light_bg, dark_bg)
    # "tinta" de la pieza: se aparta del fondo propio o cae fuera de la banda del tablero.
    ink = ((np.abs(g - base) > 0.16) | (g < lo - 0.16) | (g > hi + 0.16)).astype(np.uint8)
    # quitar el ruido fino (rayado) y rellenar la figura.
    ink = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    ink = cv2.morphologyEx(ink, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))

    ys, xs = np.where(ink > 0)
    canvas = np.zeros((SHAPE_SIZE, SHAPE_SIZE), dtype=np.float32)
    if len(xs) < 5:
        return canvas
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    crop = ink[y0:y1 + 1, x0:x1 + 1].astype(np.float32)
    # escalar manteniendo proporción a un cuadrado SHAPE_SIZE con margen.
    h, w = crop.shape
    scale = (SHAPE_SIZE - 6) / max(h, w)
    nh, nw = max(1, int(round(h * scale))), max(1, int(round(w * scale)))
    resized = cv2.resize(crop, (nw, nh), interpolation=cv2.INTER_AREA)
    oy, ox = (SHAPE_SIZE - nh) // 2, (SHAPE_SIZE - nw) // 2
    canvas[oy:oy + nh, ox:ox + nw] = resized
    return (canvas > 0.5).astype(np.float32)


def shape_features(sil: np.ndarray) -> np.ndarray:
    """Características de forma sobre la silueta: píxeles + perfiles de proyección."""
    pix = sil.reshape(-1)  # SHAPE_SIZE^2
    col_profile = sil.mean(axis=0)  # ancho por columna
    row_profile = sil.mean(axis=1)  # alto por fila
    fill = np.array([sil.mean()], dtype=np.float32)
    return np.concatenate([pix, col_profile, row_profile, fill]).astype(np.float32)


def dark_fill_ratio(
    tile: np.ndarray, sil: np.ndarray, light_bg: float, dark_bg: float
) -> float:
    """Proporción de relleno OSCURO dentro de la silueta (para decidir el color).

    Se remuestrea la casilla al tamaño de la silueta y se mide, dentro de la máscara,
    qué fracción de píxeles es oscura (por debajo del punto medio entre ambos fondos).
    """
    g = cv2.resize(
        _gray01(tile), (SHAPE_SIZE, SHAPE_SIZE), interpolation=cv2.INTER_AREA
    )
    # Erosionar la máscara para quedarnos con el CUERPO (interior), no el contorno:
    # el contorno es oscuro en ambos colores y confunde la medida.
    body = cv2.erode(sil.astype(np.uint8), np.ones((3, 3), np.uint8), iterations=1)
    mask = body > 0
    if mask.sum() < 5:
        mask = sil > 0.5
    if mask.sum() < 5:
        return 0.0
    # "oscuro" = cercano al fondo oscuro del tablero (no al punto medio): así el
    # interior claro de una pieza blanca NO cuenta como oscuro.
    dark_level = dark_bg + 0.20 * (light_bg - dark_bg)
    dark = (g < dark_level) & mask
    return float(dark.sum()) / float(mask.sum())


def color_from_dark_fill(ratio: float, threshold: float = 0.5) -> str:
    """'b' (negra) si el cuerpo está mayormente relleno de oscuro; 'w' si no."""
    return "b" if ratio >= threshold else "w"


@dataclass
class ShapeClassifier:
    """Clasificador de forma (6 clases) + regla de color por relleno oscuro."""

    model: object
    color_threshold: float = 0.78  # calibrado sobre samples de desarrollo
    classes: tuple[str, ...] = SHAPE_CLASSES

    def predict_piece(
        self,
        tile: np.ndarray,
        light_bg: float,
        dark_bg: float,
        square_is_light: bool,
    ) -> tuple[str, float]:
        """Devuelve (label 'wK'.., confianza de forma) para una casilla ocupada."""
        sil = silhouette(tile, light_bg, dark_bg, square_is_light)
        x = shape_features(sil).reshape(1, -1)
        proba = self.model.predict_proba(x)[0]
        i = int(np.argmax(proba))
        shape = str(self.model.classes_[i])
        conf = float(proba[i])
        ratio = dark_fill_ratio(tile, sil, light_bg, dark_bg)
        color = color_from_dark_fill(ratio, self.color_threshold)
        return f"{color}{shape}", conf

    def save(self, path: str | Path = DEFAULT_SHAPE_MODEL) -> Path:
        import joblib

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": self.model, "color_threshold": self.color_threshold}, path)
        return path

    @classmethod
    def load(cls, path: str | Path = DEFAULT_SHAPE_MODEL) -> "ShapeClassifier":
        import joblib

        data = joblib.load(Path(path))
        return cls(model=data["model"], color_threshold=data.get("color_threshold", 0.5))
