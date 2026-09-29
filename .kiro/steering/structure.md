# Estructura

```
tablerovoz/
  board.py        detectar y rectificar el tablero, orientación, cortar 64 casillas
  tiles.py        extracción de características de casilla + clasificador
  synth.py        generar diagramas sintéticos con FEN conocido
  train.py        entrenar el clasificador
  vision_llm.py   segunda opinión con Bedrock (imagen con rejilla y coordenadas superpuestas)
  fuse.py         combinar clasificador + LLM, confianza por casilla
  validate.py     reglas del ajedrez (python-chess) y avisos
  describe.py     FEN → descripción accesible (texto, voz, por filas)
  braille.py      FEN → braille según Documento técnico B8 de la CBE
  annotations.py  resaltados y flechas (2ª spec)
  cli.py          python -m tablerovoz.cli <imagen> → salida braille + audio + FEN
  api.py          FastAPI
web/              index.html, app.js, styles.css
samples/          diagramas oficiales ONCE (+ .fen, .braille.txt, .meta.json)
  holdout/        diagramas reservados SOLO para el Sprint 3
tests/            test_describe.py, test_validate.py, test_board.py
eval.py           precisión por casilla y por tablero
KIRO-LOG.md       cómo usamos Kiro (para el pitch)
```
