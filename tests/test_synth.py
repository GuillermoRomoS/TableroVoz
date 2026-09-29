"""Tests de synth.py — diagramas sintéticos con FEN conocido (Requirement 2.4).

Backend PNG por defecto: solo Pillow + sprites recortados de samples de desarrollo
(cairo no está disponible en este entorno). No se usa samples/holdout (R31).
"""
from __future__ import annotations

import random

import chess

from tablerovoz import synth
from tablerovoz.validate import validate


def test_random_fens_deterministic():
    a = synth.random_fens(10, seed=42)
    b = synth.random_fens(10, seed=42)
    assert a == b
    # semilla distinta -> (muy probablemente) distinto
    assert synth.random_fens(10, seed=1) != a


def test_random_fens_are_valid_positions():
    for fen in synth.random_fens(30, seed=7):
        result = validate(fen)
        assert result.ok, (fen, result.warnings)


def test_random_fen_has_one_king_each():
    for fen in synth.random_fens(20, seed=3):
        board = chess.Board(None)
        board.set_board_fen(fen)
        assert len(list(board.pieces(chess.KING, chess.WHITE))) == 1
        assert len(list(board.pieces(chess.KING, chess.BLACK))) == 1


def test_board_svg_contains_svg_root():
    svg = synth.board_svg(synth.random_fens(1, seed=0)[0])
    assert "<svg" in svg and "</svg>" in svg


def test_sprite_library_builds_from_dev_samples_only():
    lib = synth.build_sprite_library()
    # Debe haber al menos reyes de ambos colores (todos los samples tienen reyes).
    assert lib.get("wK") and lib.get("bK")
    # Todas las etiquetas tienen el formato color+letra válido.
    valid = {c + p for c in "wb" for p in "KQRBNP"}
    assert set(lib.keys()) <= valid
    # Cada sprite es una imagen no vacía.
    for sprites in lib.values():
        for s in sprites:
            assert s.image.size[0] > 0 and s.image.size[1] > 0


def test_sprite_library_excludes_holdout():
    # R31: la fuente por defecto son solo los tablero*_digital de desarrollo.
    assert all("holdout" not in stem for stem in synth._DEV_DIGITAL_SAMPLES)


def test_render_png_digital_size_and_mode():
    fen = synth.random_fens(1, seed=5)[0]
    img = synth.render_png(fen, size=256, style="digital")
    assert img.size == (256, 256)
    assert img.mode == "RGBA"


def test_render_png_book_style():
    fen = synth.random_fens(1, seed=5)[0]
    img = synth.render_png(fen, size=256, style="libro")
    assert img.size == (256, 256)


def test_render_png_deterministic_with_seed():
    fen = synth.random_fens(1, seed=9)[0]
    lib = synth.build_sprite_library()
    a = synth.render_png(fen, size=128, sprites=lib, rng=random.Random(0))
    b = synth.render_png(fen, size=128, sprites=lib, rng=random.Random(0))
    assert a.tobytes() == b.tobytes()


def test_generate_dataset_roundtrips_fen(tmp_path):
    items = synth.generate_dataset(tmp_path, n=3, seed=0)
    assert len(items) == 3
    for png_path, fen in items:
        assert png_path.exists()
        fen_file = png_path.with_suffix(".fen")
        assert fen_file.exists()
        assert fen_file.read_text(encoding="utf-8").strip() == fen
