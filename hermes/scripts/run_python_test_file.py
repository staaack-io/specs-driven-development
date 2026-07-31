#!/usr/bin/env python3
"""Supervise one isolated unittest process and report through a private FD."""

from __future__ import annotations

import argparse
import ctypes
import importlib.util
import json
import multiprocessing
from multiprocessing.connection import Connection
import os
from pathlib import Path
import signal
import sys
import time
import traceback
import unittest


RESULT_MARKER = "HERMES_TEST_RESULT="
PROTOCOL_VERSION = 1
MAX_DETAIL_CHARACTERS = 4096
CHILD_TERM_GRACE_SECONDS = 0.25
CHILD_KILL_GRACE_SECONDS = 1.0
MAX_DESCENDANT_PROCESSES = 4096
FORCE_KILL_SIGNAL = getattr(signal, "SIGKILL", signal.SIGTERM)
PR_SET_CHILD_SUBREAPER = 36


def failure(detail: str) -> dict[str, object]:
    return {
        "version": PROTOCOL_VERSION,
        "ok": False,
        "discovered": 0,
        "executed": 0,
        "skipped": 0,
        "detail": detail[:MAX_DETAIL_CHARACTERS],
    }


def execute_in_child(test_file: str, result_connection: Connection) -> None:
    """Load and run tests in a spawned process with no supervisor result FD."""

    try:
        os.set_inheritable(result_connection.fileno(), False)
        if os.name == "posix":
            os.setsid()
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
            payload = failure(
                "contains no unittest cases; pytest-only files are unsupported"
            )
        else:
            result = unittest.TextTestRunner(verbosity=1).run(suite)
            skipped = len(result.skipped)
            executed = result.testsRun - skipped
            if executed == 0:
                detail = "executed no non-skipped unittest cases"
            elif not result.wasSuccessful():
                detail = "unittest suite failed"
            else:
                detail = ""
            ok = result.wasSuccessful() and executed > 0
            payload = {
                "version": PROTOCOL_VERSION,
                "ok": ok,
                "discovered": discovered,
                "executed": executed,
                "skipped": skipped,
                "detail": detail,
            }
    except BaseException as error:  # A test import must never terminate CI cleanly.
        traceback.print_exc()
        payload = failure(f"cannot load test file: {error}")
    try:
        result_connection.send(payload)
    finally:
        result_connection.close()


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


def linux_direct_children(process_id: int) -> set[int]:
    """Read children created by every thread of one Linux process."""

    children: set[int] = set()
    task_root = Path(f"/proc/{process_id}/task")
    try:
        task_directories = list(task_root.iterdir())
    except (FileNotFoundError, PermissionError):
        return children
    for task_directory in task_directories:
        try:
            content = (task_directory / "children").read_text(
                encoding="ascii"
            ).strip()
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if content:
            children.update(int(value) for value in content.split())
    return children


def linux_descendants(process_id: int) -> set[int]:
    """Resolve the current descendant tree through /proc with a hard bound."""

    descendants: set[int] = set()
    pending = list(linux_direct_children(process_id))
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


def reap_children_nonblocking() -> None:
    while True:
        try:
            process_id, _status = os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            return
        if process_id == 0:
            return


def kill_and_reap_linux_descendants() -> None:
    """TERM, KILL and reap all recursively discovered/adopted descendants."""

    if not sys.platform.startswith("linux"):
        return

    descendants = linux_descendants(os.getpid())
    for process_id in descendants:
        try:
            os.kill(process_id, signal.SIGTERM)
        except (PermissionError, ProcessLookupError):
            pass
    term_deadline = time.monotonic() + CHILD_TERM_GRACE_SECONDS
    while descendants and time.monotonic() < term_deadline:
        reap_children_nonblocking()
        time.sleep(0.01)
        descendants = linux_descendants(os.getpid())

    kill_deadline = time.monotonic() + CHILD_KILL_GRACE_SECONDS
    while descendants and time.monotonic() < kill_deadline:
        for process_id in descendants:
            try:
                os.kill(process_id, FORCE_KILL_SIGNAL)
            except (PermissionError, ProcessLookupError):
                pass
        reap_children_nonblocking()
        time.sleep(0.01)
        descendants = linux_descendants(os.getpid())
    reap_children_nonblocking()
    descendants = linux_descendants(os.getpid())
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


def supervise(test_file: Path, timeout_seconds: float) -> tuple[int, dict[str, object]]:
    enable_child_subreaper()
    context = multiprocessing.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(
        target=execute_in_child,
        args=(str(test_file), sender),
    )
    payload: dict[str, object]
    try:
        process.start()
        sender.close()
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
            try:
                if not receiver.poll(0):
                    raise EOFError
                received = receiver.recv()
            except (EOFError, OSError):
                received = None
            if not isinstance(received, dict):
                payload = failure(
                    f"test child exited without a result (status {process.exitcode})"
                )
            else:
                payload = received
            if process.exitcode != 0:
                payload = failure(
                    f"test child result contradicted exit status {process.exitcode}"
                )
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
        receiver.close()
        sender.close()
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
    parser.add_argument("--timeout", type=float, required=True)
    parser.add_argument("test_file", type=Path)
    args = parser.parse_args(argv)

    os.set_inheritable(args.result_fd, False)
    try:
        status, payload = supervise(
            args.test_file.resolve(strict=True),
            args.timeout,
        )
        emit_result(args.result_fd, payload)
    except BaseException as error:
        traceback.print_exc()
        status = 1
        emit_result(args.result_fd, failure(f"worker failed: {error}"))
    finally:
        os.close(args.result_fd)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
