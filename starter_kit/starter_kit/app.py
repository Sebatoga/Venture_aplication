"""
Consola del Asistente — EJERCICIO 6.

Arranca así:

    python app.py            # http://localhost:8000

El servidor y el esqueleto de la página ya funcionan: si lo corres ahora mismo
verás la página, escribirás una pregunta y te devolverá un error porque
`consultar()` todavía no está implementada. Eso es lo que tú construyes.

NO agregues dependencias. Todo esto sale de la librería estándar a propósito:
nada de Flask, FastAPI, React ni CSS externo. Feo pero claro está bien —
no evaluamos diseño gráfico, evaluamos que se entienda lo que pasó.
"""

from __future__ import annotations

import asyncio
import html
import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from config.intents import classify_intent, specialist_for
from shared import retriever

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("consola")

PUERTO = 8000

# Umbrales de decisión. Son un punto de partida, no una verdad revelada:
# si los cambias, di por qué en NOTAS.md.
UMBRAL_MINIMO = 0.55   # por debajo de esto no hay evidencia suficiente
UMBRAL_ALTO = 0.75     # por debajo de esto la respuesta va marcada como dudosa


# ---------------------------------------------------------------------------
# LO QUE TIENES QUE IMPLEMENTAR
# ---------------------------------------------------------------------------

async def consultar(pregunta: str, workspace_id: str = "acme") -> dict:
    """Ejecuta el pipeline completo sobre una pregunta y devuelve qué pasó.

    Esta función es el corazón del ejercicio y debe ser **testeable sin
    levantar el servidor**: recibe texto, devuelve un diccionario.

    Pasos:

    1. **Clasificar** la intención con `config.intents.classify_intent`.
    2. **Recuperar** fragmentos con `shared.retriever.search`.
    3. **Decidir** el veredicto según el mejor puntaje de similitud:
       - `SIN_EVIDENCIA` si no hay fragmentos o el mejor queda por debajo de
         `UMBRAL_MINIMO`. En este caso **no se responde**: `respuesta` es
         `None`. Este camino es el más importante de los tres.
       - `DUDOSO` si el mejor está entre `UMBRAL_MINIMO` y `UMBRAL_ALTO`.
         Se responde, pero marcado para revisión.
       - `APROBADO` si el mejor llega a `UMBRAL_ALTO` o más.
    4. **Redactar**: en esta prueba no hay modelo de lenguaje ni llamadas a
       ninguna API. La "respuesta" es el texto literal del mejor fragmento.
       Así se garantiza que nada de lo que muestra la consola esté inventado.

    Devuelve exactamente esta forma (los tests y la página dependen de ella):

        {
          "pregunta":    "¿Cuántos días de garantía tiene el plan Pro?",
          "workspace":   "acme",
          "intencion":   "facturacion",
          "especialista": "billing_agent",     # o None si la intención es desconocida
          "fragmentos":  [ {source_id, titulo, chunk, texto, similitud}, ... ],
          "veredicto":   "APROBADO" | "DUDOSO" | "SIN_EVIDENCIA",
          "motivo":      "Similitud 0.37, por debajo del mínimo de 0.55",
          "respuesta":   "El plan Pro incluye…"   # None si SIN_EVIDENCIA
        }

    El `motivo` lo lee un humano cuando algo sale raro: que diga números.
    """
    intencion = classify_intent(pregunta)
    especialista = specialist_for(intencion)
    fragmentos = await retriever.search(pregunta)

    mejor = max(fragmentos, key=lambda fragmento: fragmento.get("similitud", 0), default=None)
    score = float(mejor.get("similitud", 0)) if mejor else 0.0

    if mejor is None:
        veredicto = "SIN_EVIDENCIA"
        motivo = "Similitud 0.000: no se recuperaron fragmentos (umbral mínimo 0.55)"
        respuesta = None
    elif score < UMBRAL_MINIMO:
        veredicto = "SIN_EVIDENCIA"
        motivo = f"Similitud {score:.3f}, por debajo del mínimo de {UMBRAL_MINIMO:.2f}"
        respuesta = None
    elif score < UMBRAL_ALTO:
        veredicto = "DUDOSO"
        motivo = (
            f"Similitud {score:.3f}, entre el mínimo de {UMBRAL_MINIMO:.2f} "
            f"y el umbral alto de {UMBRAL_ALTO:.2f}"
        )
        respuesta = mejor["texto"]
    else:
        veredicto = "APROBADO"
        motivo = f"Similitud {score:.3f}, igual o por encima del umbral alto de {UMBRAL_ALTO:.2f}"
        respuesta = mejor["texto"]

    return {
        "pregunta": pregunta,
        "workspace": workspace_id,
        "intencion": intencion,
        "especialista": especialista,
        "fragmentos": fragmentos,
        "veredicto": veredicto,
        "motivo": motivo,
        "respuesta": respuesta,
    }


