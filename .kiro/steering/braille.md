---
inclusion: fileMatch
fileMatchPattern: ["tablerovoz/describe.py", "tablerovoz/braille.py", "tests/**", "web/**"]
---
# Salida braille — formato oficial ONCE / Ebrai (ver samples/REFERENCIA_ONCE.txt)

R08. La salida braille debe coincidir carácter a carácter con `samples/tablero*_digital.braille.txt`.
R09. Estructura: línea `Tablero:`, luego `Blancas: …`, luego `Negras: …`, luego `Juegan blancas.` o `Juegan negras.`
R10. Pieza = letra en tinta R, D, T, C, A (sin signo braille); peones SIN letra (confirmado por la ONCE).
R11. Casilla = columna en tinta a–h + fila en braille posición baja: 1⠂ 2⠆ 3⠒ 4⠲ 5⠢ 6⠖ 7⠶ 8⠦ (ej. Re⠂, e⠲).
R12. Orden braille: R, D, T, C, A, peones (caballos ANTES que alfiles); dentro del tipo, columna a→h y luego fila ascendente.
R13. Separador: un espacio entre piezas.
R14. Resaltadas: `)Resaltadas en amarillo las casillas g⠒ y h⠲(`; con dos colores: `… y, en rojo, f⠖`.
R15. Flechas: `origen¬⠒⠕¬destino` (→) o `¬⠪⠒¬` (←), una por línea dentro del bloque de observaciones.
