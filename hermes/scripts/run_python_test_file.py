#!/usr/bin/env python3
"""Supervise one isolated unittest process and report through a private FD.

The process boundary prevents test output and ordinary early exits from forging a
successful CI result. It is not an OS sandbox for deliberately hostile Python
code running as the same user.
"""

from __future__ import annotations

import argparse
import ctypes
import importlib.util
import json
import multiprocessing
import os
from pathlib import Path
import signal
import sys
import time
import traceback
import unittest


RESULT_MARKER = "HERMES_TEST_RESULT="
CLEANUP_MARKER = "HERMES_TEST_CHILD="
PROTOCOL_VERSION = 1
MAX_DETAIL_CHARACTERS = 4096
CHILD_TERM_GRACE_SECONDS = 0.25
CHILD_KILL_GRACE_SECONDS = 1.0
MAX_DESCENDANT_PROCESSES = 4096
FORCE_KILL_SIGNAL = getattr(signal, "SIGKILL", signal.SIGTERM)
PR_SET_CHILD_SUBREAPER = 36
PR_SET_PDEATHSIG = 1
NORMAL_COMPLETION_EXIT_CODE = 86
OUTCOME_NOT_COMPLETED = 0
OUTCOME_SUCCESS = 1
OUTCOME_NO_TESTS = 2
OUTCOME_NO_EXECUTED_TESTS = 3
OUTCOME_TEST_FAILURE = 4
OUTCOME_LOAD_FAILURE = 5


class DarwinBsdInfo(ctypes.Structure):
    """Prefix-complete proc_bsdinfo layout through the process start time."""

    _fields_ = [
        ("pbi_flags", ctypes.c_uint32),
        ("pbi_status", ctypes.c_uint32),
        ("pbi_xstatus", ctypes.c_uint32),
        ("pbi_pid", ctypes.c_uint32),
        ("pbi_ppid", ctypes.c_uint32),
        ("pbi_uid", ctypes.c_uint32),
        ("pbi_gid", ctypes.c_uint32),
        ("pbi_ruid", ctypes.c_uint32),
        ("pbi_rgid", ctypes.c_uint32),
        ("pbi_svuid", ctypes.c_uint32),
        ("pbi_svgid", ctypes.c_uint32),
        ("rfu_1", ctypes.c_uint32),
        ("pbi_comm", ctypes.c_char * 16),
        ("pbi_name", ctypes.c_char * 32),
        ("pbi_nfiles", ctypes.c_uint32),
        ("pbi_pgid", ctypes.c_uint32),
        ("pbi_pjobc", ctypes.c_uint32),
        ("e_tdev", ctypes.c_uint32),
        ("e_tpgid", ctypes.c_uint32),
        ("pbi_nice", ctypes.c_int32),
        ("pbi_start_tvsec", ctypes.c_uint64),
        ("pbi_start_tvusec", ctypes.c_uint64),
    ]


def process_start_token(process_id: int) -> str:
    """Return a platform birth token, never a PID-only identity."""

    if process_id <= 1:
        raise RuntimeError("unsafe process ID for start-token lookup")
    if sys.platform.startswith("linux"):
        try:
            content = Path(f"/proc/{process_id}/stat").read_text(encoding="ascii")
        except FileNotFoundError as error:
            raise ProcessLookupError(process_id) from error
        closing_parenthesis = content.rfind(")")
        if closing_parenthesis < 0:
            raise RuntimeError("invalid Linux process stat record")
        fields_after_name = content[closing_parenthesis + 2 :].split()
        if len(fields_after_name) <= 19:
            raise RuntimeError("invalid Linux process stat record")
        start_ticks = fields_after_name[19]
        if not start_ticks.isascii() or not start_ticks.isdecimal():
            raise RuntimeError("invalid Linux process start time")
        return f"linux:{start_ticks}"
    if sys.platform == "darwin":
        info = DarwinBsdInfo()
        libproc = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
        proc_pidinfo = libproc.proc_pidinfo
        proc_pidinfo.argtypes = [
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_uint64,
            ctypes.c_void_p,
            ctypes.c_int,
        ]
        proc_pidinfo.restype = ctypes.c_int
        ctypes.set_errno(0)
        returned = proc_pidinfo(
            process_id,
            3,  # PROC_PIDTBSDINFO
            0,
            ctypes.byref(info),
            ctypes.sizeof(info),
        )
        if returned <= 0:
            error_number = ctypes.get_errno()
            if error_number in {0, 3}:
                raise ProcessLookupError(process_id)
            raise OSError(error_number, os.strerror(error_number))
        if returned < ctypes.sizeof(info):
            raise RuntimeError("incomplete Darwin process info")
        return f"darwin:{info.pbi_start_tvsec}:{info.pbi_start_tvusec}"
    raise RuntimeError("stable process identity is unavailable")


