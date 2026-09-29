# Cómo usamos Kiro (se rellena solo con el hook log-kiro-usage)

| Hora | Tarea | Qué hizo Kiro | Qué corregimos / depuramos | Precisión eval.py |
|---|---|---|---|---|
| Sprint 2 | 6. board.py | Kiro implementó detección (umbral adaptativo + mayor cuadrilátero, fallback por proyecciones), rectificación a 512×512 y corte en 64 casillas en orden FEN | Rutas con acentos en Windows: `np.fromfile`+`imdecode`. Verificado alineado de casillas en samples (digitales usan fallback, libro usa cuadrilátero) | — |
| Sprint 2 | 7. tiles.py + train.py + eval.py | Clasificador de 13 clases (SVC calibrado), features 32×32 + HOG + señales de pieza; entrenamiento con sintéticos (digital+libro) y recortes de samples de desarrollo; `eval.py --quick` | `SVC(probability=True)` deprecado en sklearn 1.9 → `CalibratedClassifierCV`. Añadidas señales de primer plano para separar pieza/vacía | Sintético held-out ≈ 97 %; samples reales ≈ 73 % por casilla (0/8 tableros perfectos) |
| Sprint 2 | 8. api.py + web/ + cli.py + Docker | Flujo E2E imagen→FEN→braille ONCE+audio ONCE: FastAPI (`/api/recognize`, `/api/describe`, sirve web), web accesible (aria-live, foco a "Posición", tabla 8×8, consultar casilla, voz es-ES), CLI y Dockerfile (uvicorn en `$PORT`) | Verificado por HTTP y CLI con `tablero5_digital` y `libro_diag1_p15`; `/api/describe` reproduce el audio oficial del Diagrama 1. Docker no instalado en local: build no ejecutado | 88 tests en verde |
| Sprint 3 | Precisión · Cambio 1 (vacía/ocupada relativa) | `occupancy.py`: estima fondo claro/oscuro del tablero (mediana del anillo exterior por color de casilla) y marca ocupada si el centro se aleja de su fondo; apertura morfológica para ignorar el rayado del libro | Iteré el discriminador pieza-vs-rayado (opening morfológico fue lo más robusto); las piezas blancas sobre casilla clara siguen siendo el punto débil. Compuerta integrada en recognize.py y eval.py | Ocupación 90,0%; **por casilla 73,4% → 76,2%** (samples reales, --quick) |
| Sprint 3 | Precisión · Cambio 2 (forma+color separadas) | `shape.py`: clasificador de FORMA de 6 clases (K,Q,R,B,N,P) sobre la silueta binarizada y centrada (invariante al color) + COLOR por proporción de relleno oscuro del cuerpo; `train.py --only-shape` | Medido con eval.py: standalone 74,6% (forma 69,9%, color 83,1% con umbral calibrado 0,78); combinado con la compuerta como corrección de color, neutro/peor (75,2–76,2%). En samples reales pequeños/de baja resolución la silueta pierde textura útil, así que NO se cablea al pipeline por defecto; el módulo queda disponible para fusión/LLM (tarea 9) | Por casilla se mantiene en **76,2%** (Cambio 1); Cambio 2 no mejora en real, hallazgo registrado |
| Sprint 3 | Precisión · Cambio 3 (validate marca dudas) | Confirmado que tras la compuerta de ocupación, `validate.py` sigue corriendo en `recognize.py` y sus dudas (p. ej. dos reyes → e1/e2) se fusionan con las de baja confianza en `Recognition.doubts`; `validation` se devuelve entero | Tests nuevos `test_recognize.py`: FEN inválido (dos reyes) aflora aviso y casillas dudosas; baja confianza marca duda; posición legal sigue ok | Sin cambio de precisión (Cambio 3 es de robustez/avisos), se mantiene 76,2% |

## Resumen de la iteración de precisión (Sprint 3)

Precisión por casilla sobre `samples/` de desarrollo (`python eval.py --quick`, sin tocar `samples/holdout/`):

