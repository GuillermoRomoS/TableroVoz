"""Casillas resaltadas y flechas en diagramas digitales (spec `anotaciones-diagrama`, R29).

- Resaltado: color mediano del anillo de la casilla (evita la pieza) en HSV.
  Amarillo: tono 25–42, S ≥ 90 y V ≥ 180 (el verde oscuro normal tiene tono ≈45 y V≈148); rojo: tono < 12 o > 170 con saturación alta.
- Flecha: máscara naranja (tono 14–26, S y V altas) → componentes conexos → casillas que toca;
  los extremos de la cadena de casillas son origen y destino; el destino es el extremo con
  más píxeles naranjas (la punta triangular).
Los diagramas de libro (blanco y negro) no tienen anotaciones: se devuelven vacías.
"""
from __future__ import annotations

import cv2
import numpy as np

FILES = "abcdefgh"


def _sq(row: int, col: int, flipped: bool) -> str:
    if flipped:
        return FILES[7 - col] + str(row + 1)
    return FILES[col] + str(8 - row)


def _is_color(img_bgr: np.ndarray) -> bool:
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    return float(np.percentile(hsv[..., 1], 75)) > 60


def detect(warped: np.ndarray, flipped: bool = False) -> dict:
    """Devuelve {"highlights": {"amarillo": [...], "rojo": [...]}, "arrows": [[origen, destino], ...]}."""
    out: dict = {"highlights": {}, "arrows": []}
    if not _is_color(warped):
        return out
    hsv = cv2.cvtColor(warped, cv2.COLOR_BGR2HSV)
    H, S, V = hsv[..., 0].astype(int), hsv[..., 1].astype(int), hsv[..., 2].astype(int)
    orange = ((H >= 14) & (H <= 26) & (S > 120) & (V > 170)).astype(np.uint8)
    cell = warped.shape[0] // 8

    yellow, red = [], []
    for r in range(8):
        for c in range(8):
            y0, x0 = r * cell, c * cell
            ring = np.zeros((cell, cell), bool)
            b = max(3, cell // 10)
            ring[:b, :] = ring[-b:, :] = ring[:, :b] = ring[:, -b:] = True
            ring[: cell // 4, : cell // 4] = False  # esquina con número de coordenada
            ring[-cell // 4 :, -cell // 4 :] = False  # esquina con letra de coordenada
            sl = (slice(y0, y0 + cell), slice(x0, x0 + cell))
            mask = ring & (orange[sl] == 0)
            if mask.sum() < 20:
                continue
            h = float(np.median(H[sl][mask])); s = float(np.median(S[sl][mask])); v = float(np.median(V[sl][mask]))
            if 25 <= h <= 42 and s >= 90 and v >= 180:  # amarillo claro (#F6F669) u oscuro
                yellow.append(_sq(r, c, flipped))
            elif (h < 12 or h > 170) and s >= 110 and v >= 120:
                red.append(_sq(r, c, flipped))
    if yellow:
        out["highlights"]["amarillo"] = sorted(yellow)
    if red:
        out["highlights"]["rojo"] = sorted(red)

    n, lab, stats, _ = cv2.connectedComponentsWithStats(orange, 8)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] < cell * cell * 0.08:
            continue
        comp = lab == i
        counts = {}
        for r in range(8):
            for c in range(8):
                k = int(comp[r * cell:(r + 1) * cell, c * cell:(c + 1) * cell].sum())
                if k > cell * cell * 0.02:
                    counts[(r, c)] = k
        if len(counts) < 2:
            continue
        cells = set(counts)
        deg = {rc: sum(1 for d in cells if abs(d[0] - rc[0]) + abs(d[1] - rc[1]) == 1) for rc in cells}  # vecinos en cruz: soporta flechas en L (caballo)
        ends = [rc for rc in cells if deg[rc] <= 1] or sorted(cells, key=lambda rc: counts[rc])[:2]
        if len(ends) < 2:
            continue
        ends = sorted(ends, key=lambda rc: counts[rc])[-2:]

        # la punta es la zona más gruesa de la flecha: máximo de la transformada de distancia
        dt = cv2.distanceTransform(comp.astype(np.uint8), cv2.DIST_L2, 3)
        py, px = np.unravel_index(int(np.argmax(dt)), dt.shape)

        def dist_to_tip(rc):
            cy, cx = (rc[0] + 0.5) * cell, (rc[1] + 0.5) * cell
            return (cy - py) ** 2 + (cx - px) ** 2

        head, tail = sorted(ends, key=dist_to_tip)
        out["arrows"].append([_sq(*tail, flipped), _sq(*head, flipped)])
    out["arrows"].sort()
    return out


# --- Formato ONCE de las anotaciones (R14, R15, R21) ---
_LOW = ["", "⠂", "⠆", "⠒", "⠲", "⠢", "⠖", "⠶", "⠦"]


def _join_y(items: list[str]) -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " y " + items[-1]


def _br(sq: str) -> str:
    return sq[0] + _LOW[int(sq[1])]


def braille_block(ann: dict) -> str:
    """Bloque de observaciones en braille, p. ej. `)Resaltadas en amarillo las casillas g⠒ y h⠲(`."""
    hl = {c: v for c, v in (ann.get("highlights") or {}).items() if v}
    arrows = ann.get("arrows") or []
    if not hl and not arrows:
        return ""
    lines = []
    if hl:
        colors = list(hl)
        parts = []
        for i, c in enumerate(colors):
            sqs = _join_y([_br(s) for s in hl[c]])
            parts.append((f"en {c} las casillas{':' if len(colors) > 1 else ''} " if i == 0 else f", en {c}, ") + sqs)
        lines.append("Resaltadas " + (" y".join(parts)))
    lines += [f"{_br(a)}¬⠒⠕¬{_br(b)}" for a, b in arrows]
    return ")" + "\n".join(lines) + "("


def audio_lines(ann: dict) -> str:
    """Frases finales de audio: resaltados y flechas."""
    out = []
    for c, sqs in (ann.get("highlights") or {}).items():
        if sqs:
            many = len(sqs) > 1
            out.append(f"Resaltada{'s' if many else ''} en {c} {'las casillas' if many else 'la casilla'} {_join_y([s.upper() for s in sqs])}.")
    out += [f"Flecha de {a.upper()} a {b.upper()}." for a, b in ann.get("arrows") or []]
    return " ".join(out)