def failure(detail: str) -> dict[str, object]:
    return {
        "version": PROTOCOL_VERSION,
        "ok": False,
        "discovered": 0,
        "executed": 0,
        "skipped": 0,
        "detail": detail[:MAX_DETAIL_CHARACTERS],
    }


def enable_parent_death_signal(expected_parent_pid: int) -> None:
    """Kill the Linux test process if its trusted worker disappears."""

    if not sys.platform.startswith("linux"):
        return
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(PR_SET_PDEATHSIG, FORCE_KILL_SIGNAL, 0, 0, 0) != 0:
        error_number = ctypes.get_errno()
        raise OSError(error_number, os.strerror(error_number))
    # The worker may have died between spawn and prctl. Close that race instead
    # of silently continuing under the outer subreaper.
    if os.getppid() != expected_parent_pid:
        os.kill(os.getpid(), FORCE_KILL_SIGNAL)


def execute_in_child(
    test_file: str,
    metadata: object,
    expected_parent_pid: int,
) -> None:
    """Run tests and expose only fail-closed, untrusted count metadata."""

    try:
        if os.name == "posix":
            os.setsid()
        enable_parent_death_signal(expected_parent_pid)
        path = Path(test_file)
        module_name = "_hermes_isolated_test_file"
        module_spec = importlib.util.spec_from_file_location(module_name, path)
        if module_spec is None or module_spec.loader is None:
            raise RuntimeError(f"cannot import {path}")
        module = importlib.util.module_from_spec(module_spec)
        sys.modules[module_name] = module
        sys.path.insert(0, str(path.parent.resolve()))
        module_spec.loader.exec_module(module)
        suite = unittest.defaultTestLoader.loadTestsFromModule(module)
        discovered = suite.countTestCases()
        if discovered == 0:
            executed = 0
            skipped = 0
            outcome = OUTCOME_NO_TESTS
        else:
            result = unittest.TextTestRunner(verbosity=1).run(suite)
            skipped = len(result.skipped)
            executed = result.testsRun - skipped
            if executed == 0:
                outcome = OUTCOME_NO_EXECUTED_TESTS
            elif not result.wasSuccessful():
                outcome = OUTCOME_TEST_FAILURE
            else:
                outcome = OUTCOME_SUCCESS
    except BaseException as error:  # A test import must never terminate CI cleanly.
        traceback.print_exc()
        discovered = 0
        executed = 0
        skipped = 0
        outcome = OUTCOME_LOAD_FAILURE

    # This shared array is deliberately metadata-only. The supervisor derives
    # success from the reserved normal-completion exit status, never from these
    # values. A test can therefore corrupt counts only to make the run fail.
    metadata[0] = discovered
    metadata[1] = executed
    metadata[2] = skipped
    metadata[3] = outcome
    raise SystemExit(
        NORMAL_COMPLETION_EXIT_CODE if outcome == OUTCOME_SUCCESS else 1
    )


