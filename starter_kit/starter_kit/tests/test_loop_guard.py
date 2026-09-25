"""
Tests del EJERCICIO 5.

Aquí no te damos nada hecho a propósito: queremos ver qué casos se te ocurren.
Escribe la suite completa. Como mínimo debe cubrir:

  - se permiten hasta MAX_CALLS llamadas
  - la siguiente levanta ToolLoopError
  - el mensaje de error contiene agente, sesión y conteo
  - los conteos no se cruzan entre agentes
  - los conteos no se cruzan entre sesiones
  - reset() limpia una sesión y no afecta a las demás
  - snapshot() refleja los conteos actuales
"""

import threading

import pytest

from tools.loop_guard import LoopGuard, ToolLoopError


def test_allows_max_calls_then_reports_detailed_error():
    guard = LoopGuard(max_calls=2)

    assert guard.record("session-a", "classifier") == 1
    assert guard.record("session-a", "classifier") == 2
    with pytest.raises(ToolLoopError, match=r"classifier.*session-a.*count=3"):
        guard.record("session-a", "classifier")


def test_counts_are_independent_by_agent_and_session():
    guard = LoopGuard(max_calls=2)

    guard.record("session-a", "classifier")
    guard.record("session-a", "classifier")
    assert guard.record("session-a", "verifier") == 1
    assert guard.record("session-b", "classifier") == 1


def test_reset_clears_only_requested_session_and_snapshot_is_a_copy():
    guard = LoopGuard()
    guard.record("session-a", "classifier")
    guard.record("session-b", "verifier")

    snapshot = guard.snapshot("session-a")
    snapshot["classifier"] = 99
    assert guard.snapshot("session-a") == {"classifier": 1}

    guard.reset("session-a")
    assert guard.snapshot("session-a") == {}
    assert guard.snapshot("session-b") == {"verifier": 1}


def test_max_calls_must_be_positive_integer():
    with pytest.raises(ValueError):
        LoopGuard(0)
    with pytest.raises(ValueError):
        LoopGuard(True)


def test_concurrent_records_do_not_lose_increments():
    guard = LoopGuard(max_calls=100)
    threads = [
        threading.Thread(target=guard.record, args=("session-a", "classifier"))
        for _ in range(20)
    ]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert guard.snapshot("session-a") == {"classifier": 20}
