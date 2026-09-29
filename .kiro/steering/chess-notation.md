---
inclusion: fileMatch
fileMatchPattern: ["tablerovoz/describe.py", "tests/**", "web/**"]
---
# Salida audio / lector de pantalla — formato oficial ONCE

R16. Formato: `Blancas: Rey en E2, Dama en A4, Torres en C1 y H1, Alfil en B5, Caballos en C3 y F3, Peones en A2, B2 y H2.`
R17. Orden audio: Rey, Dama, Torres, Alfiles, Caballos, Peones (alfiles ANTES que caballos, al revés que en braille).
R18. Singular/plural según cantidad; enumeración con comas y "y" antes del último; omitir tipos sin piezas.
R19. Casillas con columna en MAYÚSCULA + número (E2); dentro del tipo, columna A→H y luego fila ascendente.
R20. Tras Negras, siempre el turno: "Juegan blancas." / "Juegan negras."
R21. Resaltados y flechas al final: "Resaltadas en amarillo las casillas G3 y H4. Flecha de C1 a F1."
R22. Misma posición → misma salida (determinista). Siempre mostrar y permitir copiar el FEN.
R23. La imagen es la verdad: los textos de ejemplo de la ONCE tienen errores (diag. 2 y 5, ver samples/*.meta.json).
