"""Extracción de características de casilla + clasificador de 13 clases (Requirement 2.2/2.3, R26/R27).

Clases: empty, wK, wQ, wR, wB, wN, wP, bK, bQ, bR, bB, bN, bP.

- Características: casilla 32x32 en gris normalizada + HOG (contornos de la pieza).
- "Vacía vs. ocupada" (R26): además del clasificador, se compara con plantillas de
  casilla vacía clara/oscura (soporta rayado) por baja varianza / alta similitud.
- Clasificador ligero (scikit-learn) que entrena en < 1 min (R-tech).

Funciones puras salvo el propio modelo entrenado, que se guarda/carga con joblib.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

TILE_SIZE = 32
CLASSES = (
    "empty",
    "wK", "wQ", "wR", "wB", "wN", "wP",
    "bK", "bQ", "bR", "bB", "bN", "bP",
)

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL_PATH = ROOT / "models" / "tiles.joblib"


def to_gray_tile(tile: np.ndarray) -> np.ndarray:
    """Normaliza una casilla a gris TILE_SIZE x TILE_SIZE en float [0,1]."""
    if tile.ndim == 3:
        gray = cv2.cvtColor(tile, cv2.COLOR_BGR2GRAY)
    else:
        gray = tile
    resized = cv2.resize(gray, (TILE_SIZE, TILE_SIZE), interpolation=cv2.INTER_AREA)
    return resized.astype(np.float32) / 255.0


def _hog(gray01: np.ndarray) -> np.ndarray:
    """HOG sencillo: magnitudes de gradiente por celda 8x8 -> vector."""
    gx = cv2.Sobel(gray01, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray01, cv2.CV_32F, 0, 1, ksize=3)
    mag = np.sqrt(gx * gx + gy * gy)
    # promediar en bloques 8x8 -> 4x4 = 16 valores
    blocks = mag.reshape(4, 8, 4, 8).mean(axis=(1, 3))
    return blocks.reshape(-1)


def _foreground_features(g: np.ndarray) -> np.ndarray:
    """Características que resaltan la pieza (objeto central) frente al fondo de la casilla.

    Una pieza ocupa el centro y contrasta con las esquinas (que son fondo de casilla).
    Estas señales separan pieza-vs-vacía de forma robusta (R26) y ayudan con el color
    de la pieza (blanca clara / negra oscura).
    """
    center = g[8:24, 8:24]
    corners = np.concatenate([
        g[0:8, 0:8].reshape(-1), g[0:8, 24:32].reshape(-1),
        g[24:32, 0:8].reshape(-1), g[24:32, 24:32].reshape(-1),
    ])
    bg = float(corners.mean())  # nivel del fondo de la casilla
    # máscara de "tinta" = píxeles que se salen del fondo (más oscuros o más claros)
    ink = np.abs(g - bg)
    fg_frac = float((ink > 0.20).mean())  # cuánta casilla difiere del fondo
    return np.array([
        center.mean(), center.std(),
        bg, fg_frac,
        float(center.mean() - bg),  # signo: pieza clara (>0) vs oscura (<0)
        float(ink.mean()), float(ink.max()),
    ], dtype=np.float32)


def features(tile: np.ndarray) -> np.ndarray:
    """Vector de características de una casilla: píxeles 32x32 + HOG + stats + señales de pieza."""
    g = to_gray_tile(tile)
    pix = g.reshape(-1)  # 1024
    hog = _hog(g)  # 16
    stats = np.array([g.mean(), g.std(), g.min(), g.max()], dtype=np.float32)  # 4
    fg = _foreground_features(g)  # 7
    return np.concatenate([pix, hog, stats, fg]).astype(np.float32)


def is_empty_by_template(tile: np.ndarray, std_threshold: float = 0.06) -> bool:
    """Heurística R26: una casilla vacía tiene baja variación interior (aunque esté rayada).

    Se recorta el centro para ignorar la rejilla y se mide la desviación típica.
    """
    g = to_gray_tile(tile)
    c = g[6:26, 6:26]  # centro
    return bool(c.std() < std_threshold)


@dataclass
class TileClassifier:
    """Envoltura del clasificador de casillas. Guarda/carga con joblib."""

    model: object  # sklearn estimator con predict/predict_proba
    classes: tuple[str, ...] = CLASSES

    def predict(self, tile: np.ndarray) -> tuple[str, float]:
        """Devuelve (clase, confianza) para una casilla."""
        x = features(tile).reshape(1, -1)
        proba = self.model.predict_proba(x)[0]
        idx = int(np.argmax(proba))
        label = self.model.classes_[idx]
        return str(label), float(proba[idx])

    def predict_board(
        self, tiles: list[np.ndarray], occupied: list[bool] | None = None
    ) -> tuple[list[str], list[float]]:
        """Clasifica las 64 casillas; devuelve (labels, confidences) en orden FEN.

        Si se pasa `occupied` (Cambio 1: vacía/ocupada relativa al tablero), se usa como
        compuerta: donde dice vacía -> "empty"; donde dice ocupada -> la MEJOR clase de
        pieza (se ignora la probabilidad de "empty" del clasificador).
        """
        X = np.stack([features(t) for t in tiles])
        proba = self.model.predict_proba(X)
        classes = list(self.model.classes_)

        if occupied is None:
            idx = proba.argmax(axis=1)
            labels = [str(classes[i]) for i in idx]
            confs = [float(proba[r, i]) for r, i in enumerate(idx)]
            return labels, confs

        empty_col = classes.index("empty") if "empty" in classes else None
        labels: list[str] = []
        confs: list[float] = []
        for r in range(len(tiles)):
            if not occupied[r]:
                labels.append("empty")
                # confianza = prob. de vacía si existe, si no 1 - max pieza
                confs.append(float(proba[r, empty_col]) if empty_col is not None else 1.0)
                continue
            row = proba[r].copy()
            if empty_col is not None:
                row[empty_col] = -1.0  # forzar una PIEZA
            i = int(row.argmax())
            labels.append(str(classes[i]))
            confs.append(float(proba[r, i]))
        return labels, confs

    def save(self, path: str | Path = DEFAULT_MODEL_PATH) -> Path:
        import joblib

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, path)
        return path

    @classmethod
    def load(cls, path: str | Path = DEFAULT_MODEL_PATH) -> "TileClassifier":
        import joblib

        model = joblib.load(Path(path))
        return cls(model=model)


# --------------------------------------------------------------------------- #
# Conversión entre etiquetas de casilla y FEN
# --------------------------------------------------------------------------- #
_LABEL_TO_FEN = {
    "wK": "K", "wQ": "Q", "wR": "R", "wB": "B", "wN": "N", "wP": "P",
    "bK": "k", "bQ": "q", "bR": "r", "bB": "b", "bN": "n", "bP": "p",
}


def labels_to_fen(labels: list[str]) -> str:
    """Convierte 64 etiquetas (orden a8..h1) al campo de posición de un FEN."""
    if len(labels) != 64:
        raise ValueError("se esperan 64 etiquetas")
    rows: list[str] = []
    for r in range(8):
        row = labels[r * 8:(r + 1) * 8]
        fen_row = ""
        empties = 0
        for label in row:
            if label == "empty":
                empties += 1
            else:
                if empties:
                    fen_row += str(empties)
                    empties = 0
                fen_row += _LABEL_TO_FEN.get(label, "?")
        if empties:
            fen_row += str(empties)
        rows.append(fen_row)
    return "/".join(rows)


def fen_to_labels(fen: str) -> list[str]:
    """Convierte el campo de posición de un FEN a 64 etiquetas (orden a8..h1)."""
    import chess

    board = chess.Board(None)
    board.set_board_fen(fen.strip().split()[0])
    labels: list[str] = []
    for row in range(8):  # fila 8 arriba
        rank = 7 - row
        for col in range(8):
            piece = board.piece_at(chess.square(col, rank))
            if piece is None:
                labels.append("empty")
            else:
                color = "w" if piece.color else "b"
                labels.append(f"{color}{piece.symbol().upper()}")
    return labels
