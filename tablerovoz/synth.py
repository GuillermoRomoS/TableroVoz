"""Generación de diagramas sintéticos con FEN conocido (Requirement 2.4, design "synth.py").

Objetivo: producir imágenes de tableros cuyo FEN conocemos, para entrenar y medir
el clasificador de casillas (train.py / eval.py) sin depender de datos externos.

Backends de imagen:
- SVG (`board_svg`): vía `chess.svg`, Python puro, siempre disponible.
- PNG por defecto (`render_png`): SOLO Pillow. Dibuja el tablero (casillas claras/
  oscuras, con variante rayada tipo libro) y pega *sprites* de piezas recortados de
  los samples de desarrollo (conocemos su FEN, así que cada casilla ocupada da un
  sprite etiquetado con su clase). No requiere cairo.
- PNG opcional vía cairosvg (`render_png_cairosvg`): solo si el sistema tiene la
  librería nativa cairo; si no, se ignora y se usa el backend Pillow.

NOTA (R31): la biblioteca de sprites se construye SOLO con samples de desarrollo,
nunca con `samples/holdout/`.

La generación de FEN es determinista si se pasa una `seed`.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import chess
import chess.svg
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "samples"

# Samples de desarrollo válidos como fuente de sprites (NO incluye holdout, R31).
_DEV_DIGITAL_SAMPLES = (
    "tablero1_digital",
    "tablero2_digital",
    "tablero3_digital",
    "tablero4_digital",
    "tablero5_digital",
)

# Colores de casilla estilo "digital" (verde/crema típico de los samples).
_LIGHT = (234, 233, 210)
_DARK = (120, 149, 92)
# Estilo "libro impreso": claras casi blancas, oscuras rayadas en gris.
_BOOK_LIGHT = (245, 245, 245)
_BOOK_DARK = (150, 150, 150)


# --------------------------------------------------------------------------- #
# 1. Generación de FEN
# --------------------------------------------------------------------------- #
def random_fen(rng: random.Random, max_pieces_per_side: int = 12) -> str:
    """Genera un FEN de posición plausible (pasa validate.validate) de forma determinista.

    Coloca dos reyes en casillas no adyacentes y un número aleatorio de piezas
    respetando: ≤ 8 peones por bando, sin peones en filas 1/8, ≤ 16 piezas por bando.
    Devuelve solo el campo de posición.
    """
    board = chess.Board(None)

    # Reyes no adyacentes.
    wk = rng.randrange(64)
    while True:
        bk = rng.randrange(64)
        if bk != wk and chess.square_distance(wk, bk) > 1:
            break
    board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))

    for color in (chess.WHITE, chess.BLACK):
        n_pawns = rng.randint(0, 8)
        n_others = rng.randint(0, max_pieces_per_side - 1 - n_pawns)
        others = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
        wanted = [chess.PAWN] * n_pawns + [rng.choice(others) for _ in range(max(n_others, 0))]
        for piece_type in wanted:
            placed = False
            for _ in range(40):  # intentos por pieza
                sq = rng.randrange(64)
                rank = chess.square_rank(sq) + 1
                if board.piece_at(sq) is not None:
                    continue
                if piece_type == chess.PAWN and rank in (1, 8):
                    continue
                board.set_piece_at(sq, chess.Piece(piece_type, color))
                placed = True
                break
            if not placed:
                continue

    return board.board_fen()


def random_fens(n: int, seed: int = 0) -> list[str]:
    """Lista determinista de `n` FEN sintéticos plausibles."""
    rng = random.Random(seed)
    return [random_fen(rng) for _ in range(n)]


# --------------------------------------------------------------------------- #
# 2. SVG (siempre disponible)
# --------------------------------------------------------------------------- #
def board_svg(fen: str, size: int = 400, coordinates: bool = True) -> str:
    """SVG del diagrama a partir de un FEN (Python puro, sin cairo)."""
    board = chess.Board(None)
    board.set_board_fen(fen.strip().split()[0])
    return chess.svg.board(board=board, size=size, coordinates=coordinates)


# --------------------------------------------------------------------------- #
# 3. Biblioteca de sprites recortados de los samples de desarrollo
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Sprite:
    """Un recorte de casilla ocupada con su etiqueta de clase (p. ej. 'wN')."""

    label: str  # clase: 'wK','wQ','wR','wB','wN','wP','bK',...
    image: Image.Image


def _piece_label(piece: chess.Piece) -> str:
    color = "w" if piece.color == chess.WHITE else "b"
    letter = piece.symbol().upper()  # K Q R B N P
    return f"{color}{letter}"


def _detect_inner_box(im: Image.Image, max_margin_frac: float = 0.25) -> tuple[int, int, int, int]:
    """Detecta el recuadro interior del tablero descartando márgenes casi uniformes.

    Devuelve (left, top, right, bottom) del área del tablero 8×8.
    """
    import numpy as np

    arr = np.asarray(im.convert("RGB")).astype(float)
    h, w = arr.shape[:2]

    def run(is_uniform) -> int:
        n = 0
        limit = int(min(h, w) * max_margin_frac)
        while n < limit and is_uniform(n):
            n += 1
        return n

    top = run(lambda i: arr[i, :, :].std() < 6)
    bottom = run(lambda i: arr[h - 1 - i, :, :].std() < 6)
    left = run(lambda i: arr[:, i, :].std() < 6)
    right = run(lambda i: arr[:, w - 1 - i, :].std() < 6)
    return left, top, w - right, h - bottom


def build_sprite_library(
    stems: Iterable[str] = _DEV_DIGITAL_SAMPLES,
) -> dict[str, list[Sprite]]:
    """Construye la biblioteca de sprites por clase a partir de samples de desarrollo.

    Para cada sample: lee su FEN, detecta el recuadro del tablero, lo divide en 8×8 y
    recorta cada casilla OCUPADA como sprite etiquetado con su clase.

    Returns:
        dict clase -> lista de sprites (imágenes RGBA de casilla).
    """
    library: dict[str, list[Sprite]] = {}
    for stem in stems:
        assert "holdout" not in stem, "R31: no usar samples/holdout para sprites"
        png = SAMPLES / f"{stem}.png"
        fen = (SAMPLES / f"{stem}.fen").read_text(encoding="utf-8").strip().split()[0]
        if not png.exists():
            continue
        im = Image.open(png).convert("RGBA")
        left, top, right, bottom = _detect_inner_box(im)
        cell_w = (right - left) / 8.0
        cell_h = (bottom - top) / 8.0

        board = chess.Board(None)
        board.set_board_fen(fen)
        for square, piece in board.piece_map().items():
            file = chess.square_file(square)  # 0..7 (a..h)
            rank = chess.square_rank(square)  # 0..7 (fila 1..8)
            # fila 8 arriba -> y=0; fila 1 abajo -> y=7*cell.
            col = file
            row = 7 - rank
            box = (
                int(round(left + col * cell_w)),
                int(round(top + row * cell_h)),
                int(round(left + (col + 1) * cell_w)),
                int(round(top + (row + 1) * cell_h)),
            )
            sprite = im.crop(box)
            library.setdefault(_piece_label(piece), []).append(
                Sprite(label=_piece_label(piece), image=sprite)
            )
    return library


# --------------------------------------------------------------------------- #
# 4. Render PNG con Pillow (backend por defecto)
# --------------------------------------------------------------------------- #
def _draw_hatch(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], color) -> None:
    """Rayado diagonal tipo libro impreso sobre una casilla oscura."""
    x0, y0, x1, y1 = box
    step = max(4, (x1 - x0) // 8)
    for x in range(x0 - (y1 - y0), x1, step):
        draw.line([(x, y1), (x + (y1 - y0), y0)], fill=color, width=1)


def render_png(
    fen: str,
    size: int = 512,
    style: str = "digital",
    sprites: dict[str, list[Sprite]] | None = None,
    rng: random.Random | None = None,
) -> Image.Image:
    """Dibuja el diagrama con Pillow y pega sprites de piezas de los samples.

    Args:
        fen: FEN de la posición (solo se usa el campo de posición).
        size: tamaño del lado del tablero en px.
        style: "digital" (verde/crema) o "libro" (claras casi blancas, oscuras rayadas).
        sprites: biblioteca de sprites; si es None se construye con build_sprite_library().
        rng: generador aleatorio para elegir entre sprites de la misma clase (determinismo).

    Returns:
        Imagen RGBA del diagrama.
    """
    if rng is None:
        rng = random.Random(0)
    if sprites is None:
        sprites = build_sprite_library()

    light, dark = (_LIGHT, _DARK) if style == "digital" else (_BOOK_LIGHT, _BOOK_DARK)
    cell = size // 8
    size = cell * 8  # asegurar múltiplo de 8
    img = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    board = chess.Board(None)
    board.set_board_fen(fen.strip().split()[0])

    for row in range(8):  # 0 arriba (fila 8) .. 7 abajo (fila 1)
        for col in range(8):  # 0 = columna a
            x0, y0 = col * cell, row * cell
            box = (x0, y0, x0 + cell, y0 + cell)
            is_dark = (row + col) % 2 == 1
            draw.rectangle(box, fill=dark if is_dark else light)
            if style == "libro" and is_dark:
                _draw_hatch(draw, box, (110, 110, 110))

            rank = 7 - row
            square = chess.square(col, rank)
            piece = board.piece_at(square)
            if piece is not None:
                label = _piece_label(piece)
                choices = sprites.get(label)
                if choices:
                    sprite = rng.choice(choices).image.resize((cell, cell))
                    img.paste(sprite, (x0, y0), sprite if sprite.mode == "RGBA" else None)
    return img


def render_png_cairosvg(fen: str, size: int = 400) -> Image.Image:
    """PNG vía cairosvg (opcional). Lanza RuntimeError si cairo no está disponible."""
    try:
        import io

        import cairosvg
    except OSError as exc:  # librería nativa cairo ausente
        raise RuntimeError("cairo no disponible en este sistema") from exc
    svg = board_svg(fen, size=size)
    png_bytes = cairosvg.svg2png(bytestring=svg.encode("utf-8"))
    return Image.open(io.BytesIO(png_bytes)).convert("RGBA")


def cairosvg_available() -> bool:
    """True si cairosvg puede cargar la librería nativa cairo."""
    try:
        import cairosvg  # noqa: F401

        return True
    except OSError:
        return False


# --------------------------------------------------------------------------- #
# 5. Generación de un banco de datos
# --------------------------------------------------------------------------- #
def generate_dataset(
    out_dir: Path | str,
    n: int = 50,
    seed: int = 0,
    style: str = "digital",
) -> list[tuple[Path, str]]:
    """Genera `n` diagramas sintéticos PNG con su FEN en `out_dir`.

    Escribe `<out>/synth_XXXX.png` y `<out>/synth_XXXX.fen`. Devuelve la lista de
    (ruta_png, fen). Determinista para un `seed` dado.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    sprites = build_sprite_library()
    rng = random.Random(seed)
    fens = random_fens(n, seed=seed)
    written: list[tuple[Path, str]] = []
    for i, fen in enumerate(fens):
        img = render_png(fen, style=style, sprites=sprites, rng=rng)
        png_path = out / f"synth_{i:04d}.png"
        img.convert("RGB").save(png_path)
        (out / f"synth_{i:04d}.fen").write_text(fen + "\n", encoding="utf-8")
        written.append((png_path, fen))
    return written


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Genera diagramas sintéticos con FEN conocido.")
    parser.add_argument("--n", type=int, default=50)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", default="data/synth")
    parser.add_argument("--style", choices=["digital", "libro"], default="digital")
    args = parser.parse_args()
    items = generate_dataset(args.out, n=args.n, seed=args.seed, style=args.style)
    print(f"Generados {len(items)} diagramas en {args.out} (estilo {args.style}).")
