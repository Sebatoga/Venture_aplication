# Arreglar entorno y desbloquear revisión

## Objetivo

Preparar el workspace para ejecutar las pruebas de `starter_kit` y permitir que
la revisión nativa trabaje sobre un repositorio con higiene y una base Git real.

## Alcance autorizado

- Crear un entorno virtual dentro de `starter_kit/starter_kit`.
- Instalar únicamente las dependencias declaradas en `requirements.txt`.
- Ejecutar el baseline de pruebas y una comprobación de arranque segura.
- Añadir reglas de higiene del repositorio sin modificar el starter kit protegido.
- Crear commits de trabajo en la rama actual; no hacer push, PR ni merge.

## Restricciones

- No modificar `shared/clients.py`, `shared/retriever.py`, `fixtures/`, `pytest.ini`
  ni `tests/test_classify_intent.py`.
- No agregar dependencias a `requirements.txt`.
- No incluir credenciales, artefactos de `__MACOSX`, `.DS_Store`, archivos PDF o
  ZIP de entrada en los commits.

## Tareas

- [x] `ENV-001` Crear venv e instalar las dependencias declaradas.
- [x] `ENV-002` Ejecutar baseline de pytest y smoke test, registrando resultados.
- [x] `ENV-003` Añadir `.gitignore` y excluir residuos/artefactos generados.
- [x] `ENV-004` Crear commit base y comprobar la selección de archivos no versionados.
- [x] `ENV-005` Ejecutar la evaluación del preflight/revisión nuevamente y
  registrar el resultado.
- [ ] `APP-001` Completar clasificación y enrutamiento de intenciones.
- [ ] `APP-002` Completar reporte de cobertura por intención.
- [ ] `APP-003` Corregir la herramienta heredada de respuestas.
- [ ] `APP-004` Mejorar el prompt verificable y sus artefactos.
- [ ] `APP-005` Implementar la guardia anti-loop y la consola HTTP.

## Checks aplicables

- `python -m pytest`
- `python -m compileall -q .`
- `gentle-ai doctor`
- `gentle-ai review status --cwd /home/sebato/Escritorio/ventus --contract gentle-ai.review-integration/v2 --agent opencode --next-transition`

## Estado

- Ruta: delegated direct para preparación y verificación; la exploración previa
  confirmó que el bloqueo actual es la selección de archivos no versionados.
- TDD: no está activo; se ejecutan checks funcionales ordinarios.
- Progreso: `ENV-001`–`ENV-004` completadas. El baseline compila y la importación
  de la aplicación funciona; pytest reporta 21 fallos esperados por ejercicios
  aún no implementados. Commit base: `8c98f9f`. La evaluación del commit de
  seguimiento (`ddb817d`) resultó `passive`, sin revisión adicional requerida.
- Siguiente: mapear los 21 fallos y repartirlos por unidad funcional antes de
  implementar.
