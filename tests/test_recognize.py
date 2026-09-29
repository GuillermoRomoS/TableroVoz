"""Tests del pipeline recognize.py — compuerta de ocupación + dudas de validate (Cambio 3).

Confirma que, tras la refactorización (compuerta vacía/ocupada), validate.py sigue
marcando dudas y que estas afloran en Recognition.doubts / Recognition.validation.
"""
from __future__ import annotations

import random
from pathlib import Path

import cv2
import numpy as np
import pytest

from tablerovoz import board, occupancy, recognize, synth, tiles
from tablerovoz.tiles import DEFAULT_MODEL_PATH, TileClassifier
from tablerovoz.validate import validate

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "samples"


@pytest.fixture(scope="module")
def classifier():
    if not Path(DEFAULT_MODEL_PATH).exists():
        from tablerovoz import train

        train.train(n_synth=60, seed=0, save=True)
    return TileClassifier.load()


def _render_bgr(fen: str) -> np.ndarray:
    sprites = synth.build_sprite_library()
    img = synth.render_png(fen, size=512, style="digital", sprites=sprites, rng=random.Random(0))
    return cv2.cvtColor(np.asarray(img.convert("RGB")), cv2.COLOR_RGB2BGR)


def test_recognition_returns_full_confidence_map(classifier):
    img = board.load_image(SAMPLES / "tablero1_digital.png")
    rec = recognize.recognize_image(img, classifier)
    assert len(rec.confidence) == 64
    assert isinstance(rec.doubts, list)
    assert rec.fen.count("/") == 7  # 8 filas


def test_occupancy_gate_zeroes_out_clearly_empty_board(classifier):
    # Imagen de tablero vacío: la compuerta debe dejar casi todo vacío.
    empty_fen = "8/8/8/8/8/8/8/8"
    img = _render_bgr(empty_fen)
    occ = occupancy.occupancy(board.split_tiles(img))
    assert sum(occ) <= 4  # tolerancia mínima a falsos positivos


def test_validation_doubts_flow_through_pipeline(classifier, monkeypatch):
    # Forzamos un FEN inválido (dos reyes blancos) devuelto por el clasificador y
    # comprobamos que validate marca dudas y que Recognition las incluye.
    bad_fen = "4k3/8/8/8/8/8/4K3/4K3"  # dos reyes blancos (e1, e2)

    def fake_predict_board(tiles_list, occupied=None):
        labels = tiles.fen_to_labels(bad_fen)
        confs = [0.99] * 64
        return labels, confs

    monkeypatch.setattr(classifier, "predict_board", fake_predict_board)
    img = board.load_image(SAMPLES / "tablero1_digital.png")
    rec = recognize.recognize_image(img, classifier)

    assert not rec.validation.ok
    assert any("reyes de las blancas" in w for w in rec.validation.warnings)
    # las casillas implicadas (e1, e2) deben estar entre las dudas
    assert "e1" in rec.doubts and "e2" in rec.doubts


def test_low_confidence_marks_doubt(classifier, monkeypatch):
    # Todas las casillas con confianza baja -> todas dudosas.
    def low_conf(tiles_list, occupied=None):
        labels = ["empty"] * 64
        labels[0] = "wK"
        labels[63] = "bK"
        confs = [0.10] * 64
        return labels, confs

    monkeypatch.setattr(classifier, "predict_board", low_conf)
    img = board.load_image(SAMPLES / "tablero1_digital.png")
    rec = recognize.recognize_image(img, classifier)
    assert len(rec.doubts) == 64  # todas por debajo de LOW_CONF


def test_orientation_flip_improves_rotated_board(classifier):
    # tablero2_digital está GIRADO (negras abajo). El giro manual debe acercar el
    # resultado a la verdad más que sin girar.
    truth = tiles.fen_to_labels(
        (SAMPLES / "tablero2_digital.fen").read_text(encoding="utf-8").strip().split()[0]
    )
    img = board.load_image(SAMPLES / "tablero2_digital.png")

    rec_no = recognize.recognize_image(img, classifier, flipped="no")
    rec_yes = recognize.recognize_image(img, classifier, flipped="si")

    def hits(rec):
        return sum(1 for a, b in zip(truth, tiles.fen_to_labels(rec.fen)) if a == b)

    assert rec_yes.flipped is True
    assert rec_no.flipped is False
    assert hits(rec_yes) > hits(rec_no)


def test_auto_does_not_rotate_but_may_warn(classifier):
    # Decisión medida: en "auto" NO se rota (evita giros erróneos en libro impreso).
    img = board.load_image(SAMPLES / "tablero2_digital.png")
    rec = recognize.recognize_image(img, classifier, flipped="auto")
    assert rec.flipped is False


def test_validate_still_clean_on_good_fen():
    # Change 3: validate.py sin tocar, sigue dando ok en posiciones legales.
    fen = (SAMPLES / "tablero1_digital.fen").read_text(encoding="utf-8").strip().split()[0]
    assert validate(fen).ok
