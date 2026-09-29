"use strict";
// TableroVoz en GitHub Pages: ejecuta el backend Python (tablerovoz) dentro del navegador con Pyodide.
// Intercepta las llamadas de app.js a /api/recognize y /api/describe, así la misma web funciona sin servidor.
const PY_FILES = ["__init__", "board", "occupancy", "tiles", "recognize", "validate", "braille", "describe", "shape", "annotations"];
const estado = (m) => { const e = document.getElementById("estado"); if (e) e.textContent = m; };

const pyReady = (async () => {
  estado("Cargando el motor de reconocimiento (primera vez: 20–40 s)…");
  const py = await loadPyodide();
  await py.loadPackage(["numpy", "opencv-python", "scikit-learn", "joblib", "micropip"]);
  const micropip = py.pyimport("micropip");
  await micropip.install(new URL("wheels/chess-1.11.2-py3-none-any.whl", location.href).href);
  py.FS.mkdirTree("/home/pyodide/tablerovoz");
  py.FS.mkdirTree("/home/pyodide/models");
  for (const f of PY_FILES) {
    const src = await (await fetch(`py/tablerovoz/${f}.py`)).text();
    py.FS.writeFile(`/home/pyodide/tablerovoz/${f}.py`, src);
  }
  py.FS.writeFile("/home/pyodide/web_bridge.py", await (await fetch("py/web_bridge.py")).text());
  py.FS.writeFile("/home/pyodide/models/tiles.joblib", new Uint8Array(await (await fetch("models/tiles.joblib")).arrayBuffer()));
  py.runPython("import sys; sys.path.insert(0, '/home/pyodide')");
  const bridge = py.pyimport("web_bridge");
  estado("Motor listo. Elige una imagen de un diagrama.");
  return { py, bridge };
})().catch((e) => { console.error(e); estado("No se pudo cargar el motor en este navegador. Prueba con Chrome, Edge o Firefox actualizados."); throw e; });

const _fetch = window.fetch.bind(window);
function jsonResponse(text) {
  const data = JSON.parse(text);
  const status = data.status || 200; delete data.status;
  return new Response(JSON.stringify(data), { status, headers: { "Content-Type": "application/json" } });
}
window.fetch = async (input, init = {}) => {
  const url = typeof input === "string" ? input : input.url;
  if (url.endsWith("/api/recognize")) {
    const { bridge } = await pyReady;
    const fd = init.body;
    const bytes = new Uint8Array(await fd.get("image").arrayBuffer());
    return jsonResponse(bridge.api_recognize(bytes, fd.get("turn") || "w", fd.get("flipped") || "false"));
  }
  if (url.endsWith("/api/describe")) {
    const { bridge } = await pyReady;
    const body = JSON.parse(init.body || "{}");
    return jsonResponse(bridge.api_describe(body.fen || "", body.turn || "w"));
  }
  return _fetch(input, init);
};
