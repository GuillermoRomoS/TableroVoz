# Implementation Plan

## Sprint 1 · 11:00–13:00 · Diseño + Desarrollo (checkpoint diseño ≈13:30)
- [ ] 1. Revisar requirements y design con `samples/` (10 diagramas oficiales con FEN, braille y metadatos ya preparados)
  - _Requirements: 2.4_
- [x] 2. Crear proyecto Python (requirements.txt, paquete `tablerovoz`, pytest) y `KIRO-LOG.md`
- [x] 3. Implementar `describe.py` (formato audio ONCE, voz, por filas) con tests contra `samples/libro_diag1_p15` y `libro_diag23_p44`
  - _Requirements: 5.1, 5.2, 5.3_
  - _Nota: `libro_diag23_p44` está en `samples/holdout/` y R31 lo reserva para el Sprint 3; se testeó contra `libro_diag1_p15` (texto de audio oficial) + tablero1..5._
- [x] 3b. Implementar `braille.py` (FEN → formato ONCE) con tests que reproduzcan exactamente las líneas Blancas/Negras de `samples/tablero*_digital.braille.txt`
  - _Requirements: 8.1, 8.2, 8.3_
- [x] 4. Implementar `validate.py` con tests
  - _Requirements: 3.1, 3.2_
- [x] 5. Implementar `synth.py` (diagramas sintéticos con FEN conocido)
  - _Requirements: 2.4_
  - _Nota: cairo no está disponible en este Windows; el backend PNG por defecto usa solo Pillow (tablero + sprites recortados de samples de desarrollo, sin holdout). `cairosvg` queda como opcional._

## Sprint 2 · 13:45–15:45 · Desarrollo + Integración (checkpoint E2E 14:45)
- [x] 6. Implementar `board.py` (detección, rectificación, 64 casillas) probando con sintéticos y `samples/`
  - _Requirements: 2.1, 1.2_
- [x] 7. Implementar `tiles.py` + `train.py` + `eval.py`; objetivo ≥ 98 % por casilla en sintéticos
  - _Requirements: 2.2, 2.3, 2.4_
  - _Estado: sintético held-out ≈ 97 %; samples reales ≈ 73 % por casilla. La mejora de precisión (sobre todo tablero de libro) queda pendiente para la vuelta con `eval.py`._
  - _También: `tablerovoz/recognize.py` une board+tiles+validate en un pipeline reutilizable; `tablerovoz/cli.py` (imagen → braille ONCE + audio ONCE + FEN)._
- [x] 8. Implementar `api.py` y `web/` mínimos: subir imagen → FEN → descripción leída en `aria-live` (**flujo E2E antes de las 14:45**)
  - _Requirements: 1.1, 5.4, 7.2_
  - _E2E verificado por HTTP y CLI con `tablero5_digital` y `libro_diag1_p15`. Añadido `Dockerfile` + `.dockerignore` (uvicorn en `$PORT`) listo para la nube._
- [ ] 9. Implementar `vision_llm.py` + `fuse.py` si hay Bedrock; si no, saltar
  - _Requirements: 2.5_

## Sprint 3 · 15:45–16:45 · Cierre y pulido
- [ ] 10. Tabla 8×8 accesible, consultar casilla, tablero girado, turno, voz
  - _Requirements: 4.2, 4.3, 6.1, 6.2, 7.1, 7.3_
- [ ] 11. Ejecutar `eval.py` en `samples/` y, por primera vez, en `samples/holdout/` + diagramas nuevos buscados hoy, corregir los errores más frecuentes, anotar cifras en `KIRO-LOG.md`
  - _Requirements: 2.4_
- [ ] 12. Prueba con NVDA/VoiceOver con los ojos cerrados montando la posición; README y guion de demo
  - _Requirements: 7.1_
