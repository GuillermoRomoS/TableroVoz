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

  document.addEventListener("focusin", (e) => anunciar(e.target, 0));
  document.addEventListener("mouseover", (e) => anunciar(e.target, 350));
  document.addEventListener("mouseout", (e) => { if (!objetivo(e.relatedTarget)) { ultimo = null; clearTimeout(temporizador); } });
  document.addEventListener("change", (e) => { ultimo = null; anunciar(e.target, 0); });

  function pintar() {
    btn.setAttribute("aria-pressed", String(activa));
    btn.textContent = activa ? "Guía por voz: activada (pulsa para desactivar)" : "Activar guía por voz";
  }
  btn.addEventListener("click", () => {
    activa = !activa;
    try { localStorage.setItem("tv-guia-voz", activa ? "1" : "0"); } catch (e) { /* nada */ }
    pintar();
    if (activa) { ultimo = btn; decir("Guía por voz activada. Pulsa Tabulador para recorrer la página; te leeré cada botón. Primero: elige la imagen del diagrama."); }
    else speechSynthesis.cancel();
  });
  // Atajo: Alt + G activa o desactiva la guía desde cualquier punto.
  document.addEventListener("keydown", (e) => { if (e.altKey && (e.key === "g" || e.key === "G")) { e.preventDefault(); btn.click(); } });
  pintar();
})();