# ---------------------------------------------------------------------------
# LA PÁGINA
#
# Esto es un esqueleto que funciona pero no sirve de mucho: vuelca el JSON en
# crudo. Tu trabajo es que un humano entienda de un vistazo qué hizo el
# asistente y por qué. Como mínimo debe verse:
#
#   - la intención detectada
#   - los fragmentos recuperados, cada uno con su puntaje de similitud
#   - el veredicto, visualmente distinto en los tres casos
#   - la respuesta final, o el aviso de que no hay evidencia suficiente
#
# Debe quedar imposible confundir "esto está sustentado" con "esto no lo sé".
# ---------------------------------------------------------------------------

PAGINA = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<title>Consola del Asistente</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 820px; margin: 40px auto;
         padding: 0 20px; color: #1a2330; }
  input[type=text] { width: 100%; padding: 10px; font-size: 16px; }
  button { padding: 10px 18px; font-size: 15px; cursor: pointer; }
  pre { background: #f2f4f7; padding: 14px; overflow-x: auto; white-space: pre-wrap; }
  .aprobado { border-left: 6px solid #198754; }
  .dudoso { border-left: 6px solid #f0ad4e; }
  .sin-evidencia { border-left: 6px solid #dc3545; }
</style>
</head><body>
  <h1>Consola del Asistente</h1>

  <form id="f" action="/api/consulta" method="get">
    <input type="text" id="q" name="q" placeholder="Escribe una pregunta…" autofocus>
    <p>
      <select id="ws" name="ws">
        <option value="acme">acme</option>
        <option value="globex">globex</option>
        <option value="initech">initech</option>
      </select>
      <button type="submit">Preguntar</button>
    </p>
  </form>

  <pre id="out">Escribe una pregunta para empezar.</pre>

<script>
document.getElementById('f').onsubmit = async (e) => {
  e.preventDefault();
  const q = document.getElementById('q').value;
  const ws = document.getElementById('ws').value;
  const out = document.getElementById('out');
  out.textContent = 'Consultando…';
  out.className = '';
  try {
    const r = await fetch(`/api/consulta?q=${encodeURIComponent(q)}&ws=${ws}`);
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || 'La consulta no pudo procesarse');
    const fragments = data.fragmentos.map((f) =>
      `- ${f.titulo || f.source_id} (similitud ${f.similitud})\n  ${f.texto}`
    ).join('\n');
    out.className = data.veredicto.toLowerCase().replace('_', '-');
    out.textContent = [
      `Veredicto: ${data.veredicto}`,
      `Intención: ${data.intencion}`,
      `Especialista: ${data.especialista || 'ninguno'}`,
      `Motivo: ${data.motivo}`,
      '',
      'Fragmentos recuperados:',
      fragments || '(ninguno)',
      '',
      `Respuesta: ${data.respuesta || 'No hay evidencia suficiente para responder.'}`,
    ].join('\n');
  } catch (err) {
    out.className = 'sin-evidencia';
    out.textContent = 'Error: ' + err.message;
  }
};
</script>
</body></html>
"""


def _html_result_page(data: dict) -> str:
    """Render a consultation result for browsers that do not run JavaScript."""
    escape = lambda value: html.escape(str(value), quote=True)
    fragments = data.get("fragmentos") or []
    fragment_html = "".join(
        "<li><strong>{}</strong> — similitud {}<br><span>{}</span></li>".format(
            escape(fragment.get("titulo") or fragment.get("source_id") or "(sin título)"),
            escape(fragment.get("similitud", "")),
            escape(fragment.get("texto", "")),
        )
        for fragment in fragments
    )
    if not fragment_html:
        fragment_html = "<li>(ninguno)</li>"
    respuesta = data.get("respuesta")
    answer_html = escape(respuesta) if respuesta is not None else "No hay evidencia suficiente para responder."
    verdict_class = escape(str(data.get("veredicto", "")).lower().replace("_", "-"))
    return """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<title>Resultado — Consola del Asistente</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 820px; margin: 40px auto;
         padding: 0 20px; color: #1a2330; }}
  input[type=text] {{ width: 100%; padding: 10px; font-size: 16px; }}
  button {{ padding: 10px 18px; font-size: 15px; cursor: pointer; }}
  section {{ padding: 14px; margin-top: 20px; background: #f2f4f7; }}
  .aprobado {{ border-left: 6px solid #198754; }}
  .dudoso {{ border-left: 6px solid #f0ad4e; }}
  .sin-evidencia {{ border-left: 6px solid #dc3545; }}
  li {{ margin: 10px 0; }}
</style></head><body>
  <h1>Consola del Asistente</h1>
  <form action="/api/consulta" method="get">
    <input type="text" name="q" value="{question}" autofocus>
    <p><select name="ws"><option value="{workspace}" selected>{workspace}</option></select>
    <button type="submit">Preguntar</button></p>
  </form>
  <section class="{verdict_class}">
    <h2>Resultado</h2>
    <p><strong>Pregunta:</strong> {question}</p>
    <p><strong>Workspace:</strong> {workspace}</p>
    <p><strong>Intención:</strong> {intention}</p>
    <p><strong>Veredicto:</strong> {verdict}</p>
    <p><strong>Motivo:</strong> {reason}</p>
    <h3>Fragmentos recuperados</h3>
    <ul>{fragment_html}</ul>
    <h3>Respuesta</h3>
    <p>{answer}</p>
  </section>
</body></html>""".format(
        question=escape(data.get("pregunta", "")),
        workspace=escape(data.get("workspace", "")),
        intention=escape(data.get("intencion", "")),
        verdict=escape(data.get("veredicto", "")),
        reason=escape(data.get("motivo", "")),
        answer=answer_html,
        verdict_class=verdict_class,
        fragment_html=fragment_html,
    )


def _html_error_page(message: str) -> str:
    """Render a readable validation error for browsers submitting the form."""
    return """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<title>Error — Consola del Asistente</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 820px; margin: 40px auto;
         padding: 0 20px; color: #1a2330; }}
  section {{ padding: 14px; margin-top: 20px; background: #f8d7da;
             border-left: 6px solid #dc3545; }}
  a {{ color: #0d6efd; }}
</style></head><body>
  <h1>Consola del Asistente</h1>
  <section><h2>No se pudo procesar la consulta</h2><p>{}</p></section>
  <p><a href="/">Volver a la consola</a></p>
</body></html>""".format(html.escape(message, quote=True))


def _prefers_html(accept: str) -> bool:
    """Return whether the client explicitly accepts HTML responses."""
    for media_range in accept.lower().split(","):
        media_type, *parameters = media_range.strip().split(";")
        if media_type.strip() != "text/html":
            continue
        quality = 1.0
        for parameter in parameters:
            name, _, value = parameter.strip().partition("=")
            if name == "q":
                try:
                    quality = float(value)
                except ValueError:
                    quality = 0.0
        return quality > 0
    return False


# ---------------------------------------------------------------------------
# SERVIDOR — ya funciona. Puedes tocarlo si lo necesitas, pero no hace falta.
# ---------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):

    def _send(self, code, body, content_type):
        payload = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        url = urlparse(self.path)

        if url.path in ("/", "/index.html"):
            return self._send(200, PAGINA, "text/html")

        if url.path == "/api/consulta":
            wants_html = _prefers_html(self.headers.get("Accept", ""))
            params = parse_qs(url.query, keep_blank_values=True)
            pregunta = (params.get("q") or [""])[0]
            workspace = (params.get("ws") or ["acme"])[0]
            if not isinstance(pregunta, str) or not pregunta.strip():
                if wants_html:
                    return self._send(
                        400,
                        _html_error_page("la consulta q es obligatoria"),
                        "text/html",
                    )
                return self._send(
                    400,
                    json.dumps({"error": "la consulta q es obligatoria"}, ensure_ascii=False),
                    "application/json",
                )
            if not isinstance(workspace, str) or not workspace.strip():
                if wants_html:
                    return self._send(
                        400,
                        _html_error_page("el workspace ws es obligatorio"),
                        "text/html",
                    )
                return self._send(
                    400,
                    json.dumps({"error": "el workspace ws es obligatorio"}, ensure_ascii=False),
                    "application/json",
                )
            try:
                data = asyncio.run(consultar(pregunta, workspace))
                if wants_html:
                    return self._send(200, _html_result_page(data), "text/html")
                return self._send(200, json.dumps(data, ensure_ascii=False), "application/json")
            except Exception:
                logger.exception("fallo al consultar %r", pregunta)
                return self._send(
                    500, json.dumps({"error": "error interno, revisa la consola"},
                                    ensure_ascii=False), "application/json")

        self._send(404, json.dumps({"error": "no encontrado"}), "application/json")

    def log_message(self, fmt, *args):
        logger.info("%s", fmt % args)


if __name__ == "__main__":
    print(f"\n  Consola del Asistente  →  http://localhost:{PUERTO}\n")
    HTTPServer(("127.0.0.1", PUERTO), Handler).serve_forever()