def payload_from_observation(
    exitcode: int | None,
    metadata: object,
) -> dict[str, object]:
    discovered, executed, skipped, outcome = (int(value) for value in metadata)
    counts_are_valid = (
        discovered >= 0
        and executed >= 0
        and skipped >= 0
        and executed + skipped <= discovered
    )
    if exitcode == NORMAL_COMPLETION_EXIT_CODE:
        if (
            not counts_are_valid
            or outcome != OUTCOME_SUCCESS
            or discovered == 0
            or executed == 0
        ):
            return failure("test child returned invalid completion metadata")
        return {
            "version": PROTOCOL_VERSION,
            "ok": True,
            "discovered": discovered,
            "executed": executed,
            "skipped": skipped,
            "detail": "",
        }

    details = {
        OUTCOME_NO_TESTS: "contains no unittest cases; pytest-only files are unsupported",
        OUTCOME_NO_EXECUTED_TESTS: "executed no non-skipped unittest cases",
        OUTCOME_TEST_FAILURE: "unittest suite failed",
        OUTCOME_LOAD_FAILURE: "cannot load test file",
    }
    if outcome in details and counts_are_valid:
        return failure(details[outcome])
    return failure(
        "test child exited without normal framework completion "
        f"(status {exitcode})"
    )


def signal_test_group(process: multiprocessing.Process, signal_number: int) -> None:
    """Signal the test process group without touching the worker."""

    if process.pid is None:
        return
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal_number)
            return
        except (PermissionError, ProcessLookupError):
            pass
    if process.is_alive():
        if signal_number == signal.SIGTERM:
            process.terminate()
        else:
            process.kill()


def enable_child_subreaper() -> None:
    """Adopt test descendants that detach into new sessions on Linux."""

    if not sys.platform.startswith("linux"):
        return
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(PR_SET_CHILD_SUBREAPER, 1, 0, 0, 0) != 0:
        error_number = ctypes.get_errno()
        raise OSError(error_number, os.strerror(error_number))


def linux_direct_children(
    process_id: int,
    *,
    require_visibility: bool = False,
    proc_root: Path = Path("/proc"),
) -> set[int]:
    """Read children created by every thread of one Linux process."""

    children: set[int] = set()
    process_root = proc_root / str(process_id)
    task_root = process_root / "task"
    try:
        task_directories = list(task_root.iterdir())
    except PermissionError as error:
        raise RuntimeError(
            f"cannot inspect Linux descendant tree at {task_root}"
        ) from error
    except FileNotFoundError as error:
        if require_visibility or process_root.exists():
            raise RuntimeError(
                f"cannot inspect Linux descendant tree at {task_root}"
            ) from error
        return children
    visible_children_files = 0
    for task_directory in task_directories:
        try:
            content = (task_directory / "children").read_text(
                encoding="ascii"
            ).strip()
        except PermissionError as error:
            raise RuntimeError(
                f"cannot inspect Linux descendant children at {task_directory}"
            ) from error
        except (FileNotFoundError, ProcessLookupError):
            continue
        visible_children_files += 1
        if content:
            children.update(int(value) for value in content.split())
    if visible_children_files == 0 and (require_visibility or process_root.exists()):
        raise RuntimeError(
            f"cannot inspect Linux descendant children files at {task_root}"
        )
    return children


def linux_descendants(process_id: int) -> set[int]:
    """Resolve the current descendant tree through /proc with a hard bound."""

    descendants: set[int] = set()
    pending = list(
        linux_direct_children(process_id, require_visibility=True)
    )
    while pending:
        child = pending.pop()
        if child in descendants:
            continue
        descendants.add(child)
        if len(descendants) > MAX_DESCENDANT_PROCESSES:
            raise RuntimeError(
                f"test descendant tree exceeds {MAX_DESCENDANT_PROCESSES} processes"
            )
        pending.extend(linux_direct_children(child) - descendants)
    return descendants


