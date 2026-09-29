---
inclusion: fileMatch
fileMatchPattern: ["tablerovoz/board.py", "tablerovoz/tiles.py", "tablerovoz/synth.py", "tablerovoz/train.py", "tablerovoz/vision_llm.py", "tablerovoz/fuse.py", "tablerovoz/annotations.py", "eval.py"]
---
# Reconocimiento

R24. Pipeline fijo: detectar tablero → rectificar a 512×512 → 64 casillas → vacía/ocupada → pieza → validar.
R25. Soportar los dos estilos de los ejemplos: digital (verde/crema, coordenadas, resaltados, flechas, insignias "!") y libro impreso (casillas oscuras rayadas, ~300 px).
R26. "Vacía" se decide comparando con plantillas de casilla vacía clara/oscura (soporta rayado), no solo por varianza.
R27. Clasificador propio de 13 clases entrenado con diagramas sintéticos de FEN conocido + recortes de samples/; el LLM multimodal es solo segunda opinión, nunca la única fuente.
R28. Validación ajedrecística: 1 rey por bando, ≤ 8 peones, sin peones en filas 1/8, ≤ 16 piezas; si falla, la casilla se marca como duda y se avisa.
R29. Resaltados por tono HSV del fondo de la casilla (amarillo / rojo); flechas por máscara naranja → componentes → origen y punta.
R30. Toda mejora se mide con `python eval.py` (precisión por casilla y % tableros perfectos) y se anota en KIRO-LOG.md.
R31. Hold-out: `samples/holdout/` NO se usa para desarrollar ni ajustar; solo se evalúa en el Sprint 3 ("diagramas nuevos").
