"""Reliable sleep-prevention sessions, independent from the Tk interface."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import ctypes
import math
import sys
import threading
import time
from typing import Callable


ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002
MOUSEEVENTF_MOVE = 0x0001


@dataclass(frozen=True)
class StartResult:
    started: bool
    error: str | None = None


class SleepPreventerEngine:
    """Manage one cancellation-safe power session at a time.

    A session owns its own stop event and generation identifier.  That keeps a
    stopped worker from re-asserting power state after the user quickly starts a
    new session. The thread that starts a session is the sole owner of its
    ``SetThreadExecutionState`` request. The optional worker is only for the
    compatibility mouse heartbeat: it never applies or resets Windows power
    state because that API is thread-scoped.
    """

    def __init__(
        self,
        clock: Callable[[], float] = time.monotonic,
        state_applier: Callable[[int], bool] | None = None,
        mouse_heartbeat: Callable[[], None] | None = None,
        start_worker: bool = True,
    ):
        self._clock = clock
        self._state_applier = state_applier or self._set_execution_state
        self._mouse_heartbeat = mouse_heartbeat or self._send_mouse_heartbeat
        self._start_worker = start_worker
        self._lock = threading.RLock()

        self.is_active = False
        self.keep_display = True
        self.keep_system = True
        self.virtual_heartbeat = False
        self.start_monotonic = 0.0
        self.stop_monotonic = 0.0
        self.deadline_monotonic: float | None = None
        self.end_time: datetime | None = None
        self.last_error: str | None = None
        self.last_stop_reason: str | None = None
        self.session_id = 0
        self._stop_event: threading.Event | None = None
        self._worker: threading.Thread | None = None
        self._power_owner_thread_id: int | None = None
        self._restore_pending = False

    def _compute_flags(self) -> int:
        flags = ES_CONTINUOUS
        if self.keep_system:
            flags |= ES_SYSTEM_REQUIRED
        if self.keep_display:
            flags |= ES_DISPLAY_REQUIRED
        return flags

    @staticmethod
    def _set_execution_state(flags: int) -> bool:
        """Use the native API when available; allow a harmless non-Windows demo."""
        if sys.platform != "win32":
            return True
        try:
            result = ctypes.windll.kernel32.SetThreadExecutionState(flags)
            return bool(result)
        except Exception:
            return False

    @staticmethod
    def _send_mouse_heartbeat() -> None:
        if sys.platform != "win32":
            return
        try:
            ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVE, 0, 0, 0, 0)
        except Exception:
            pass

    def _apply_state(self, flags: int) -> bool:
        """Apply a power request without leaking adapter exceptions."""
        try:
            return bool(self._state_applier(flags))
        except Exception:
            return False

    def _restore_pending_state(self) -> bool:
        """Retry a failed reset from the thread that owns the request."""
        if not self._restore_pending:
            return True
        if self._power_owner_thread_id != threading.get_ident():
            self.last_error = "Windows power state can only be restored by the session owner."
            return False
        if self._apply_state(ES_CONTINUOUS):
            self._restore_pending = False
            self._power_owner_thread_id = None
            self.last_error = None
            return True
        self.last_error = "Windows could not restore normal power behavior."
        return False

    def start(
        self,
        keep_display: bool,
        keep_system: bool,
        virtual_heartbeat: bool = False,
        duration_seconds: int | None = None,
    ) -> StartResult:
        """Start a new protection session after validating power state."""
        if not keep_display and not keep_system:
            self.last_error = "Choose display protection, sleep protection, or both."
            return StartResult(False, self.last_error)
        if duration_seconds is not None and (
            not isinstance(duration_seconds, int)
            or isinstance(duration_seconds, bool)
            or duration_seconds <= 0
        ):
            self.last_error = "Session duration must be a positive number of seconds."
            return StartResult(False, self.last_error)

        with self._lock:
            if self.is_active:
                return StartResult(True)
            if not self._restore_pending_state():
                return StartResult(False, self.last_error)

            self.keep_display = keep_display
            self.keep_system = keep_system
            self.virtual_heartbeat = virtual_heartbeat
            self.last_error = None
            self.last_stop_reason = None

            if not self._apply_state(self._compute_flags()):
                self.last_error = "Windows could not apply the requested power protection."
                return StartResult(False, self.last_error)

            now = self._clock()
            self.start_monotonic = now
            self.stop_monotonic = 0.0
            self.deadline_monotonic = now + duration_seconds if duration_seconds else None
            self.end_time = datetime.now() + timedelta(seconds=duration_seconds) if duration_seconds else None
            self.is_active = True
            self._power_owner_thread_id = threading.get_ident()
            self.session_id += 1
            session_id = self.session_id
            stop_event = threading.Event()
            self._stop_event = stop_event

            if self._start_worker and self.virtual_heartbeat:
                self._worker = threading.Thread(
                    target=self._run_session,
                    args=(session_id, stop_event),
                    name="StayAwakeSession",
                    daemon=True,
                )
                self._worker.start()
            return StartResult(True)

    def _run_session(self, session_id: int, stop_event: threading.Event) -> None:
        last_mouse = self._clock()
        while not stop_event.wait(1.0):
            if not self._is_current_session(session_id):
                return
            now = self._clock()
            if self.virtual_heartbeat and now - last_mouse >= 45.0:
                self._mouse_heartbeat()
                last_mouse = now

    def _is_current_session(self, session_id: int) -> bool:
        with self._lock:
            return self.is_active and self.session_id == session_id

    def _is_expired(self, now: float | None = None) -> bool:
        return self.deadline_monotonic is not None and (now or self._clock()) >= self.deadline_monotonic

    def check_expiry(self) -> bool:
        """Stop an elapsed session. Returns True only on this transition."""
        with self._lock:
            session_id = self.session_id
            expired = self.is_active and self._is_expired()
        if expired:
            return self.stop(reason="completed", expected_session_id=session_id)
        return False

    def stop(self, reason: str = "manual", expected_session_id: int | None = None) -> bool:
        """Stop once, cancel this session's worker, and restore normal power mode."""
        with self._lock:
            if not self.is_active:
                # A later Stop click, new start, or window close can retry a
                # failed reset instead of falsely declaring success.
                return self._restore_pending and self._restore_pending_state()
            if expected_session_id is not None and expected_session_id != self.session_id:
                return False
            if self._power_owner_thread_id != threading.get_ident():
                self.last_error = "Windows power state can only be restored by the session owner."
                return False
            self.is_active = False
            self.last_stop_reason = reason
            self.stop_monotonic = self._clock()
            stop_event = self._stop_event
            worker = self._worker
            self._stop_event = None
            self._worker = None

        if stop_event:
            stop_event.set()
        if self._apply_state(ES_CONTINUOUS):
            self._power_owner_thread_id = None
            self._restore_pending = False
            self.last_error = None
        else:
            self._restore_pending = True
            self.last_error = "Windows could not restore normal power behavior."
        if worker and worker is not threading.current_thread():
            worker.join(timeout=1.5)
        return True

    def reset_timer(self) -> None:
        if not self.is_active:
            self.start_monotonic = 0.0
            self.stop_monotonic = 0.0

    def elapsed_seconds(self) -> int:
        if not self.start_monotonic:
            return 0
        end = self._clock() if self.is_active else self.stop_monotonic
        return max(0, int(end - self.start_monotonic))

    def remaining_seconds(self) -> int | None:
        if not self.is_active or self.deadline_monotonic is None:
            return None
        return max(0, math.ceil(self.deadline_monotonic - self._clock()))

    @property
    def needs_restore(self) -> bool:
        """Whether a failed reset must be retried by the owner thread."""
        return self._restore_pending

    def scope_summary(self) -> str:
        if self.keep_system and self.keep_display:
            return "system and display"
        if self.keep_system:
            return "system sleep"
        if self.keep_display:
            return "display timeout"
        return "no protection"