def linux_descendant_identities(process_id: int) -> dict[int, str]:
    """Snapshot descendants with their kernel process start times."""

    identities: dict[int, str] = {}
    for descendant in linux_descendants(process_id):
        try:
            identities[descendant] = process_start_token(descendant)
        except ProcessLookupError:
            continue
    return identities


def open_linux_descendant_pidfds(process_id: int) -> dict[int, int]:
    """Pin descendants and reject PIDs reused since the first snapshot."""

    if not sys.platform.startswith("linux"):
        return {}
    if not hasattr(os, "pidfd_open") or not hasattr(signal, "pidfd_send_signal"):
        raise RuntimeError("Linux pidfd support is unavailable")

    initial = linux_descendant_identities(process_id)
    candidates: dict[int, int] = {}
    try:
        for descendant in initial:
            try:
                candidates[descendant] = os.pidfd_open(descendant, 0)
            except ProcessLookupError:
                continue

        # A PID can disappear and be reused between /proc enumeration and
        # pidfd_open. Re-enumerating both ancestry and start time after opening
        # the handle rejects that replacement; the surviving pidfd then closes
        # the remaining race between validation and signal delivery.
        current = linux_descendant_identities(process_id)
        verified: dict[int, int] = {}
        for descendant, process_fd in candidates.items():
            if current.get(descendant) == initial[descendant]:
                verified[descendant] = process_fd
            else:
                os.close(process_fd)
        return verified
    except BaseException:
        for process_fd in candidates.values():
            try:
                os.close(process_fd)
            except OSError:
                pass
        raise


def signal_linux_descendants(signal_number: int) -> set[int]:
    """Signal verified descendant handles and close every pidfd."""

    handles = open_linux_descendant_pidfds(os.getpid())
    try:
        for process_fd in handles.values():
            try:
                signal.pidfd_send_signal(process_fd, signal_number)
            except ProcessLookupError:
                pass
        return set(handles)
    finally:
        for process_fd in handles.values():
            os.close(process_fd)


def reap_children_nonblocking() -> None:
    while True:
        try:
            process_id, _status = os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            return
        if process_id == 0:
            return


def reap_adopted_linux_children(timeout_seconds: float = 1.0) -> None:
    """Reap adopted children without relying on ps or /proc enumeration."""

    if not sys.platform.startswith("linux"):
        return
    deadline = time.monotonic() + timeout_seconds
    while True:
        try:
            process_id, _status = os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            return
        if process_id > 0:
            continue
        if time.monotonic() >= deadline:
            raise RuntimeError(
                "adopted test descendants remained alive after worker exit"
            )
        time.sleep(0.01)


def kill_and_reap_linux_descendants() -> None:
    """TERM, KILL and reap all recursively discovered/adopted descendants."""

    if not sys.platform.startswith("linux"):
        return

    descendants = signal_linux_descendants(signal.SIGTERM)
    term_deadline = time.monotonic() + CHILD_TERM_GRACE_SECONDS
    while descendants and time.monotonic() < term_deadline:
        reap_children_nonblocking()
        time.sleep(0.01)
        descendants = signal_linux_descendants(signal.SIGTERM)

    kill_deadline = time.monotonic() + CHILD_KILL_GRACE_SECONDS
    while descendants and time.monotonic() < kill_deadline:
        descendants = signal_linux_descendants(FORCE_KILL_SIGNAL)
        reap_children_nonblocking()
        time.sleep(0.01)
    reap_children_nonblocking()
    # The final snapshot is verification-only; close its pinned handles before
    # reporting the failure.
    final_handles = open_linux_descendant_pidfds(os.getpid())
    descendants = set(final_handles)
    for process_fd in final_handles.values():
        os.close(process_fd)
    if descendants:
        raise RuntimeError(
            "detached test descendants could not be reaped: "
            + ", ".join(str(value) for value in sorted(descendants))
        )


