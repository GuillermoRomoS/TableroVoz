---
name: evaluar-diagrama
description: Evalúa uno o varios diagramas de ajedrez con TableroVoz, compara con su FEN esperado si existe y genera el bloque listo para pegar en los formularios del hackathon (tipo de diagrama, nº de piezas, salida tal cual). Úsalo cuando se pida probar un diagrama, medir precisión o preparar resultados para las fichas.
---
# Evaluar diagrama

1. Ejecuta `python -m tablerovoz.cli <imagen> --turn w` y guarda la salida EXACTA (braille + audio + FEN). No la retoques.
2. Si existe `<imagen>.fen`, compara casilla a casilla y reporta: casillas correctas /64, piezas mal reconocidas (casilla: esperado → obtenido).
3. Cuenta elementos: nº de piezas blancas y negras, resaltados, flechas; tipo: "digital" o "libro impreso".
4. Devuelve este bloque:
```
Diagrama: <nombre> · tipo <digital|libro> · <N> piezas (<b> blancas, <n> negras) · <r> resaltados · <f> flechas
Precisión: <x>/64 casillas · errores: <lista o "ninguno">
Salida tal cual:
<salida exacta>
```
5. Añade una línea a KIRO-LOG.md con la precisión.
