#!/usr/bin/env python3
"""Supervise one isolated unittest process and report through a private FD."""

from __future__ import annotations

import argparse
import importlib.util
import json
import multiprocessing
from multiprocessing.connection import Connection
import os
from pathlib import Path
import sys
import traceback
import unittest


RESULT_MARKER = "HERMES_TEST_RESULT="
PROTOCOL_VERSION = 1
MAX_DETAIL_CHARACTERS = 4096


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
        path = Path(test_file)
        module_name = "_hermes_isolated_test_file"
        module_spec = importlib.util.spec_from_file_location(module_name, path)
        if module_spec is None or module_spec.loader is None:
            raise RuntimeError(f"cannot import {path}")
        module = importlib.util.module_from_spec(module_spec)
        sys.modules[module_name] = module
        sys.path.insert(0, str(path.parent))
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


def supervise(test_file: Path) -> tuple[int, dict[str, object]]:
    context = multiprocessing.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(
        target=execute_in_child,
        args=(str(test_file), sender),
    )
    process.start()
    sender.close()
    process.join()

    payload: dict[str, object] | None = None
    if receiver.poll():
        try:
            received = receiver.recv()
        except (EOFError, OSError):
            received = None
        if isinstance(received, dict):
            payload = received
    receiver.close()

    if payload is None:
        payload = failure(
            f"test child exited without a result (status {process.exitcode})"
        )
    elif process.exitcode != 0:
        payload = failure(
            f"test child result contradicted exit status {process.exitcode}"
        )
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
    parser.add_argument("test_file", type=Path)
    args = parser.parse_args(argv)

    # pass_fds makes this descriptor inheritable for the worker exec. Revoke
    # inheritance before spawning the untrusted test process.
    os.set_inheritable(args.result_fd, False)
    try:
        status, payload = supervise(args.test_file.resolve(strict=True))
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
