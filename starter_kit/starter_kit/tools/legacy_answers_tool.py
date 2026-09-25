"""
EJERCICIO 3 — Código heredado con defectos.

Esta herramienta la escribió alguien con prisa y pasó a producción. Funciona
"en la mayoría de los casos", que es exactamente el problema.

Tu trabajo: encontrar los defectos, corregirlos y explicar cada uno.
NO reescribas la herramienta cambiando su propósito: debe seguir devolviendo
las respuestas de un workspace enriquecidas con el texto de su fuente.
"""

import json
from copy import deepcopy
from pathlib import Path

from shared.clients import get_db_client


async def get_workspace_answers(workspace_id, cache=None, min_similitud=0.0):
    """Return workspace answers enriched with their source title.

    ``cache`` remains an optional caller-owned mapping for compatibility, but
    it is never shared between calls implicitly and its values are copied at
    both boundaries.
    """
    if cache is None:
        cache = {}

    cache_key = (workspace_id, min_similitud)
    if cache_key in cache:
        return deepcopy(cache[cache_key])

    db = get_db_client()

    answers = await db.table("answers").where("workspace_id", workspace_id).get()

    result = []
    for a in answers:
        data = a.to_dict()
        if data["similitud"] < min_similitud:
            continue

        source = await db.table("sources").item(data["source_id"]).get()
        data["fuente_titulo"] = source.to_dict().get("titulo") if source.exists else None
        data["confianza"] = {True: "alta", False: "baja"}[data["similitud"] > 0.8]
        result.append(data)

    Path("/tmp/last_answers.json").write_text(
        json.dumps(result, ensure_ascii=False), encoding="utf-8"
    )

    cache[cache_key] = deepcopy(result)
    return deepcopy(result)
