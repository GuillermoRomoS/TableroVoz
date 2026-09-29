# Kit Kiro · TableroVoz (Reto ONCE: diagrama de ajedrez → descripción accesible)
1. Copia `.kiro/` y `KIRO-LOG.md` a la raíz de tu repo y ábrelo en Kiro.
2. Lee `CHULETA-AJEDREZ.md` (plan del día, prompts, pitch).
3. Guarda los diagramas de ejemplo en `samples/` con un `.fen` de solución para medir la precisión.

## Ejecutar el backend (Python 3.11+, validado con 3.12)

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt      # (Linux/Mac: .venv/bin/pip)
python -m tablerovoz.train --n 200                 # entrena models/tiles.joblib
uvicorn tablerovoz.api:app --reload                # web + API en http://127.0.0.1:8000
pytest -q                                          # tests
```

### CLI

```
python -m tablerovoz.cli samples/tablero5_digital.png --turn w
```

Imprime el FEN, la salida braille (formato ONCE/Ebrai) y la de audio (formato ONCE).

### Medir precisión

```
python eval.py --quick        # solo samples de desarrollo (rápido)
python eval.py                # samples de desarrollo (+ banco sintético)
```

`samples/holdout/` NO se usa para desarrollar; se reserva para el Sprint 3 (R31).

## Desplegar en la nube (Docker)

La imagen entrena el clasificador en el build y sirve web + API con uvicorn en `$PORT`
(por defecto 8080), compatible con Cloud Run, Render, Fly, etc.

```
docker build -t tablerovoz .
docker run -p 8080:8080 -e PORT=8080 tablerovoz
```

Con Bedrock (opcional, segunda opinión): pasar `AWS_REGION` y `BEDROCK_MODEL_ID` como
variables de entorno; sin credenciales el pipeline funciona solo con el clasificador (R34).

## Demo web sin servidor (GitHub Pages)

**Pruébalo:** https://guillermoromos.github.io/TableroVoz/

La carpeta `docs/` es la misma web accesible (`web/`) pero ejecuta el backend Python **dentro del navegador** con [Pyodide](https://pyodide.org): `pyodide-shim.js` intercepta `/api/recognize` y `/api/describe` y llama a `docs/py/web_bridge.py`, que usa los mismos módulos de `tablerovoz/`. Así se puede abrir desde un simple HTML publicado en GitHub Pages (Settings → Pages → Branch `main`, carpeta `/docs`).

- Primera carga: 20–40 s (descarga numpy, OpenCV y scikit-learn para WebAssembly).
- El modelo `docs/models/tiles.joblib` está entrenado con scikit-learn 1.8 (la versión incluida en Pyodide).
