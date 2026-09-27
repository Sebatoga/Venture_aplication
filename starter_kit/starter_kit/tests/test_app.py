"""
Tests del EJERCICIO 6.

Te damos DOS: el camino feliz y el camino de abstención, que es el que de
verdad importa. Agrega al menos DOS más — el caso `DUDOSO` y algún borde
(pregunta vacía, workspace inexistente, pregunta sin ninguna palabra en común
con el corpus).

Fíjate que estos tests no levantan el servidor: llaman a `consultar()`
directamente. Si tu lógica quedó atrapada dentro del handler HTTP, no vas a
poder escribirlos, y eso ya es una señal sobre el diseño.
"""

import pytest

import app
from app import UMBRAL_MINIMO, consultar


@pytest.mark.asyncio
async def test_pregunta_sustentada_devuelve_respuesta_con_fuente():
    r = await consultar("¿Cuántos días de garantía tiene el plan Pro?", "acme")

    assert r["veredicto"] == "APROBADO"
    assert r["respuesta"] is not None
    assert "15 días" in r["respuesta"]
    assert r["fragmentos"][0]["source_id"] == "src-1"
    assert r["fragmentos"][0]["similitud"] >= UMBRAL_MINIMO


@pytest.mark.asyncio
async def test_pregunta_sin_evidencia_no_inventa_respuesta():
    # El corpus no dice nada del plan Enterprise. El recuperador igual devuelve
    # fragmentos parecidos —habla de planes y de garantías— pero ninguno responde.
    r = await consultar("¿cuánto dura la garantía del plan Enterprise?", "acme")

    assert r["veredicto"] == "SIN_EVIDENCIA"
    assert r["respuesta"] is None
    assert r["fragmentos"], "el recuperador sí devolvió fragmentos"
    assert r["fragmentos"][0]["similitud"] < UMBRAL_MINIMO
    assert "0.55" in r["motivo"] or "55" in r["motivo"], "el motivo debe citar el umbral"


# --- TUS TESTS AQUÍ ---


def test_pagina_formulario_tiene_fallback_get_y_campos_api():
    assert '<form id="f" action="/api/consulta" method="get">' in app.PAGINA
    assert 'id="q" name="q"' in app.PAGINA
    assert 'id="ws" name="ws"' in app.PAGINA
    assert '<button type="submit">' in app.PAGINA


@pytest.mark.asyncio
async def test_pregunta_dudosa_conserva_el_fragmento_literal(monkeypatch):
    async def fake_search(_pregunta):
        return [{"source_id": "src-test", "texto": "Texto dudoso", "similitud": 0.60}]

    monkeypatch.setattr(app.retriever, "search", fake_search)
    r = await consultar("¿Cuántos días de garantía tiene el plan Pro?", "acme")

    assert r["veredicto"] == "DUDOSO"
    assert r["respuesta"] == "Texto dudoso"
    assert "0.600" in r["motivo"]


@pytest.mark.asyncio
async def test_pregunta_vacia_no_inventa_respuesta():
    r = await consultar("", "acme")

    assert r["intencion"] == "desconocido"
    assert r["veredicto"] == "SIN_EVIDENCIA"
    assert r["respuesta"] is None


@pytest.mark.asyncio
async def test_motivo_de_umbral_conserva_el_puntaje(monkeypatch):
    async def fake_search(_pregunta):
        return [{"source_id": "src-test", "texto": "Texto irrelevante", "similitud": 0.549}]

    monkeypatch.setattr(app.retriever, "search", fake_search)
    r = await consultar("¿Cuántos días de garantía tiene el plan Pro?", "acme")

    assert r["veredicto"] == "SIN_EVIDENCIA"
    assert "0.549" in r["motivo"]
    assert "0.55" in r["motivo"]


def test_http_console_success_invalid_route_query_and_internal_error(monkeypatch):
    import json
    import threading
    from http.server import HTTPServer
    from urllib.request import urlopen
    from urllib.error import HTTPError

    server = HTTPServer(("127.0.0.1", 0), app.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"

    def get(path):
        try:
            with urlopen(base + path) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            return error.code, json.load(error)

    try:
        status, data = get("/api/consulta?q=garant%C3%ADa%20del%20plan%20Pro")
        assert status == 200
        assert data["veredicto"] == "APROBADO"

        status, data = get("/no-existe")
        assert status == 404
        assert data == {"error": "no encontrado"}

        status, data = get("/api/consulta?q=")
        assert status == 400
        assert "error" in data

        async def fail(_pregunta, _workspace):
            raise RuntimeError("secret internal detail")

        monkeypatch.setattr(app, "consultar", fail)
        status, data = get("/api/consulta?q=hola")
        assert status == 500
        assert data == {"error": "error interno, revisa la consola"}
        assert "secret" not in json.dumps(data)
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_http_console_html_fallback_escapes_result(monkeypatch):
    import threading
    from http.server import HTTPServer
    from urllib.request import Request, urlopen

    async def fake_consultar(_pregunta, _workspace):
        return {
            "pregunta": '<script>alert("q")</script>',
            "workspace": 'acme & <x>',
            "intencion": "facturacion",
            "especialista": "billing_agent",
            "fragmentos": [{
                "source_id": "src-1",
                "titulo": '<img src=x onerror=alert(1)>',
                "texto": "Fuente & texto",
                "similitud": 0.91,
            }],
            "veredicto": "APROBADO",
            "motivo": "Motivo <seguro>",
            "respuesta": 'Respuesta "con evidencia"',
        }

    monkeypatch.setattr(app, "consultar", fake_consultar)
    server = HTTPServer(("127.0.0.1", 0), app.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        request = Request(
            f"http://127.0.0.1:{server.server_port}/api/consulta?q=pregunta&ws=acme",
            headers={"Accept": "text/html,application/xhtml+xml"},
        )
        with urlopen(request) as response:
            body = response.read().decode("utf-8")
            assert response.headers["Content-Type"].startswith("text/html")
        assert "<script>alert" not in body
        assert "&lt;script&gt;alert(&quot;q&quot;)&lt;/script&gt;" in body
        assert "&lt;img src=x onerror=alert(1)&gt;" in body
        assert "Fuente &amp; texto" in body
        assert "Respuesta &quot;con evidencia&quot;" in body
        assert "APROBADO" in body
        assert "0.91" in body
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_http_console_html_validation_errors_stay_in_console():
    import threading
    from http.server import HTTPServer
    from urllib.error import HTTPError
    from urllib.request import Request, urlopen

    server = HTTPServer(("127.0.0.1", 0), app.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"

    def get(path):
        request = Request(
            base + path,
            headers={"Accept": "text/html,application/xhtml+xml"},
        )
        try:
            with urlopen(request) as response:
                return response.status, response.headers["Content-Type"], response.read().decode("utf-8")
        except HTTPError as error:
            return error.code, error.headers["Content-Type"], error.read().decode("utf-8")

    try:
        status, content_type, body = get("/api/consulta?q=")
        assert status == 400
        assert content_type.startswith("text/html")
        assert "la consulta q es obligatoria" in body
        assert 'href="/"' in body

        status, content_type, body = get("/api/consulta?q=hola&ws=")
        assert status == 400
        assert content_type.startswith("text/html")
        assert "el workspace ws es obligatorio" in body
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
