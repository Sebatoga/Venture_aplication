import pytest

from shared import clients
from tools.legacy_answers_tool import get_workspace_answers


@pytest.mark.asyncio
async def test_answers_filtra_antes_de_buscar_fuente_y_tolera_fuente_inexistente():
    result = await get_workspace_answers("acme", min_similitud=0.5)

    assert [answer["source_id"] for answer in result] == ["src-1", "src-99-inexistente"]
    assert result[0]["fuente_titulo"] == "Guía de planes y garantías"
    assert result[0]["confianza"] == "alta"
    assert result[1]["fuente_titulo"] is None
    assert result[1]["confianza"] == "baja"
    assert clients._INSTANTIATIONS == {"db": 1, "storage": 0}


@pytest.mark.asyncio
async def test_cache_separa_umbral_y_protege_sus_resultados_de_mutaciones():
    cache = {}

    high = await get_workspace_answers("acme", cache=cache, min_similitud=0.8)
    high[0]["pregunta"] = "mutada"
    low = await get_workspace_answers("acme", cache=cache, min_similitud=0.3)
    high_again = await get_workspace_answers("acme", cache=cache, min_similitud=0.8)

    assert len(high_again) == 1
    assert high_again[0]["pregunta"] != "mutada"
    assert len(low) == 3
    assert set(cache) == {("acme", 0.8), ("acme", 0.3)}
    assert clients._INSTANTIATIONS == {"db": 1, "storage": 0}
