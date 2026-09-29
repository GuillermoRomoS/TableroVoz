"""Tests E2E de api.py y cli.py (Requirement 1.1, 5.4, 7.2 y flujo imagen->FEN->salidas).

Requieren un modelo entrenado (models/tiles.joblib); si no existe, se entrena uno
pequeño una vez para toda la sesión de test.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tablerovoz.tiles import DEFAULT_MODEL_PATH

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "samples"


@pytest.fixture(scope="session", autouse=True)
def ensure_model():
    if not Path(DEFAULT_MODEL_PATH).exists():
        from tablerovoz import train

        train.train(n_synth=60, seed=0, save=True)


@pytest.fixture(scope="module")
def client():
    from tablerovoz.api import app

    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_web_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "<h1>TableroVoz</h1>" in r.text
    assert "aria-live" in r.text


@pytest.mark.parametrize("stem", ["tablero5_digital", "libro_diag1_p15"])
def test_recognize_returns_full_payload(client, stem):
    png = (SAMPLES / f"{stem}.png").read_bytes()
    r = client.post(
        "/api/recognize",
        files={"image": (f"{stem}.png", png, "image/png")},
        data={"turn": "w", "flipped": "false"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    # FEN completo con turno
    assert data["fen"].endswith(" w - - 0 1")
    # salidas ONCE presentes
    assert data["braille"].startswith("Tablero:\n")
    assert data["description"]["compact"].startswith("Blancas: ")
    assert data["description"]["compact"].rstrip().endswith(("blancas.", "negras.", ".", "E4.", "E3."))
    assert isinstance(data["doubts"], list)
    assert len(data["confidence"]) == 64


def test_recognize_bad_image_returns_400(client):
    r = client.post(
        "/api/recognize",
        files={"image": ("x.png", b"no-es-una-imagen", "image/png")},
        data={"turn": "w"},
    )
    assert r.status_code == 400


def test_describe_endpoint_matches_once_reference(client):
    # FEN del Diagrama 1: la salida debe ser el texto de audio oficial de la ONCE.
    fen = "r3kb1r/pp1qpppp/2n5/1Bp5/Q5b1/2N2N2/PP1PKPPP/2R4R"
    r = client.post("/api/describe", json={"fen": fen, "turn": "w"})
    assert r.status_code == 200
    compact = r.json()["description"]["compact"]
    assert compact.startswith("Blancas: Rey en E2, Dama en A4, Torres en C1 y H1")
    assert compact.endswith("Juegan blancas.")


def test_describe_endpoint_bad_fen(client):
    r = client.post("/api/describe", json={"fen": "esto-no-es-fen", "turn": "w"})
    assert r.status_code == 400


def test_cli_runs_on_sample(capsys):
    from tablerovoz import cli

    code = cli.main([str(SAMPLES / "tablero5_digital.png"), "--turn", "w"])
    assert code == 0
    out = capsys.readouterr().out
    assert "=== FEN ===" in out
    assert "=== Braille (ONCE / Ebrai) ===" in out
    assert "Tablero:" in out
    assert "=== Audio (ONCE) ===" in out
    assert "Juegan blancas." in out


def test_cli_missing_image_returns_code_2():
    from tablerovoz import cli

    assert cli.main(["no_existe.png", "--turn", "w"]) == 2
