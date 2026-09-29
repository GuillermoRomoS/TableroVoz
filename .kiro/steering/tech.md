# Stack

- **Python 3.11+** en todo el backend (validado con 3.12).
- `opencv-python-headless`, `numpy`: detección del tablero, rectificación y corte en 64 casillas.
- `python-chess`: FEN, validación de la posición, y `chess.svg` + `cairosvg` para **generar diagramas sintéticos** con FEN conocido (datos de entrenamiento y de test).
- `scikit-learn`: clasificador ligero de casillas (13 clases: vacía + 6 piezas × 2 colores). Sin redes profundas: debe entrenar en < 1 min.
- **Amazon Bedrock** (API Converse, modelo multimodal en `BEDROCK_MODEL_ID`, región `AWS_REGION`) como segunda opinión y para casos difíciles. Opcional: si no hay credenciales, el pipeline funciona solo con el clasificador.
- **FastAPI** + `uvicorn`: `POST /api/recognize` (imagen) y `POST /api/describe` (FEN).
- Frontend: **HTML + JS sin framework** servido por FastAPI (`/web`). Voz con `speechSynthesis` es-ES.
- Tests: `pytest`. Script `eval.py` que mide la precisión por casilla y por tablero.

## Comandos
- `pip install -r requirements.txt`
- `python -m tablerovoz.synth --n 300` (genera diagramas sintéticos en `data/`)
- `python -m tablerovoz.train` (entrena el clasificador → `models/tiles.joblib`)
- `python eval.py` (precisión sobre `samples/` y `data/test`)
- `uvicorn tablerovoz.api:app --reload`
- `pytest -q`

## Reglas
R32. Python 3.11+ (validado con 3.12); funciones puras y testeables; nada de lógica en la API.
R33. Credenciales solo en `.env`, nunca en el código ni en logs.
R34. Si Bedrock falla o no hay credenciales, el pipeline sigue con el clasificador y lo indica.
R35. No generar código sin una tarea de la spec que lo pida (planificar antes de programar).