| Estado | Por casilla | Nota |
|---|---|---|
| Base (clasificador 13 clases) | 73,4 % | Top error: `empty→bB` (rayado del libro leído como alfil) |
| + Cambio 1 (ocupación relativa) | **76,2 %** | Compuerta vacía/ocupada por tablero; elimina el `empty→bB`. La mejora real |
| + Cambio 2 (forma+color) | 76,2 % | `shape.py` medido; no mejora en real (silueta pierde textura a baja resolución) → no cableado, disponible para fusión/LLM |
| + Cambio 3 (dudas de validate) | 76,2 % | Robustez: avisos y casillas dudosas afloran en la salida |

Puntos flojos conocidos (siguientes pasos): piezas blancas sobre casilla clara (contorno fino), diagramas de libro impreso a baja resolución. Palancas pendientes: mejorar la detección/rectificación del tablero de libro, y la segunda opinión del LLM multimodal (`vision_llm.py` + `fuse.py`, tarea 9). Suite de tests: 110 en verde.
| Sprint 3 | Orientación (bug tablero2 girado) | Detección de orientación en `recognize.py` (altura media de peones/reyes) + parámetro `flipped` (auto/si/no) en cli, api y web ("Tablero girado") | El auto-giro por peones era ruidoso: giraba de más en libro impreso (que SIEMPRE va con blancas abajo) y regresó libro_diag5 (35→26). Decisión medida: **auto NO rota, solo avisa**; el giro se aplica con "Tablero girado". Con `flipped=si`, tablero2 mejora 39→50 | Global se mantiene en **76,2%** (sin regresiones); tablero2 girado a mano 39→50. 112 tests |

## Iteración con Claude (asistente) · 13:00

| Hora | Cambio | Qué se hizo | Resultado |
|---|---|---|---|
| 12:25 | Depuración tablero2_digital | Se dibujó la rejilla sobre el tablero rectificado: la rejilla era correcta pero el diagrama está GIRADO (1 arriba, h..a abajo). Kiro implementó `flipped` (auto avisa / sí rota) | tablero2: 39 → 50/64 con "Tablero girado" |
| 13:00 | Prueba HOLD-OUT (diagramas no vistos) | Primera evaluación de `samples/holdout/`: tablero6_digital 57/64; libro_diag23 **15/64** → el marco del libro no cerraba contorno (número "23" pegado) y se usaba el recorte por proyecciones | Detectado fallo real de generalización |
| 13:00 | `board.py`: `_frame_box` | Detección del marco de libro por líneas oscuras largas (apertura morfológica ≥50 % del lado) antes del fallback | libro_diag23 (hold-out): **15 → 45/64**; dev sin cambios (76,4 %); 112 tests en verde |
| 13:00 | Prueba descartada | Clasificador vecino-más-cercano por correlación (NCC) por estilo, validación leave-one-board-out | 60,7 % → peor que el SVC actual; no se integra |
| 13:25 | Spec 2 `anotaciones-diagrama` (tareas 1–4) | `annotations.py`: resaltados por HSV del anillo de la casilla (amarillo claro/oscuro, rojo), flechas por máscara naranja → casillas en cruz → punta = máximo de la transformada de distancia; salida en formato ONCE (`)Resaltadas…(`, `c⠂¬⠒⠕¬f⠂`) integrada en API, web y demo | Resaltados **12/12** (incl. hold-out); flechas 4/8: fallan las flechas de caballo que salen juntas de una casilla (tablero6, hold-out) |
| 14:05 | Guía por voz (idea del equipo) | `guia-voz.js`: botón "Activar guía por voz" + Alt+G; lee el nombre del control al recibir foco (Tab) o con el ratón encima (350 ms), incluidos estado de opciones/casillas y el archivo elegido. Desactivada por defecto para no duplicar al lector de pantalla. Nueva regla R36 | Probado en GitHub Pages |
