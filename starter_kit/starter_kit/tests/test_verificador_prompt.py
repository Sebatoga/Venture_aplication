from pathlib import Path


PROMPT = Path(__file__).resolve().parents[1] / "prompts" / "verificador_v2.md"


def test_prompt_v2_exige_contrato_de_verificacion_y_salida_estable():
    content = PROMPT.read_text(encoding="utf-8").lower()

    for requirement in (
        "texto literal",
        "subcadena exacta",
        "dudoso",
        "0.80",
        "no inventes",
        "reescribas",
        "additionalproperties",
        "salida esperada",
    ):
        assert requirement in content

    assert '"veredicto"' in content
    assert '"razon"' in content
    assert '"aprobado"' in content
    assert '"sin_evidencia"' in content
