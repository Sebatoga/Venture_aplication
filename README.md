# Venture Application

Asistente de consultas basado en evidencia, desarrollado como una prueba
técnica de IA. El proyecto clasifica intenciones, busca fragmentos relevantes y
devuelve respuestas con un veredicto explícito.

## Requisitos

- Python 3.10 o superior
- `pip`

## Instalación

```bash
cd starter_kit/starter_kit
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Verificación

```bash
python -m pytest
python -m compileall -q .
```

Resultado esperado: **38 tests pasan**.

## Ejecución

```bash
python app.py
```

La consola HTTP queda disponible en `http://localhost:8000`.

## Estructura principal

- `starter_kit/starter_kit/app.py` — pipeline de consulta y consola HTTP.
- `starter_kit/starter_kit/config/intents.py` — clasificación de intenciones.
- `starter_kit/starter_kit/tools/` — reporte, respuestas heredadas y protección
  contra loops.
- `starter_kit/starter_kit/shared/` — clientes y retriever protegidos.
- `starter_kit/starter_kit/tests/` — pruebas automatizadas.
- `starter_kit/starter_kit/NOTAS.md` — decisiones y verificación detallada.

## Veredictos

- `APROBADO` — existe evidencia suficiente.
- `DUDOSO` — la evidencia es parcial.
- `SIN_EVIDENCIA` — no existe evidencia utilizable.

Las respuestas aprobadas y dudosas usan literalmente el mejor fragmento
recuperado; el sistema no inventa contenido.
