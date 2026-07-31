#!/usr/bin/env python3
"""Execute one unittest file and emit the runner's machine-readable result."""

from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import sys
import traceback
import unittest


RESULT_MARKER = "HERMES_TEST_RESULT="
PROTOCOL_VERSION = 1


def emit_result(payload: dict[str, object]) -> None:
    print(
        RESULT_MARKER + json.dumps(payload, ensure_ascii=True, sort_keys=True),
        flush=True,
    )


def execute(test_file: Path) -> tuple[int, dict[str, object]]:
    output = io.StringIO()
    try:
        module_name = "_hermes_isolated_test_file"
        module_spec = importlib.util.spec_from_file_location(module_name, test_file)
        if module_spec is None or module_spec.loader is None:
            raise RuntimeError(f"cannot import {test_file}")
        module = importlib.util.module_from_spec(module_spec)
        sys.modules[module_name] = module
        sys.path.insert(0, str(test_file.parent))
        module_spec.loader.exec_module(module)
        suite = unittest.defaultTestLoader.loadTestsFromModule(module)
        discovered = suite.countTestCases()
        if discovered == 0:
            return 1, {
                "version": PROTOCOL_VERSION,
                "ok": False,
                "discovered": 0,
                "executed": 0,
                "skipped": 0,
                "detail": "contains no unittest cases; pytest-only files are unsupported",
                "output": output.getvalue(),
            }
        with redirect_stdout(output):
            result = unittest.TextTestRunner(stream=output, verbosity=1).run(suite)
        skipped = len(result.skipped)
        executed = result.testsRun - skipped
        if executed == 0:
            detail = "executed no non-skipped unittest cases"
        elif not result.wasSuccessful():
            detail = "unittest suite failed"
        else:
            detail = ""
        ok = result.wasSuccessful() and executed > 0
        return (0 if ok else 1), {
            "version": PROTOCOL_VERSION,
            "ok": ok,
            "discovered": discovered,
            "executed": executed,
            "skipped": skipped,
            "detail": detail,
            "output": output.getvalue(),
        }
    except BaseException as error:  # A test import must never terminate CI cleanly.
        return 1, {
            "version": PROTOCOL_VERSION,
            "ok": False,
            "discovered": 0,
            "executed": 0,
            "skipped": 0,
            "detail": f"cannot load test file: {error}",
            "output": output.getvalue() + traceback.format_exc(),
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("test_file", type=Path)
    args = parser.parse_args(argv)
    status, payload = execute(args.test_file.resolve(strict=True))
    emit_result(payload)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
