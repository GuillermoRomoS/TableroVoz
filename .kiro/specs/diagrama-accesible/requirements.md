# Requirements Document

## Introduction
TableroVoz convierte la imagen de un diagrama de ajedrez en una descripción accesible para personas ciegas. Tres pasos: modelado, reconocimiento y traducción accesible. Formato EARS.

## Requirements

### Requirement 1 – Entrada de la imagen
**User Story:** Como persona ciega (o quien le ayuda), quiero subir o pegar la imagen de un diagrama, para conocer la posición.
#### Acceptance Criteria
1. WHEN el usuario sube una imagen PNG/JPG o la pega desde el portapapeles THE SYSTEM SHALL iniciar el reconocimiento y anunciar "Reconociendo el diagrama…".
2. IF no se detecta un tablero THEN THE SYSTEM SHALL decirlo y sugerir recortar la imagen al diagrama.

### Requirement 2 – Reconocimiento de tablero y piezas
**User Story:** Como usuario, quiero que la posición se reconozca correctamente, para poder confiar en ella.
#### Acceptance Criteria
1. WHEN hay un tablero en la imagen THE SYSTEM SHALL localizarlo, rectificarlo y dividirlo en 64 casillas.
2. THE SYSTEM SHALL clasificar cada casilla como vacía o una de las 12 piezas y producir un FEN.
3. THE SYSTEM SHALL calcular una confianza por casilla.
4. THE SYSTEM SHALL alcanzar ≥ 98 % de casillas correctas en el banco de diagramas sintéticos de test y medirlo en `samples/` reales.
5. WHERE hay credenciales de Bedrock THE SYSTEM SHALL usar el modelo multimodal como segunda opinión y fusionar ambos resultados.

### Requirement 3 – Validación ajedrecística
#### Acceptance Criteria
1. THE SYSTEM SHALL comprobar: un rey por bando, ≤ 8 peones por bando, ningún peón en filas 1 u 8, ≤ 16 piezas por bando.
2. IF la validación falla THEN THE SYSTEM SHALL marcar como dudosas las casillas implicadas y avisarlo al final de la descripción.

### Requirement 4 – Orientación y turno
#### Acceptance Criteria
1. THE SYSTEM SHALL asumir blancas abajo salvo que detecte coordenadas impresas que indiquen lo contrario.
2. WHEN el usuario activa "Tablero girado" THE SYSTEM SHALL rotar 180° la posición y volver a describirla.
3. THE SYSTEM SHALL exigir el turno (Juegan blancas / Juegan negras) mediante un selector obligatorio, con blancas preseleccionado, e incluirlo en el FEN, en la salida braille y en la de audio.
4. WHERE el diagrama muestre un indicador de turno THE SYSTEM SHALL proponerlo automáticamente, y el usuario podrá cambiarlo.

### Requirement 5 – Salida para audio / lector de pantalla (formato ONCE)
**User Story:** Como jugador ciego, quiero oír la posición en el formato que usa la ONCE, para montarla en mi tablero adaptado.
#### Acceptance Criteria
1. THE SYSTEM SHALL generar el texto con el formato de `chess-notation.md` (orden Rey, Dama, Torres, Alfiles, Caballos, Peones; "Torres en C1 y H1").
2. THE SYSTEM SHALL producir la misma salida para la misma posición (determinista).
3. THE SYSTEM SHALL ofrecer lectura con voz sintética y modo "por filas".
4. THE SYSTEM SHALL mostrar y permitir copiar el FEN.
### Requirement 6 – Exploración del tablero
#### Acceptance Criteria
1. THE SYSTEM SHALL mostrar un tablero como tabla HTML 8×8 con encabezados de fila y columna y texto en cada celda.
2. WHEN el usuario escribe una casilla (p. ej. "e4") en "Consultar casilla" THE SYSTEM SHALL responder qué hay en ella.

### Requirement 7 – Accesibilidad de la interfaz
#### Acceptance Criteria
1. THE SYSTEM SHALL poder usarse completo con teclado y lector de pantalla (NVDA / VoiceOver).
2. WHEN hay un resultado THE SYSTEM SHALL anunciarlo en `aria-live` y mover el foco al encabezado "Posición".
3. THE SYSTEM SHALL comunicar las dudas con texto, no solo con color.

### Requirement 8 – Salida braille (formato ONCE / Ebrai)
**User Story:** Como jugador ciego que lee braille, quiero la posición en el formato de adaptación de la ONCE, para leerla en línea braille o imprimirla con Ebrai.
#### Acceptance Criteria
1. THE SYSTEM SHALL generar `Tablero:` / `Blancas:` / `Negras:` según `braille.md` (letras en tinta, filas en números braille en posición baja, orden R D T C A peones).
2. WHEN se ejecutan los tests THE SYSTEM SHALL reproducir exactamente las líneas de `samples/tablero*_digital.braille.txt` a partir de su `.fen`.
3. THE SYSTEM SHALL escribir los peones siempre sin letra (decisión confirmada por la ONCE).
4. THE SYSTEM SHALL permitir copiar y descargar la salida como `.txt`.

> Casillas resaltadas y flechas: ver la segunda spec `anotaciones-diagrama`.
