# Design Document – Anotaciones

## Módulo `tablerovoz/annotations.py`
- Entrada: imagen rectificada 512×512 + rejilla. Salida: `{ highlights: {amarillo: [sq], rojo: [sq]}, arrows: [[from, to]] }`.
- **Resaltados:** para cada casilla, color mediano de un anillo interior (evita la pieza). Convertir a HSV y comparar con el fondo verde/crema normal del tablero: tono ≈ 55–65° y saturación alta → amarillo; tono ≈ 0–15° → rojo.
- **Flechas:** máscara naranja (tono ≈ 25–40°, S y V altas) → morfología → componentes conexos. Esqueletizar; los dos extremos se mapean a casillas. La **punta** es el extremo con más píxeles en un radio (triángulo) → destino.
- **Insignias:** círculos pequeños azules/rojos en la esquina de una casilla → se ignoran (no son fondo ni flecha).
- Integración: `describe.py` y `braille.py` reciben `annotations` y añaden el bloque final (R14, R15, R21).

## Verificación
- `eval.py --annotations` compara con `samples/*.meta.json`: aciertos de resaltados y de flechas por separado.
