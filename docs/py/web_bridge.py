"""Puente para GitHub Pages: ejecuta la API de TableroVoz dentro del navegador (Pyodide).

Replica la lógica de tablerovoz/api.py sin FastAPI: mismas entradas y la misma
respuesta JSON, para que la web accesible (app.js) funcione sin servidor.
"""
import json

import cv2
import numpy as np

from tablerovoz import annotations, board, braille, describe
from tablerovoz.recognize import recognize_image
from tablerovoz.tiles import TileClassifier

_classifier = None


def _clf():
    global _classifier
    if _classifier is None:
        _classifier = TileClassifier.load()
    return _classifier


def _full_fen(position_fen, turn):
    t = "b" if (turn or "w").lower().startswith(("b", "n")) else "w"
    return f"{position_fen.strip().split()[0]} {t} - - 0 1"


def _descriptions(full_fen, doubts):
    return {
        "compact": describe.describe(full_fen, mode="compact", doubts=doubts),
        "spoken": describe.describe(full_fen, mode="spoken", doubts=doubts),
        "ranks": describe.describe(full_fen, mode="ranks"),
    }


def api_recognize(raw: bytes, turn: str = "w", flipped: str = "false") -> str:
    img = cv2.imdecode(np.frombuffer(bytes(raw), dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return json.dumps({"status": 400, "detail": "No pude leer la imagen. Sube un PNG o JPG."})
    flip_mode = "si" if str(flipped).lower() in ("true", "si", "yes", "1") else "auto"
    rec = recognize_image(img, _clf(), flipped=flip_mode)
    if not rec.found_quad and not rec.fen:
        return json.dumps({"status": 422, "detail": "No encuentro el tablero. Recorta la imagen al diagrama."})
    full_fen = _full_fen(rec.fen, turn)
    ann = annotations.detect(board.detect_board(img).warped, flipped=bool(rec.flipped))
    desc = _descriptions(full_fen, rec.doubts)
    extra_audio = annotations.audio_lines(ann)
    if extra_audio:
        desc["compact"] += " " + extra_audio
        desc["spoken"] += " " + extra_audio
    br = braille.to_braille(full_fen, include_turn=True)
    block = annotations.braille_block(ann)
    if block:
        br += "\n" + block
    return json.dumps({
        "status": 200,
        "fen": full_fen,
        "doubts": rec.doubts,
        "confidence": rec.confidence,
        "description": desc,
        "braille": br,
        "annotations": ann,
        "warnings": rec.validation.warnings,
        "found_board": rec.found_quad,
        "flipped": rec.flipped,
        "source": "classifier",
    }, default=float)


def api_describe(fen: str, turn: str = "w") -> str:
    try:
        full_fen = _full_fen(fen, turn)
        describe.describe(full_fen, mode="compact")
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"status": 400, "detail": f"FEN no válido: {exc}"})
    return json.dumps({
        "status": 200,
        "fen": full_fen,
        "description": _descriptions(full_fen, []),
        "braille": braille.to_braille(full_fen, include_turn=True),
    })
