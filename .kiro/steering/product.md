# Producto: TableroVoz · Hackathon Kiro × UCJC · Reto ONCE

## Reto
Convertir la **imagen de un diagrama de ajedrez** (libros, revistas, webs, capturas) en una **descripción accesible** que una persona ciega pueda usar para reconstruir la posición en su tablero adaptado: notación de ajedrez, orden fijo, sin ambigüedad, por lector de pantalla o audio.

## Los 3 pasos del problema
1. **Modelado:** qué reconocer (tablero, orientación, 64 casillas, 12 tipos de pieza, turno si aparece) y qué salida producir (lista de piezas en notación española + FEN).
2. **Reconocimiento:** imagen → posición (FEN) con validación y confianza por casilla.
3. **Traducción accesible:** FEN → **formato braille ONCE/Ebrai** y **formato audio ONCE** (ver `braille.md` y `chess-notation.md`), con casillas resaltadas y flechas, + tablero navegable.

## Datos oficiales
`samples/`: 6 diagramas digitales (con resaltados y flechas) y 4 de libro impreso, con FEN verificado contra la imagen, salida braille oficial y metadatos. `samples/REFERENCIA_ONCE.txt` = documento de la ONCE.

## Criterios del jurado (y cómo los atacamos)
| Criterio | Nuestra respuesta |
|---|---|
| Innovación: enfoque propio, no una herramienta genérica | Pipeline híbrido: visión clásica (rejilla + clasificador de casillas entrenado con diagramas sintéticos) + LLM multimodal como segunda opinión + validación con reglas del ajedrez |
| Viabilidad técnica: acierta piezas y posiciones y habla "en ajedrez" | Precisión medida por casilla sobre un banco de pruebas con FEN conocido; salida en casillas, piezas y notación |
| Impacto social: realmente utilizable por una persona ciega | Orden fijo tipo libro adaptado, pronunciación clara de columnas, tablero HTML navegable, consulta "¿qué hay en e4?", avisos de duda |
| Uso de Kiro: planificación, iteración, depuración | Spec + steering + hooks de evaluación automática; registro en `KIRO-LOG.md` |

## Checkpoints de evaluación
- ≈13:30 diseño y planteamiento técnico (no el resultado).
- 14:45 flujo funcional de extremo a extremo, aunque incompleto.
- ≈17:15 lo que verá el jurado. Pitch + demo de 2–3 min.

## Principios
- Nunca inventar una pieza: si una casilla es dudosa, se dice.
- Misma posición → siempre la misma descripción (determinista).
- Primero que funcione de extremo a extremo; después precisión; después extras.
