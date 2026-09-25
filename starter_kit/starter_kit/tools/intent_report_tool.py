"""
Herramienta del paso Clasificador: reporte de cobertura por intención.

EJERCICIO 2.

Contexto de producto: antes de activar el asistente en un workspace, el equipo
quiere ver "de tus 200 preguntas, 80 son de facturación, 40 de soporte y 60 no
supe de qué son". Ese último número es el que decide si el asistente está listo
o si al cliente le falta subir contenido.
"""

from __future__ import annotations

import logging

from config.intents import UNKNOWN, classify_intent
from shared import clients

logger = logging.getLogger(__name__)


async def count_messages_by_intent(workspace_id: str) -> dict[str, int]:
    """Cuenta los mensajes de un workspace agrupados por intención.

    Comportamiento esperado:

    1. Lee las intenciones válidas de la tabla `intents` de la base de datos.
       Solo cuentan las que tienen `active: true`.
    2. Lista los mensajes del workspace con el cliente de almacenamiento.
    3. Clasifica cada mensaje con `config.intents.classify_intent`.
    4. Devuelve `{intencion: conteo}` incluyendo:
       - todas las intenciones activas, **aunque su conteo sea 0**;
       - la intención `desconocido`, siempre presente.
       Las intenciones inactivas no aparecen en el resultado.

    Restricciones (se evalúan):
    - Reutiliza los singletons de `shared.clients`. No construyas clientes
      nuevos dentro de esta función.
    - Es `async`: usa `await` sobre las llamadas de los clientes.
    - Si el workspace no existe, el cliente levanta `KeyError`. Decide qué hace
      la herramienta en ese caso y **documenta tu decisión en un comentario**:
      propagar, devolver dict vacío o devolver ceros no son equivalentes para
      el agente que la llama.
    - Deja al menos un log útil, siguiendo el patrón del módulo.

    Args:
        workspace_id: por ejemplo `acme`.

    Returns:
        Diccionario `{intencion: conteo}`.
    """
    db = clients.get_db_client()
    storage = clients.get_storage_client()

    active_intents = {
        record.id
        for record in await db.table("intents").get()
        if record.to_dict().get("active") is True
    }
    counts = {intent: 0 for intent in active_intents}
    counts[UNKNOWN] = 0

    # Preserve the storage client's KeyError: an unknown workspace is an
    # input error for the caller, not an empty coverage report.
    messages = await storage.list_messages(workspace_id)
    for message in messages:
        intent = classify_intent(message)
        if intent in counts:
            counts[intent] += 1
        else:
            counts[UNKNOWN] += 1

    logger.info("Intent coverage for workspace %s: %s", workspace_id, counts)
    return counts
