from pathlib import Path


PROMPT = Path(__file__).resolve().parents[1] / "prompts" / "verificador_v1.md"


def test_prompt_exige_contrato_de_verificacion_y_salida_estable():
    content = PROMPT.read_text(encoding="utf-8").lower()

    for requirement in (
        "evidencia",
        "identificador de fuente",
        "no contradiga",
        "solo las respuestas aprobadas",
        "lista",
        "orden de entrada",
    ):
        assert requirement in content
