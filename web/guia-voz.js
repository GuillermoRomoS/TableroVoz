"use strict";
// Guía por voz (opcional): lee en voz alta el control que tiene el foco (Tab) o el que está bajo el ratón.
// Pensada para personas con baja visión o que no usan lector de pantalla. Desactivada por defecto
// para no pisar a NVDA / Narrador / VoiceOver, que ya leen los controles por sí mismos.
(function () {
  const btn = document.getElementById("btn-guia");
  if (!btn || !("speechSynthesis" in window)) { if (btn) btn.hidden = true; return; }
  let activa = false;
  try { activa = localStorage.getItem("tv-guia-voz") === "1"; } catch (e) { /* sin almacenamiento */ }
  let ultimo = null, temporizador = null;

  const TIPOS = { BUTTON: "botón", SELECT: "lista", TEXTAREA: "campo de texto" };

  function textoDe(el) {
    if (el.getAttribute("aria-label")) return el.getAttribute("aria-label");
    if (el.id) {
      const lab = document.querySelector(`label[for="${el.id}"]`);
      if (lab) return lab.textContent.trim();
    }
    const padre = el.closest("label");
    if (padre) return padre.textContent.trim();
    return (el.textContent || el.value || el.title || "").trim();
  }

  function describir(el) {
    const nombre = textoDe(el);
    if (el.tagName === "INPUT") {
      if (el.type === "file") return `${nombre}. Botón para elegir la imagen. ${el.files && el.files.length ? "Imagen elegida: " + el.files[0].name : "Ninguna imagen elegida"}.`;
      if (el.type === "radio") { const g = el.closest("fieldset")?.querySelector("legend")?.textContent.trim(); return `${g ? g + ". " : ""}${nombre}. Opción ${el.checked ? "marcada" : "sin marcar"}.`; }
      if (el.type === "checkbox") return `${nombre}. Casilla ${el.checked ? "marcada" : "sin marcar"}.`;
      return `${nombre}. Campo de texto.`;
    }
    if (el.tagName === "TD" || el.tagName === "TH") return el.textContent.trim();
    return `${nombre}. ${TIPOS[el.tagName] || ""}`.trim();
  }

  function decir(texto) {
    if (!activa || !texto) return;
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(texto);
    u.lang = "es-ES"; u.rate = 1.05;
    speechSynthesis.speak(u);
  }

  function objetivo(el) { return el && el.closest ? el.closest("button, input, select, textarea, a[href], td, th") : null; }

  function anunciar(el, retraso) {
    const t = objetivo(el);
    if (!t || t === ultimo) return;
    ultimo = t;
    clearTimeout(temporizador);
    temporizador = setTimeout(() => decir(describir(t)), retraso);
  }

  // --- Orientación espacial: texto bajo el ratón y dirección al control más cercano ---
  const CONTROLES = "button, input, select, textarea, a[href]";
  const TEXTO = "h1, h2, h3, p, legend, label, pre, code, li, span, td, th";

  function visibles() {
    return [...document.querySelectorAll(CONTROLES)].filter((el) => el.offsetParent !== null && !el.disabled);
  }

  function direccion(dx, dy) {
    const v = Math.abs(dy) < 25 ? "" : dy > 0 ? "abajo" : "arriba";
    const h = Math.abs(dx) < 40 ? "" : dx > 0 ? "a la derecha" : "a la izquierda";
    return [v, h].filter(Boolean).join(" y ") || "justo aquí";
  }

  function distancia(px) { return px < 120 ? "muy cerca" : px < 350 ? "cerca" : "más lejos"; }

  function masCercano(x, y, excluir) {
    let mejor = null, dmin = Infinity;
    for (const el of visibles()) {
      if (el === excluir) continue;
      const r = el.getBoundingClientRect();
      const cx = Math.max(r.left, Math.min(x, r.right)), cy = Math.max(r.top, Math.min(y, r.bottom));
      const d = Math.hypot(cx - x, cy - y);
      if (d < dmin) { dmin = d; mejor = { el, dx: (r.left + r.right) / 2 - x, dy: (r.top + r.bottom) / 2 - y, d }; }
    }
    return mejor;
  }

  function indicacion(x, y, excluir) {
    const c = masCercano(x, y, excluir);
    if (!c) return "";
    return ` Lo más cercano: ${textoDe(c.el) || "un control"}, ${direccion(c.dx, c.dy)}, ${distancia(c.d)}.`;
  }

  function recortar(t, n = 220) { t = t.replace(/\s+/g, " ").trim(); return t.length > n ? t.slice(0, n) + "…" : t; }

  let ultimoTexto = null, reposo = null;
  document.addEventListener("focusin", (e) => anunciar(e.target, 0));
  document.addEventListener("mouseover", (e) => anunciar(e.target, 350));
  document.addEventListener("mouseout", (e) => { if (!objetivo(e.relatedTarget)) { ultimo = null; clearTimeout(temporizador); } });
  document.addEventListener("change", (e) => { ultimo = null; anunciar(e.target, 0); });

  // Ratón quieto sobre texto o sobre una zona vacía: lee el texto (si lo hay) y orienta hacia el botón más cercano.
  document.addEventListener("mousemove", (e) => {
    if (!activa) return;
    clearTimeout(reposo);
    const x = e.clientX, y = e.clientY, t = e.target;
    reposo = setTimeout(() => {
      if (objetivo(t) && t.closest(CONTROLES)) return; // los controles ya se anuncian solos
      const bloque = t.closest ? t.closest(TEXTO) : null;
      const clave = bloque || "vacio:" + Math.round(x / 80) + "," + Math.round(y / 80);
      if (clave === ultimoTexto) return;
      ultimoTexto = clave;
      ultimo = null;
      const txt = bloque ? recortar(bloque.textContent) : ""; const texto = bloque ? (/[.!?…:]$/.test(txt) ? txt : txt + ".") : "Zona sin controles.";
      decir(texto + indicacion(x, y));
    }, 700);
  });

  // Alt + D: "¿dónde estoy?" — control con foco y los controles anterior y siguiente.
  function dondeEstoy() {
    const lista = visibles();
    const i = lista.indexOf(document.activeElement);
    if (i < 0) { decir("Ningún control tiene el foco. Pulsa Tabulador para empezar. El primero es: " + textoDe(lista[0]) + "."); return; }
    const partes = ["Estás en: " + describir(lista[i])];
    if (lista[i + 1]) partes.push("Siguiente con Tabulador: " + textoDe(lista[i + 1]) + ".");
    if (lista[i - 1]) partes.push("Anterior con Mayúsculas más Tabulador: " + textoDe(lista[i - 1]) + ".");
    decir(partes.join(" "));
  }
  document.addEventListener("keydown", (e) => { if (activa && e.altKey && (e.key === "d" || e.key === "D")) { e.preventDefault(); dondeEstoy(); } });

  function pintar() {
    btn.setAttribute("aria-pressed", String(activa));
    btn.textContent = activa ? "Guía por voz: activada (pulsa para desactivar)" : "Activar guía por voz";
  }
  btn.addEventListener("click", () => {
    activa = !activa;
    try { localStorage.setItem("tv-guia-voz", activa ? "1" : "0"); } catch (e) { /* nada */ }
    pintar();
    if (activa) { ultimo = btn; decir("Guía por voz activada. Pulsa Tabulador para recorrer la página y te leeré cada botón. Si mueves el ratón, te leo el texto y te digo dónde está el botón más cercano. Alt más D te dice dónde estás. Primero: elige la imagen del diagrama."); }
    else speechSynthesis.cancel();
  });
  // Atajo: Alt + G activa o desactiva la guía desde cualquier punto.
  document.addEventListener("keydown", (e) => { if (e.altKey && (e.key === "g" || e.key === "G")) { e.preventDefault(); btn.click(); } });
  pintar();
})();
