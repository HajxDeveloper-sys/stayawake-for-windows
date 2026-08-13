import threading

from session_engine import (
    ES_CONTINUOUS,
    ES_DISPLAY_REQUIRED,
    ES_SYSTEM_REQUIRED,
    SleepPreventerEngine,
)


class FakeClock:
    def __init__(self, value=100.0):
        self.value = value

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


def test_timed_session_expires_once_and_restores_default_state():
    clock = FakeClock()
    calls = []
    engine = SleepPreventerEngine(
        clock=clock, state_applier=lambda flags: calls.append(flags) or True, start_worker=False
    )

    result = engine.start(True, True, duration_seconds=30)

    assert result.started is True
    assert engine.is_active is True
    assert calls == [ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED]
    assert engine.remaining_seconds() == 30

    clock.advance(29.1)
    assert engine.remaining_seconds() == 1
    assert engine.check_expiry() is False

    clock.advance(0.9)
    assert engine.check_expiry() is True
    assert engine.is_active is False
    assert engine.last_stop_reason == "completed"
    assert engine.elapsed_seconds() == 30
    assert calls[-1] == ES_CONTINUOUS
    assert engine.check_expiry() is False


def test_failed_power_application_never_marks_session_active():
    engine = SleepPreventerEngine(state_applier=lambda _flags: False, start_worker=False)

    result = engine.start(True, False)

    assert result.started is False
    assert engine.is_active is False
    assert engine.last_error


def test_start_rejects_empty_scope_and_invalid_duration_before_api_call():
    calls = []
    engine = SleepPreventerEngine(
        state_applier=lambda flags: calls.append(flags) or True, start_worker=False
    )

    assert engine.start(False, False).started is False
    assert engine.start(True, False, duration_seconds=0).started is False
    assert engine.start(True, False, duration_seconds=True).started is False
    assert calls == []


def test_manual_stop_freezes_elapsed_time():
    clock = FakeClock()
    engine = SleepPreventerEngine(clock=clock, state_applier=lambda _flags: True, start_worker=False)

    assert engine.start(False, True).started
    clock.advance(12)
    assert engine.stop()
    assert engine.elapsed_seconds() == 12
    clock.advance(100)
    assert engine.elapsed_seconds() == 12


def test_worker_never_applies_or_resets_the_ui_threads_power_state():
    calls = []
    owner_thread = threading.get_ident()
    engine = SleepPreventerEngine(
        state_applier=lambda flags: calls.append((threading.get_ident(), flags)) or True,
        start_worker=False,
    )

    assert engine.start(True, True, virtual_heartbeat=True).started
    stop_event = threading.Event()
    stop_event.set()
    worker = threading.Thread(target=engine._run_session, args=(engine.session_id, stop_event))
    worker.start()
    worker.join(timeout=1)

    # The heartbeat worker has no SetThreadExecutionState responsibility.
    assert calls == [(owner_thread, ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)]
    assert engine.stop()
    assert calls[-1] == (owner_thread, ES_CONTINUOUS)


def test_failed_reset_is_reported_and_can_be_retried_by_the_owner_thread():
    results = iter([True, False, True])
    calls = []
    engine = SleepPreventerEngine(
        state_applier=lambda flags: calls.append(flags) or next(results), start_worker=False
    )

    assert engine.start(True, False).started
    assert engine.stop()
    assert engine.is_active is False
    assert engine.last_error == "Windows could not restore normal power behavior."
    assert engine.stop()  # retries the pending reset rather than reporting success prematurely
    assert engine.last_error is None
    assert calls == [ES_CONTINUOUS | ES_DISPLAY_REQUIRED, ES_CONTINUOUS, ES_CONTINUOUS]
