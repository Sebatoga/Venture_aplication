# Venture Application

Asistente local de consultas basado en evidencia. El proyecto recibe una
pregunta, detecta su intención, recupera fragmentos del contenido del cliente y
devuelve un resultado explicable: qué intención detectó, qué evidencia encontró,
qué puntaje obtuvo y si corresponde responder o abstenerse.

Este repositorio implementa la prueba técnica de IA incluida en
`02_Prueba_Practica.pdf`. La solución no utiliza proveedores externos, claves de
API ni frameworks web: todo corre localmente con Python, la librería estándar y
pytest.

## Índice

1. [Qué problema resuelve](#qué-problema-resuelve)
2. [Flujo de una consulta](#flujo-de-una-consulta)
3. [Organización del repositorio](#organización-del-repositorio)
4. [Requisitos e instalación](#requisitos-e-instalación)
5. [Ejecución de la consola](#ejecución-de-la-consola)
6. [Comportamiento y veredictos](#comportamiento-y-veredictos)
7. [Ejercicios implementados](#ejercicios-implementados)
8. [Verificación](#verificación)
9. [Restricciones y decisiones](#restricciones-y-decisiones)
10. [Trazabilidad de la entrega](#trazabilidad-de-la-entrega)

## Qué problema resuelve

El sistema simula un asistente para una plataforma SaaS donde cada workspace
tiene documentación propia. Ante una pregunta del usuario, el asistente debe:

- clasificar el tema de la consulta;
- encontrar evidencia relevante en el corpus local;
- evitar respuestas inventadas cuando la evidencia es insuficiente;
- mostrar el razonamiento operativo de forma visible;
- controlar errores transversales como cachés contaminadas y loops de agentes.

La aplicación **no genera texto con un LLM**. La respuesta final es el texto
literal del mejor fragmento recuperado. Esta decisión hace que el resultado sea
determinista y permite comprobar que la consola nunca presenta como hecho algo
que no aparece en la documentación.

## Flujo de una consulta

```text
Pregunta del usuario
        │
        ▼
classify_intent()
        │  normaliza y selecciona el patrón más específico
        ▼
retriever.search()
        │  devuelve fragmentos con similitud y metadatos
        ▼
consultar()
        │  compara el mejor puntaje con los umbrales
        ├── SIN_EVIDENCIA ──► respuesta = None
        ├── DUDOSO         ──► fragmento literal + revisión humana
        └── APROBADO       ──► fragmento literal respaldado
        │
        ▼
Consola HTTP explicable
```

La función `consultar(pregunta, workspace_id)` está separada del servidor para
poder probar el pipeline directamente sin levantar HTTP. El `Handler` solo
parsea parámetros, invoca el pipeline, serializa JSON y traduce errores a
respuestas HTTP seguras.

## Organización del repositorio

```text
.
├── README.md                         # Esta guía
├── 02_Prueba_Practica.pdf            # Enunciado original
├── openspec/config.yaml              # Artifact store del entorno SDD
├── odd/tasks/arreglar-entorno.md     # Plan y evidencia de trabajo
├── starter_kit/
│   └── starter_kit/
│       ├── app.py                    # Pipeline async y consola HTTP
│       ├── config/
│       │   └── intents.py             # Catálogo y clasificación
│       ├── fixtures/                 # Datos locales de prueba
│       │   ├── db.json
│       │   └── storage.json
│       ├── prompts/
│       │   ├── verificador_v1.md      # Prompt original preservado
│       │   ├── verificador_v2.md      # Prompt corregido
│       │   └── casos_verificador.md   # Casos a-1..a-5
│       ├── shared/
│       │   ├── clients.py             # Clientes singleton entregados
│       │   └── retriever.py            # Recuperador léxico entregado
│       ├── tools/
│       │   ├── intent_report_tool.py  # Cobertura por intención
│       │   ├── legacy_answers_tool.py # Respuestas heredadas corregidas
│       │   └── loop_guard.py          # Protección contra loops
│       ├── tests/                    # Suite de 38 pruebas
│       ├── evidence/                 # Evidencia visual de la consola
│       ├── NOTAS.md                  # Entrega, decisiones y verificación
│       ├── pytest.ini                # Configuración de pytest
│       └── requirements.txt          # Dependencias permitidas
└── .gitignore
```

El directorio `.venv/` se crea dentro del starter kit, pero está excluido del
repositorio porque es un artefacto local reproducible.

## Requisitos e instalación

### Requisitos

- Python 3.10 o superior.
- `pip`.
- No se requieren credenciales, servicios externos ni conexión a una API.

### Instalación reproducible

Desde la raíz del repositorio:

```bash
cd starter_kit/starter_kit
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
.venv/bin/python -m pip install -r requirements.txt
```

Las únicas dependencias declaradas son `pytest` y `pytest-asyncio`. No se
agregaron Flask, FastAPI, React, Tailwind ni clientes de nube.

## Ejecución de la consola

Con el entorno virtual activo:

```bash
cd starter_kit/starter_kit
.venv/bin/python app.py
```

Abrí `http://localhost:8000` en el navegador. La página permite elegir el
workspace y enviar una pregunta. Para probar la API directamente:

```bash
curl 'http://localhost:8000/api/consulta?q=%C2%BFCu%C3%A1ntos%20d%C3%ADas%20de%20garant%C3%ADa%20tiene%20el%20plan%20Pro%3F&ws=acme'
```

La respuesta JSON contiene exactamente:

```json
{
  "pregunta": "...",
  "workspace": "acme",
  "intencion": "facturacion",
  "especialista": "billing_agent",
  "fragmentos": [],
  "veredicto": "APROBADO",
  "motivo": "Similitud 0.910, igual o por encima del umbral alto de 0.75",
  "respuesta": "..."
}
```

### Si no aparecen resultados

El servidor debe permanecer ejecutándose en una terminal y las consultas deben
hacerse desde otra. Si aparece `Address already in use`, ya existe otro
`app.py` ocupando el puerto 8000. Volvé a la terminal anterior y detenelo con
`Ctrl+C`; después iniciá una sola instancia:

```bash
cd starter_kit/starter_kit
.venv/bin/python app.py
```

En una segunda terminal comprobá que responde:

```bash
curl -i --max-time 10 http://127.0.0.1:8000/
```

Debe devolver `HTTP/1.0 200 OK`. Si la conexión se establece pero no responde,
detené la instancia anterior, esperá un segundo y reiniciá el servidor. No
abras varias instancias en el mismo puerto.

## Comportamiento y veredictos

La decisión usa el mejor puntaje de similitud recuperado:

| Veredicto | Condición | Respuesta |
|---|---|---|
| `SIN_EVIDENCIA` | No hay fragmentos o el mejor puntaje es menor que `0.55`. | `respuesta: null`; el sistema se abstiene. |
| `DUDOSO` | Puntaje entre `0.55` y menor que `0.75`. | Se muestra el fragmento literal, marcado para revisión. |
| `APROBADO` | Puntaje mayor o igual que `0.75`. | Se muestra el fragmento literal respaldado. |

Los umbrales están definidos en `app.py` como `UMBRAL_MINIMO` y
`UMBRAL_ALTO`. El motivo siempre incluye el puntaje y el umbral relevante para
que el resultado sea accionable y no un mensaje genérico.

### Casos recomendados por la guía

| Pregunta | Resultado esperado | Motivo |
|---|---|---|
| ¿Cuántos días de garantía tiene el plan Pro? | `APROBADO` | El corpus contiene la garantía de devolución del plan Pro. |
| olvidé mi contraseña, ¿cómo la restablezco? | `DUDOSO` | Hay evidencia parcial según el recuperador léxico. |
| ¿cuánto dura la garantía del plan Enterprise? | `SIN_EVIDENCIA` | Hay coincidencias sobre planes, pero no evidencia del plan Enterprise. |

La captura del tercer caso está en
`starter_kit/starter_kit/evidence/console-enterprise.png`.

## Ejercicios implementados

### Ejercicio 1 — Clasificador de intención

`config/intents.py` implementa una clasificación basada en reglas:

- normaliza mayúsculas, acentos, signos, separadores y espacios;
- ignora líneas citadas que empiezan con `>`;
- devuelve `desconocido` para `None`, entradas vacías o mensajes demasiado cortos;
- selecciona el patrón más largo cuando coinciden varias intenciones;
- conserva el catálogo configurable de `INTENTS` sin casos hardcodeados.

### Ejercicio 2 — Reporte de cobertura

`tools/intent_report_tool.py` usa `get_db_client()` y `get_storage_client()`.
Lee las intenciones activas, incluye categorías con conteo cero, agrega siempre
`desconocido`, clasifica todos los mensajes y propaga `KeyError` si el workspace
no existe. Esta última decisión evita confundir un identificador inválido con un
workspace vacío.

### Ejercicio 3 — Revisión de código heredado

`tools/legacy_answers_tool.py` conserva el contrato de lista de respuestas, pero
corrige:

- caché mutable compartida entre llamadas;
- claves de caché que ignoraban `min_similitud`;
- creación repetida de clientes;
- búsqueda de fuentes antes del filtrado;
- fuentes inexistentes que provocaban excepciones;
- escritura dependiente de la codificación del sistema;
- exposición de listas mutables almacenadas en caché.

La tabla de síntomas y severidades está en `NOTAS.md`, junto con las pruebas de
regresión correspondientes.

### Ejercicio 4 — Verificador

`prompts/verificador_v1.md` conserva el prompt original para comparación.
`prompts/verificador_v2.md` exige citas literales, trazabilidad, similitud,
salida JSON estricta y prohíbe reescribir la respuesta. Incluye el veredicto
`DUDOSO` cuando la evidencia es real pero falta un metadato de trazabilidad.

Los cinco casos de `fixtures/db.json` están analizados en
`prompts/casos_verificador.md`, incluyendo las trampas de citas genéricas,
fuentes inexistentes y chunks ausentes.

### Ejercicio 5 — Guardia anti-loop

`tools/loop_guard.py` cuenta llamadas por `(session_id, agent_name)`.
`LoopGuard` permite hasta `max_calls`, lanza `ToolLoopError` en el siguiente
intento, informa agente/sesión/conteo, permite `reset()` y devuelve snapshots
defensivos. Un `threading.Lock` protege las operaciones compuestas para que las
llamadas concurrentes no pierdan incrementos.

### Ejercicio 6 — Consola del asistente

`app.py` conecta clasificación, recuperación y decisión de evidencia. La
interfaz muestra intención, especialista, fragmentos, puntajes, veredicto,
motivo y respuesta. Los tres veredictos tienen estilos visuales distintos y la
abstención se presenta explícitamente como falta de evidencia.

## Verificación

### Suite local

Desde `starter_kit/starter_kit`:

```bash
.venv/bin/python -m pytest
.venv/bin/python -m compileall -q .
```

Resultado observado: **38 tests pasan** y la compilación finaliza sin errores.

### Verificación en clon limpio

La entrega también fue comprobada en un clon independiente con Python 3.14.7:

```bash
git clone <repository-url> clean-checkout
cd clean-checkout/starter_kit/starter_kit
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest
.venv/bin/python -m compileall -q .
.venv/bin/python app.py
```

El clon obtuvo 38 tests exitosos, compiló correctamente y levantó la consola
respondiendo `HTTP 200`.

## Restricciones y decisiones

Se mantuvieron sin modificaciones:

- `shared/clients.py`;
- `shared/retriever.py`;
- `fixtures/`;
- `pytest.ini`;
- `requirements.txt`;
- `tests/test_classify_intent.py`.

No se agregaron dependencias nuevas. Las decisiones, defectos corregidos,
trade-offs, uso de IA y límites conocidos están documentados en
`starter_kit/starter_kit/NOTAS.md`.

## Trazabilidad de la entrega

El historial Git conserva commits pequeños por unidad de trabajo: entorno,
clasificación/reporte/guardia, respuestas heredadas, consola, documentación,
auditoría de la guía y README. La rama `main` del repositorio remoto contiene
la misma historia que el workspace local.
