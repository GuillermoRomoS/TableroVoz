---
inclusion: always
---
# Accesibilidad (usuario ciego con lector de pantalla)

R01. La salida principal es texto que se escucha bien con lector de pantalla (NVDA, Narrador, VoiceOver); toda salida se valida ESCUCHÁNDOLA, no leyéndola en pantalla.
R02. Cada resultado nuevo se anuncia en una región `aria-live="polite"` y el foco pasa al encabezado "Posición".
R03. El tablero se ofrece también como `<table>` 8×8 con `th scope` (a–h, 8–1) y texto en cada celda ("e4, peón blanco").
R04. Campo "Consultar casilla" con `label`: escribir "e4" responde "En E4 hay un peón blanco".
R05. Ninguna información solo visual: las dudas, colores y flechas se dicen con texto.
R06. HTML semántico, un solo `h1`, botones con texto, foco visible, contraste ≥ 7:1, zoom 200 %.
R07. Estados y errores se anuncian en frases cortas y dicen qué hacer ("No encuentro el tablero. Recorta la imagen al diagrama.").
R36. Guía por voz opcional (desactivada por defecto, Alt+G): lee el control con foco o bajo el ratón, el texto bajo el ratón y la dirección y distancia del botón más cercano; Alt+D dice dónde estás y cuáles son el control anterior y el siguiente. Nunca activa por defecto para no pisar a NVDA/Narrador/VoiceOver.
