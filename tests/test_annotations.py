"""Tests de la spec anotaciones-diagrama: resaltados y flechas con el formato ONCE."""
import json
from pathlib import Path

from tablerovoz import annotations
from tablerovoz.board import detect_board, load_image

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


def _ann(name, flipped=False):
    return annotations.detect(detect_board(load_image(SAMPLES / f"{name}.png")).warped, flipped=flipped)


def test_resaltados_de_los_ejemplos_digitales():
    for name, flipped in [("tablero1_digital", False), ("tablero2_digital", True), ("tablero3_digital", False), ("tablero5_digital", False)]:
        meta = json.loads((SAMPLES / f"{name}.meta.json").read_text(encoding="utf-8"))
        assert _ann(name, flipped)["highlights"] == {c: sorted(v) for c, v in meta["highlights"].items()}


def test_flechas_tablero5_formato_oficial():
    ann = _ann("tablero5_digital")
    assert ann["arrows"] == [["c1", "f1"], ["d3", "g3"], ["h5", "f6"]]


def test_libro_sin_anotaciones():
    assert _ann("libro_diag1_p15") == {"highlights": {}, "arrows": []}


def test_bloque_braille_exacto():
    ann = {"highlights": {"amarillo": ["g3", "h5"], "rojo": ["f6"]}, "arrows": [["c1", "f1"], ["d3", "g3"], ["h5", "f6"]]}
    assert annotations.braille_block(ann) == ")Resaltadas en amarillo las casillas: g⠒ y h⠢ y, en rojo, f⠖\nc⠂¬⠒⠕¬f⠂\nd⠒¬⠒⠕¬g⠒\nh⠢¬⠒⠕¬f⠖("
