"""API FastAPI de TableroVoz: subir imagen -> FEN -> descripción accesible.

Endpoints (design.md):
- POST /api/recognize  (multipart: image, turn?, flipped?) -> FEN, dudas, confianza,
  descripción (compact/spoken/ranks), braille, source.
- POST /api/describe    (JSON: fen, turn?) -> descripción + braille.
- GET  /               -> sirve la web accesible (web/index.html).
- GET  /health          -> estado.

La lógica vive en los módulos puros (recognize, describe, braille); la API solo
orquesta y serializa (R32).
"""
from __future__ import annotations

import io
from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from tablerovoz import annotations, board, braille, describe
from tablerovoz.recognize import recognize_image
from tablerovoz.tiles import DEFAULT_MODEL_PATH, TileClassifier

ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT / "web"

app = FastAPI(title="TableroVoz", version="0.1.0")

# El clasificador se carga una sola vez (perezosamente) y se reutiliza.
_classifier: TileClassifier | None = None


def get_classifier() -> TileClassifier | None:
    global _classifier
    if _classifier is None and Path(DEFAULT_MODEL_PATH).exists():
        _classifier = TileClassifier.load()
    return _classifier


def _full_fen(position_fen: str, turn: str | None) -> str:
    turn_field = "b" if (turn or "w").lower().startswith(("b", "n")) else "w"
    return f"{position_fen.strip().split()[0]} {turn_field} - - 0 1"


def _descriptions(full_fen: str, doubts: list[str]) -> dict[str, str]:
    return {
        "compact": describe.describe(full_fen, mode="compact", doubts=doubts),
        "spoken": describe.describe(full_fen, mode="spoken", doubts=doubts),
        "ranks": describe.describe(full_fen, mode="ranks"),
    }


class DescribeRequest(BaseModel):
    fen: str
    turn: str | None = "w"


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model_loaded": get_classifier() is not None}


@app.post("/api/recognize")
async def recognize(
    image: UploadFile = File(...),
    turn: str = Form("w"),
    flipped: str = Form("auto"),
) -> JSONResponse:
    classifier = get_classifier()
    if classifier is None:
        raise HTTPException(
            status_code=503,
            detail="No hay modelo entrenado. Ejecuta: python -m tablerovoz.train",
        )

    raw = await image.read()
    arr = np.frombuffer(raw, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="No pude leer la imagen. Sube un PNG o JPG.")

    # "Tablero girado": auto (avisa, no rota), sí (rota 180°) o no.
    flip_mode = "si" if str(flipped).lower() in ("true", "si", "yes", "1") else "auto"
    rec = recognize_image(img, classifier, flipped=flip_mode)
    if not rec.found_quad and not rec.fen:
        raise HTTPException(
            status_code=422,
            detail="No encuentro el tablero. Recorta la imagen al diagrama.",
        )

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
    return JSONResponse(
        {
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
        }
    )


@app.post("/api/describe")
def describe_endpoint(req: DescribeRequest) -> JSONResponse:
    try:
        full_fen = _full_fen(req.fen, req.turn)
        # valida que el FEN es procesable
        _ = describe.describe(full_fen, mode="compact")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"FEN no válido: {exc}") from exc
    return JSONResponse(
        {
            "fen": full_fen,
            "description": _descriptions(full_fen, []),
            "braille": braille.to_braille(full_fen, include_turn=True),
        }
    )


# Servir la web accesible como estáticos en la raíz.
if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