def stop_test_tree(process: multiprocessing.Process) -> bool:
    """Terminate, then forcibly kill and reap the complete test tree."""

    signal_test_group(process, signal.SIGTERM)
    process.join(CHILD_TERM_GRACE_SECONDS)
    if process.is_alive():
        signal_test_group(process, FORCE_KILL_SIGNAL)
        process.join(CHILD_KILL_GRACE_SECONDS)
    # The direct child can exit while same-group descendants remain alive.
    signal_test_group(process, FORCE_KILL_SIGNAL)
    kill_and_reap_linux_descendants()
    return not process.is_alive()


def emit_cleanup_identity(cleanup_fd: int, process_id: int) -> None:
    payload = {
        "pid": process_id,
        "start": process_start_token(process_id),
    }
    encoded = (
        CLEANUP_MARKER + json.dumps(payload, ensure_ascii=True, sort_keys=True) + "\n"
    ).encode("ascii")
    while encoded:
        written = os.write(cleanup_fd, encoded)
        encoded = encoded[written:]


def supervise(
    test_file: Path,
    timeout_seconds: float,
    cleanup_fd: int,
) -> tuple[int, dict[str, object]]:
    enable_child_subreaper()
    context = multiprocessing.get_context("spawn")
    metadata = context.Array("q", 4, lock=False)
    process = context.Process(
        target=execute_in_child,
        args=(str(test_file), metadata, os.getpid()),
    )
    payload: dict[str, object]
    try:
        process.start()
        if process.pid is None:
            raise RuntimeError("spawned test child has no process ID")
        # Only this trusted supervisor owns the registry FD. It is marked
        # non-inheritable before spawn, so test code cannot forge a cleanup PID.
        emit_cleanup_identity(cleanup_fd, process.pid)
        process.join(timeout_seconds)
        if process.is_alive():
            stopped = stop_test_tree(process)
            payload = failure(
                f"test child timed out after {timeout_seconds:g} seconds"
                + ("" if stopped else "; test child could not be reaped")
            )
        else:
            # Cleanup is required after success too: tests may have spawned
            # descendants and returned without waiting for them.
            signal_test_group(process, FORCE_KILL_SIGNAL)
            kill_and_reap_linux_descendants()
            payload = payload_from_observation(process.exitcode, metadata)
    except BaseException as error:
        traceback.print_exc()
        payload = failure(f"worker supervisor failed: {error}")
    finally:
        if process.pid is not None and process.is_alive():
            try:
                stop_test_tree(process)
            except BaseException:
                traceback.print_exc()
        try:
            kill_and_reap_linux_descendants()
        except BaseException as error:
            traceback.print_exc()
            payload = failure(f"worker descendant cleanup failed: {error}")
    return (0 if payload.get("ok") is True else 1), payload


def emit_result(result_fd: int, payload: dict[str, object]) -> None:
    encoded = (
        RESULT_MARKER + json.dumps(payload, ensure_ascii=True, sort_keys=True) + "\n"
    ).encode("utf-8")
    while encoded:
        written = os.write(result_fd, encoded)
        encoded = encoded[written:]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result-fd", type=int, required=True)
    parser.add_argument("--cleanup-fd", type=int, required=True)
    parser.add_argument("--timeout", type=float, required=True)
    parser.add_argument("test_file", type=Path)
    args = parser.parse_args(argv)

    os.set_inheritable(args.result_fd, False)
    os.set_inheritable(args.cleanup_fd, False)
    try:
        status, payload = supervise(
            args.test_file.resolve(strict=True),
            args.timeout,
            args.cleanup_fd,
        )
        emit_result(args.result_fd, payload)
    except BaseException as error:
        traceback.print_exc()
        status = 1
        emit_result(args.result_fd, failure(f"worker failed: {error}"))
    finally:
        os.close(args.cleanup_fd)
        os.close(args.result_fd)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
