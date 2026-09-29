"use strict";

// Estado del último resultado, para el tablero navegable y "consultar casilla".
let currentFen = null;
let currentBoard = null; // mapa "e4" -> {piece, color} | null

const PIEZA_ES = {
  K: "rey", Q: "dama", R: "torre", B: "alfil", N: "caballo", P: "peón",
};

function $(id) { return document.getElementById(id); }

function setEstado(msg) { $("estado").textContent = msg; }

// --- Parseo de FEN a un mapa de casillas para el tablero navegable ---
function parseFen(fen) {
  const board = {};
  const files = ["a", "b", "c", "d", "e", "f", "g", "h"];
  const rows = fen.trim().split(" ")[0].split("/");
  for (let r = 0; r < 8; r++) {
    const rankNum = 8 - r; // primera fila del FEN = fila 8
    let col = 0;
    for (const ch of rows[r]) {
      if (/\d/.test(ch)) {
        col += parseInt(ch, 10);
      } else {
        const sq = files[col] + rankNum;
        board[sq] = {
          piece: ch.toUpperCase(),
          color: ch === ch.toUpperCase() ? "blanco" : "negro",
        };
        col += 1;
      }
    }
  }
  return board;
}

function describeCasilla(sq) {
  const info = currentBoard ? currentBoard[sq] : null;
  if (!info) return `En ${sq.toUpperCase()} no hay ninguna pieza.`;
  return `En ${sq.toUpperCase()} hay un ${PIEZA_ES[info.piece]} ${info.color}.`;
}

// --- Tabla 8x8 accesible (R03) ---
function buildTable(board, doubts) {
  const files = ["a", "b", "c", "d", "e", "f", "g", "h"];
  const doubtSet = new Set((doubts || []).map((d) => d.toLowerCase()));
  const table = document.createElement("table");
  table.className = "tablero";
  const caption = document.createElement("caption");
  caption.textContent = "Tablero: filas 8 a 1, columnas a a h.";
  table.appendChild(caption);

  // Cabecera de columnas.
  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  headRow.appendChild(document.createElement("th")); // esquina
  for (const f of files) {
    const th = document.createElement("th");
    th.scope = "col";
    th.textContent = f;
    headRow.appendChild(th);
  }
  thead.appendChild(headRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  for (let rank = 8; rank >= 1; rank--) {
    const tr = document.createElement("tr");
    const rowHead = document.createElement("th");
    rowHead.scope = "row";
    rowHead.textContent = String(rank);
    tr.appendChild(rowHead);
    for (let c = 0; c < 8; c++) {
      const sq = files[c] + rank;
      const td = document.createElement("td");
      const isDark = (c + rank) % 2 === 0;
      td.className = isDark ? "dark" : "light";
      const info = board[sq];
      if (info) {
        td.textContent = `${sq}, ${PIEZA_ES[info.piece]} ${info.color}`;
      } else {
        td.textContent = `${sq}, vacía`;
      }
      if (doubtSet.has(sq)) {
        td.classList.add("dudoso");
        td.textContent += " (dudosa)";
      }
      tr.appendChild(td);
    }
    tbody.appendChild(tr);
  }
  table.appendChild(tbody);

  const wrap = $("tabla-wrap");
  wrap.innerHTML = "";
  wrap.appendChild(table);
}

// --- Voz (speechSynthesis es-ES) ---
function hablar(texto) {
  if (!("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(texto);
  u.lang = "es-ES";
  window.speechSynthesis.speak(u);
}

// --- Rellenar el resultado y mover el foco a "Posición" (R02) ---
function mostrarResultado(data) {
  currentFen = data.fen;
  currentBoard = parseFen(data.fen);

  $("audio-texto").textContent = data.description.compact;
  $("braille-texto").textContent = data.braille;
  $("fen-texto").textContent = data.fen;

  const avisos = [];
  if (data.warnings && data.warnings.length) avisos.push(...data.warnings);
  if (data.doubts && data.doubts.length) {
    avisos.push("Casillas dudosas: " + data.doubts.join(", ").toUpperCase() + ".");
  }
  $("dudas-texto").textContent = avisos.length
    ? avisos.join(" ")
    : "Sin avisos. Todas las casillas con confianza suficiente.";

  buildTable(currentBoard, data.doubts);

  $("resultado").hidden = false;
  setEstado("Listo. Posición reconocida.");
  // Mover el foco al encabezado "Posición" (R02).
  $("posicion-h").focus();
}

// --- Envío del formulario de reconocimiento ---
$("form-recognize").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const file = $("imagen").files[0];
  if (!file) { setEstado("Elige una imagen primero."); return; }

  setEstado("Reconociendo el diagrama…");
  const fd = new FormData();
  fd.append("image", file);
  fd.append("turn", document.querySelector('input[name="turn"]:checked').value);
  fd.append("flipped", $("flipped").checked ? "true" : "false");

  try {
    const resp = await fetch("/api/recognize", { method: "POST", body: fd });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      setEstado(err.detail || "No pude reconocer el diagrama. Recorta la imagen al diagrama.");
      return;
    }
    const data = await resp.json();
    mostrarResultado(data);
  } catch (e) {
    setEstado("Error de red al reconocer el diagrama.");
  }
});

// --- Botones de voz ---
$("btn-voz").addEventListener("click", () => hablar($("audio-texto").textContent));
$("btn-parar-voz").addEventListener("click", () => window.speechSynthesis && window.speechSynthesis.cancel());
$("btn-filas").addEventListener("click", async () => {
  if (!currentFen) return;
  // Pedimos la descripción por filas al backend para mantener el formato determinista.
  const resp = await fetch("/api/describe", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fen: currentFen }),
  });
  if (resp.ok) {
    const data = await resp.json();
    hablar(data.description.ranks);
  }
});

// --- Copiar / descargar ---
async function copiar(texto, msg) {
  try { await navigator.clipboard.writeText(texto); setEstado(msg); }
  catch { setEstado("No pude copiar automáticamente; selecciona y copia a mano."); }
}
$("btn-copiar-braille").addEventListener("click", () => copiar($("braille-texto").textContent, "Braille copiado."));
$("btn-copiar-fen").addEventListener("click", () => copiar($("fen-texto").textContent, "FEN copiado."));
$("btn-descargar-braille").addEventListener("click", () => {
  const blob = new Blob([$("braille-texto").textContent + "\n"], { type: "text/plain;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "tablero.braille.txt";
  a.click();
  URL.revokeObjectURL(a.href);
});

// --- Consultar casilla (R04) ---
$("form-consulta").addEventListener("submit", (ev) => {
  ev.preventDefault();
  const val = $("casilla").value.trim().toLowerCase();
  if (!/^[a-h][1-8]$/.test(val)) {
    $("consulta-resultado").textContent = "Escribe una casilla válida, por ejemplo e4.";
    return;
  }
  if (!currentBoard) {
    $("consulta-resultado").textContent = "Primero reconoce un diagrama.";
    return;
  }
  $("consulta-resultado").textContent = describeCasilla(val);
});
