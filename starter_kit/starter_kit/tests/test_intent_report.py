"""
Tests del EJERCICIO 2.

Te damos UN test de ejemplo para que veas el estilo. Debes agregar al menos
CUATRO más, cubriendo:

  - un workspace con mensajes variados (verifica los conteos exactos)
  - un workspace vacío
  - la intención inactiva de la base de datos (`ventas`) — no debe aparecer
  - un workspace inexistente — el comportamiento que tú decidiste y documentaste
  - que NO se instancian clientes nuevos (usa `clients._INSTANTIATIONS`)

Nombra cada test de forma que al leer el nombre se entienda qué protege.
"""

import pytest

from shared import clients
from tools.intent_report_tool import count_messages_by_intent


@pytest.mark.asyncio
async def test_globex_solo_tiene_mensajes_de_soporte():
    result = await count_messages_by_intent("globex")

    assert result["soporte_tecnico"] == 4
    assert result["facturacion"] == 0
    assert result["cuenta"] == 0
    assert result["desconocido"] == 0


@pytest.mark.asyncio
async def test_acme_cuenta_intenciones_y_mensajes_desconocidos():
    result = await count_messages_by_intent("acme")

    assert result == {
        "facturacion": 3,
        "soporte_tecnico": 1,
        "cuenta": 3,
        "desconocido": 3,
    }


@pytest.mark.asyncio
async def test_workspace_vacio_incluye_intenciones_activas_en_cero():
    result = await count_messages_by_intent("initech")

    assert result == {
        "facturacion": 0,
        "soporte_tecnico": 0,
        "cuenta": 0,
        "desconocido": 0,
    }


@pytest.mark.asyncio
async def test_reporte_omite_intenciones_inactivas():
    result = await count_messages_by_intent("acme")

    assert "ventas" not in result


@pytest.mark.asyncio
async def test_workspace_inexistente_propaga_keyerror():
    with pytest.raises(KeyError, match="workspace no encontrado"):
        await count_messages_by_intent("missing")


@pytest.mark.asyncio
async def test_reporte_reutiliza_clientes_singleton():
    await count_messages_by_intent("acme")
    await count_messages_by_intent("globex")

    assert clients._INSTANTIATIONS == {"db": 1, "storage": 1}
