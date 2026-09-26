# Casos del verificador

Estos resultados aplican `verificador_v2.md` a `fixtures/db.json`.

| Caso | Veredicto esperado | Razón | Trampa identificada |
|---|---|---|---|
| **a-1** | `APROBADO` | La cita es literal, cubre los 15 días, `src-1` y `chunk=3` son trazables y `0.91 >= 0.80`. | Ninguna; es el caso válido. |
| **a-2** | `SIN_EVIDENCIA` | La cita es una paráfrasis genérica, no aparece literalmente en la fuente, y `0.34 < 0.55`. | Cita vacía disfrazada de evidencia y baja similitud. |
| **a-3** | `SIN_EVIDENCIA` | La cita literal solo respalda la ruta de invitación, pero la respuesta también afirma que caduca en 7 días. | La respuesta contiene una afirmación que su propia cita no cubre. |
| **a-4** | `DUDOSO` | La cita es literal y suficiente, pero `source_id=src-99-inexistente` no permite trazabilidad; se necesita revisión. | Cita real con identificador de fuente inexistente. |
| **a-5** | `DUDOSO` | La cita es literal, pero `chunk=null` deja incompleta la trazabilidad aunque `src-1` exista y `0.86` supere el umbral. | Falta el índice del fragmento. |

El caso más fácil de aprobar por error es **a-4**: el texto de la cita parece
correcto, pero no se puede auditar desde el identificador entregado. Por eso no
es `APROBADO`; tampoco se descarta una cita que sí puede verificarse como
literal: queda `DUDOSO`.
