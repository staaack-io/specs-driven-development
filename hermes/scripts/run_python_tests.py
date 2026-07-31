#!/usr/bin/env python3
"""Discover and execute every supported Hermes unittest file."""

from __future__ import annotations

import fnmatch
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile

import run_python_test_file as test_file_worker


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKER = Path(__file__).with_name("run_python_test_file.py")
RESULT_MARKER = "HERMES_TEST_RESULT="
PROTOCOL_VERSION = 1
DEFAULT_TIMEOUT_SECONDS = 120.0
WORKER_GRACE_SECONDS = 5.0
MAX_LOG_BYTES = 64 * 1024
MAX_PROTOCOL_BYTES = 16 * 1024
FORCE_KILL_SIGNAL = getattr(signal, "SIGKILL", signal.SIGTERM)


def repository_inventory(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if result.returncode:
        detail = os.fsdecode(result.stderr).strip() or "git ls-files failed"
        raise RuntimeError(f"cannot enumerate repository tests: {detail}")
    return [
        Path(os.fsdecode(raw_path))
        for raw_path in result.stdout.split(b"\0")
        if raw_path
    ]


def discover_test_files(root: Path) -> list[Path]:
    hermes_root = (root / "hermes").resolve(strict=True)
    tests: list[Path] = []
    for relative in repository_inventory(root):
        if (
            len(relative.parts) < 2
            or relative.parts[0] != "hermes"
            or not fnmatch.fnmatchcase(relative.name, "test_*.py")
        ):
            continue
        test = root / relative
        if test.is_symlink() or not test.is_file():
            raise RuntimeError(f"unsafe Hermes test path: {relative}")
        try:
            test.resolve(strict=True).relative_to(hermes_root)
        except (OSError, ValueError) as error:
            raise RuntimeError(f"Hermes test escapes hermes/: {relative}") from error
        tests.append(test)
    return sorted(tests)


def worker_result(protocol_output: str) -> dict[str, object]:
    marker_lines = [
        line.removeprefix(RESULT_MARKER)
        for line in protocol_output.splitlines()
        if line.startswith(RESULT_MARKER)
    ]
    if len(marker_lines) != 1:
        raise RuntimeError(
            f"worker protocol error: expected one {RESULT_MARKER!r} marker, "
            f"received {len(marker_lines)}"
        )
    try:
        payload = json.loads(marker_lines[0])
    except json.JSONDecodeError as error:
        raise RuntimeError(f"worker protocol error: invalid JSON: {error}") from error
    required = {"version", "ok", "discovered", "executed", "skipped", "detail"}
    if not isinstance(payload, dict) or set(payload) != required:
        raise RuntimeError("worker protocol error: invalid result fields")
    if payload["version"] != PROTOCOL_VERSION:
        raise RuntimeError("worker protocol error: unsupported version")
    if not isinstance(payload["ok"], bool):
        raise RuntimeError("worker protocol error: ok must be boolean")
    if any(
        not isinstance(payload[name], int) or isinstance(payload[name], bool) or payload[name] < 0
        for name in ("discovered", "executed", "skipped")
    ):
        raise RuntimeError("worker protocol error: invalid test counts")
    if payload["executed"] + payload["skipped"] > payload["discovered"]:
        raise RuntimeError("worker protocol error: inconsistent test counts")
    if not isinstance(payload["detail"], str):
        raise RuntimeError("worker protocol error: invalid detail")
    if payload["ok"] and (
        payload["discovered"] == 0
        or payload["executed"] == 0
        or payload["detail"]
    ):
        raise RuntimeError("worker protocol error: invalid successful result")
    return payload


def bounded_worker_log(log_file: object) -> tuple[str, bool]:
    log_file.flush()
    log_file.seek(0)
    content = log_file.read(MAX_LOG_BYTES + 1)
    truncated = len(content) > MAX_LOG_BYTES
    return content[:MAX_LOG_BYTES].decode("utf-8", errors="replace"), truncated


def stop_worker_tree(
    process: subprocess.Popen[bytes],
    grace_seconds: float,
) -> None:
    """TERM, KILL and reap a wedged worker and its process group."""

    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except (PermissionError, ProcessLookupError):
            pass
    elif process.poll() is None:
        process.terminate()
    try:
        process.wait(grace_seconds)
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            try:
                os.killpg(process.pid, FORCE_KILL_SIGNAL)
            except (PermissionError, ProcessLookupError):
                pass
        if process.poll() is None:
            process.kill()
        try:
            process.wait(grace_seconds)
        except subprocess.TimeoutExpired as error:
            raise RuntimeError("worker process tree could not be reaped") from error
    if os.name == "posix":
        try:
            os.killpg(process.pid, FORCE_KILL_SIGNAL)
        except (PermissionError, ProcessLookupError):
            pass


def read_protocol(control_stream: object) -> str:
    encoded = control_stream.read(MAX_PROTOCOL_BYTES + 1)
    if len(encoded) > MAX_PROTOCOL_BYTES:
        raise RuntimeError("worker protocol error: result exceeds size limit")
    return encoded.decode("utf-8", errors="strict")


def run_tests(
    test_files: list[Path],
    repository_root: Path = REPOSITORY_ROOT,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    worker: Path = WORKER,
    worker_grace_seconds: float = WORKER_GRACE_SECONDS,
) -> int:
    if not test_files:
        print("error: no Hermes Python tests were discovered", file=sys.stderr)
        return 1
    try:
        # The inner worker is itself a subreaper, but it can be killed by this
        # outer timeout before cleaning a test process that called setsid().
        # Becoming the next subreaper lets this runner adopt and reap that
        # detached session instead of leaking it into the CI host.
        test_file_worker.enable_child_subreaper()
    except OSError as error:
        print(f"error: cannot enable outer child subreaper: {error}", file=sys.stderr)
        return 1

    print(f"Discovered {len(test_files)} Hermes test files.", flush=True)
    total_cases = 0
    total_executed = 0
    total_skipped = 0
    for test_file in test_files:
        try:
            display = test_file.relative_to(repository_root)
        except ValueError:
            display = test_file
        print(f"\n==> {display}", flush=True)

        read_fd, write_fd = os.pipe()
        os.set_inheritable(read_fd, False)
        os.set_inheritable(write_fd, False)
        process: subprocess.Popen[bytes] | None = None
        returncode: int | None = None
        timed_out = False
        cleanup_error: BaseException | None = None
        with (
            tempfile.TemporaryFile(mode="w+b") as worker_log,
            os.fdopen(read_fd, "rb", closefd=True) as control_stream,
        ):
            try:
                process = subprocess.Popen(
                    [
                        sys.executable,
                        str(worker),
                        "--result-fd",
                        str(write_fd),
                        "--timeout",
                        str(timeout_seconds),
                        str(test_file),
                    ],
                    cwd=repository_root,
                    pass_fds=(write_fd,),
                    stdout=worker_log,
                    stderr=subprocess.STDOUT,
                    start_new_session=os.name == "posix",
                )
                try:
                    returncode = process.wait(
                        timeout_seconds + worker_grace_seconds
                    )
                except subprocess.TimeoutExpired:
                    timed_out = True
                    try:
                        stop_worker_tree(process, worker_grace_seconds)
                    except BaseException as error:
                        cleanup_error = error
            finally:
                os.close(write_fd)
                try:
                    # On Linux, children from a detached test session are now
                    # adopted by this subreaper after the worker exits. Cleanup
                    # is required after normal worker completion as well as an
                    # outer timeout, because a wedged worker may exit early.
                    test_file_worker.kill_and_reap_linux_descendants()
                except BaseException as enumeration_error:
                    try:
                        # The direct test child has PDEATHSIG=SIGKILL. Once the
                        # worker dies, this subreaper can therefore reap it via
                        # waitpid even when ps or /proc cannot enumerate PIDs.
                        test_file_worker.reap_adopted_linux_children()
                    except BaseException as fallback_error:
                        cleanup_error = RuntimeError(
                            "process enumeration failed: "
                            f"{enumeration_error}; waitpid fallback failed: "
                            f"{fallback_error}"
                        )

            protocol_output = read_protocol(control_stream)
            log_output, truncated = bounded_worker_log(worker_log)

        if log_output:
            print(log_output, end="" if log_output.endswith("\n") else "\n")
        if truncated:
            print(f"[worker output truncated after {MAX_LOG_BYTES} bytes]")
        if cleanup_error is not None:
            print(
                f"error: {display}: outer descendant cleanup failed: "
                f"{cleanup_error}",
                file=sys.stderr,
            )
            return 1
        if timed_out:
            print(
                f"error: {display} supervisor timed out after "
                f"{timeout_seconds + worker_grace_seconds:g} seconds",
                file=sys.stderr,
            )
            return 1
        try:
            payload = worker_result(protocol_output)
        except (RuntimeError, UnicodeError) as error:
            print(f"error: {display}: {error}", file=sys.stderr)
            return 1
        if returncode == 0 and not payload["ok"]:
            print(f"error: {display}: worker status contradicts result", file=sys.stderr)
            return 1
        if returncode != 0 or not payload["ok"]:
            detail = payload["detail"] or f"worker exited with status {returncode}"
            print(f"error: {display}: {detail}", file=sys.stderr)
            return 1
        total_cases += payload["discovered"]
        total_executed += payload["executed"]
        total_skipped += payload["skipped"]

    print(
        f"\nAll {total_executed} Hermes test cases executed "
        f"({total_skipped} skipped; {total_cases} discovered)."
    )
    return 0


def main(root: Path = REPOSITORY_ROOT) -> int:
    try:
        tests = discover_test_files(root.resolve(strict=True))
    except (OSError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return run_tests(tests, root)


if __name__ == "__main__":
    raise SystemExit(main())
