# Requirements Document – Anotaciones del diagrama (resaltados y flechas)

## Introduction
Los diagramas digitales del libro resaltan casillas (amarillo, rojo) y dibujan flechas para explicar la jugada. Sin ellas, el lector ciego pierde la explicación. Esta spec las detecta y las transcribe en el formato de la ONCE.

## Requirements

### Requirement 1 – Casillas resaltadas
**User Story:** Como lector ciego, quiero saber qué casillas destaca el diagrama, porque el texto del libro se refiere a ellas.
#### Acceptance Criteria
1. WHEN una casilla tiene fondo amarillo o rojo THE SYSTEM SHALL detectarla y clasificar su color.
2. THE SYSTEM SHALL escribirlas en braille como `)Resaltadas en amarillo las casillas g⠒ y h⠲(` y en audio como "Resaltadas en amarillo las casillas G3 y H4."
3. THE SYSTEM SHALL acertar los resaltados de todos los `samples/tablero*_digital.meta.json`.

### Requirement 2 – Flechas
**User Story:** Como lector ciego, quiero conocer las flechas del diagrama, porque indican la jugada o la amenaza.
#### Acceptance Criteria
1. WHEN hay una flecha THE SYSTEM SHALL detectar su casilla de origen y de destino (punta).
2. THE SYSTEM SHALL escribirla como `c⠂¬⠒⠕¬f⠂` en braille y "Flecha de C1 a F1." en audio.
3. IF una flecha no se puede resolver con seguridad THEN THE SYSTEM SHALL decir "Hay una flecha que no he podido leer" en lugar de inventarla.

### Requirement 3 – Ruido
#### Acceptance Criteria
1. THE SYSTEM SHALL ignorar insignias de anotación ("!", "?") superpuestas a piezas.
2. WHERE el diagrama es de libro impreso THE SYSTEM SHALL no buscar resaltados ni flechas.
