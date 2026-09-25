# Notas de implementación

La solución completa los seis ejercicios del starter kit sin modificar los
clientes, el retriever, los fixtures ni la configuración protegida de pytest.

## Qué se implementó

- Clasificación robusta de intenciones: normalización, acentos, líneas citadas,
  mensajes cortos y selección del patrón más específico.
- Reporte de cobertura con clientes singleton, intenciones activas y categoría
  `desconocido`.
- Reparación de respuestas heredadas: caché segura por umbral, filtrado,
  enriquecimiento de fuentes y manejo de fuentes ausentes.
- Prompt de verificación con requisitos explícitos de evidencia, fuente,
  contradicciones y salida aprobada.
- `LoopGuard` con aislamiento por sesión/agente, límite configurable, snapshots
  y protección mediante lock.
- Pipeline asíncrono y consola HTTP estándar con veredictos
  `SIN_EVIDENCIA`, `DUDOSO` y `APROBADO`.

## Decisiones y límites

- Se conserva la forma pública de las respuestas y no se agregan dependencias.
- La consola exige `q` no vacío y usa `acme` como workspace predeterminado si
  no se informa `ws`.
- Las respuestas aprobadas y dudosas usan literalmente el mejor fragmento
  recuperado; no se inventa contenido.
- Se conserva la escritura histórica de `/tmp/last_answers.json`, ahora con
  codificación UTF-8 explícita.

## Verificación reproducible

Desde `starter_kit/starter_kit`:

```bash
.venv/bin/python -m pytest
.venv/bin/python -m compileall -q .
python app.py
```

Resultado observado: **38 tests pasan**, la compilación pasa y la aplicación
puede iniciar la consola HTTP en `http://localhost:8000`.

## Archivos protegidos

No se modificaron `shared/clients.py`, `shared/retriever.py`, `fixtures/`,
`pytest.ini`, `requirements.txt` ni `tests/test_classify_intent.py`.

## Declaración de asistencia

Se utilizó asistencia de IA para explorar el código, proponer la estructura y
verificar los cambios. Las decisiones y el resultado deben revisarse contra el
enunciado de la prueba técnica.
