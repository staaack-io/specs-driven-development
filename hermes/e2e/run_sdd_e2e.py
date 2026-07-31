#!/usr/bin/env python3
"""Run the SDD specification-to-plan smoke test through Hermes Agent 0.19."""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import uuid


MIN_HERMES_VERSION = (0, 19, 0)
MIN_PROFILE_VERSION = (0, 4, 7)
RUN_PREFIX = "sdd-hermes-e2e-"
SENTINEL = ".sdd-hermes-e2e-run.json"
AUTOMATED_ACTOR = "automated-e2e"
FEATURE_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,38}[a-z0-9])?$")
SESSION_RE = re.compile(r"(?m)^session_id:\s*([A-Za-z0-9_.:-]+)\s*$")
TASK_HEADING_RE = re.compile(r"(?m)^###\s+(T-\d{3})\b[^\n]*$")
TEST_ID_RE = re.compile(r"\bT-\d{3}-T\d+\b")
TEST_ID_FIELD_RE = re.compile(
    r"^\s*[-*]\s+(?:\*\*)?Test-IDs\s*:(?:\*\*)?\s*(.*?)\s*$",
    re.IGNORECASE,
)
TEST_ID_DEFINITION_RE = re.compile(r"^\s{2,}[-*]\s+(T-\d{3}-T\d+)\b")


class E2EError(RuntimeError):
    """Expected harness failure with a user-actionable message."""


@dataclasses.dataclass(frozen=True)
class CommandResult:
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float


def parse_version(value: str, label: str) -> tuple[int, int, int]:
    match = re.search(r"(?<!\d)(\d+)\.(\d+)\.(\d+)(?!\d)", value)
    if not match:
        raise E2EError(f"Impossible de lire la version {label} dans: {value!r}")
    return tuple(int(part) for part in match.groups())


def version_text(version: tuple[int, int, int]) -> str:
    return ".".join(str(part) for part in version)


def resolve_hermes_binary(value: str) -> str:
    if os.sep in value:
        candidate = Path(value).expanduser().resolve()
        if not candidate.is_file() or not os.access(candidate, os.X_OK):
            raise E2EError(f"Binaire Hermes non exécutable: {candidate}")
        return str(candidate)
    resolved = shutil.which(value)
    if not resolved:
        raise E2EError(f"Binaire Hermes introuvable dans PATH: {value}")
    return str(Path(resolved).resolve())


def validated_temp_root(value: str | None) -> Path:
    root = Path(value or tempfile.gettempdir()).expanduser().resolve()
    if not root.is_dir():
        raise E2EError(f"Racine temporaire absente: {root}")
    if root == Path(root.anchor) or root == Path.home().resolve():
        raise E2EError(f"Racine temporaire trop large: {root}")
    return root


def create_run_dir(temp_root: Path) -> Path:
    raw = Path(tempfile.mkdtemp(prefix=RUN_PREFIX, dir=str(temp_root)))
    run_dir = raw.resolve(strict=True)
    if run_dir.parent != temp_root or not run_dir.name.startswith(RUN_PREFIX):
        raise E2EError(f"mktemp a retourné un chemin inattendu: {run_dir}")
    sentinel = {
        "schema": 1,
        "run_id": str(uuid.uuid4()),
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "realpath": str(run_dir),
    }
    (run_dir / SENTINEL).write_text(json.dumps(sentinel, indent=2) + "\n", encoding="utf-8")
    (run_dir / "project").mkdir()
    (run_dir / "logs").mkdir()
    return run_dir


def validate_cleanup_target(run_dir: Path, temp_root: Path) -> Path:
    resolved_root = temp_root.resolve(strict=True)
    resolved_run = validate_run_sentinel(run_dir)
    if resolved_run.parent != resolved_root:
        raise E2EError(f"Nettoyage refusé hors de la racine temporaire: {resolved_run}")
    return resolved_run


def validate_run_sentinel(run_dir: Path) -> Path:
    resolved_run = run_dir.expanduser().resolve(strict=True)
    if not resolved_run.is_dir() or run_dir.is_symlink():
        raise E2EError(f"Run refusé: dossier réel attendu ({run_dir})")
    if not resolved_run.name.startswith(RUN_PREFIX):
        raise E2EError(f"Run refusé pour un nom inattendu: {resolved_run.name}")
    sentinel_path = resolved_run / SENTINEL
    if not sentinel_path.is_file() or sentinel_path.is_symlink():
        raise E2EError(f"Run refusé: sentinelle absente dans {resolved_run}")
    try:
        sentinel = json.loads(sentinel_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise E2EError(f"Run refusé: sentinelle illisible ({exc})") from exc
    if sentinel.get("schema") != 1 or sentinel.get("realpath") != str(resolved_run):
        raise E2EError("Run refusé: sentinelle incohérente")
    try:
        uuid.UUID(str(sentinel["run_id"]))
    except (KeyError, ValueError) as exc:
        raise E2EError("Run refusé: identifiant de sentinelle invalide") from exc
    return resolved_run


@contextlib.contextmanager
def profile_lock(temp_root: Path, profile: str, hermes_bin: str):
    digest = hashlib.sha256(f"{profile}\0{hermes_bin}".encode()).hexdigest()[:20]
    lock_path = temp_root / f".sdd-hermes-e2e-{digest}.lock"
    flags = os.O_RDWR | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(lock_path, flags, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise E2EError(f"Verrou non régulier refusé: {lock_path}")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise E2EError(f"Un test Hermes utilise déjà le profil {profile!r}") from exc
        os.ftruncate(fd, 0)
        os.write(fd, f"pid={os.getpid()}\n".encode())
        yield
    finally:
        with contextlib.suppress(OSError):
            fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def terminate_process_group(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    with contextlib.suppress(ProcessLookupError):
        os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=5)
        return
    except subprocess.TimeoutExpired:
        pass
    with contextlib.suppress(ProcessLookupError):
        os.killpg(process.pid, signal.SIGKILL)
    with contextlib.suppress(subprocess.TimeoutExpired):
        process.wait(timeout=5)


def run_command(
    argv: list[str],
    *,
    cwd: Path,
    timeout: float,
    logs_dir: Path,
    step: str,
) -> CommandResult:
    started = time.monotonic()
    process = subprocess.Popen(
        argv,
        cwd=str(cwd),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        terminate_process_group(process)
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            # A descendant that deliberately escaped the process group may keep
            # inherited pipes open. Never let log draining defeat the timeout.
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode(errors="replace")
            if isinstance(stderr, bytes):
                stderr = stderr.decode(errors="replace")
            for stream in (process.stdout, process.stderr):
                if stream is not None:
                    with contextlib.suppress(OSError):
                        stream.close()
        write_command_log(logs_dir, step, argv, process.returncode, stdout, stderr, time.monotonic() - started)
        raise E2EError(f"Délai de {timeout:g}s dépassé pendant {step}") from exc
    result = CommandResult(
        argv=tuple(argv),
        returncode=process.returncode,
        stdout=stdout,
        stderr=stderr,
        duration_seconds=time.monotonic() - started,
    )
    write_command_log(logs_dir, step, argv, result.returncode, stdout, stderr, result.duration_seconds)
    if result.returncode != 0:
        raise E2EError(f"Commande {step} en échec (code {result.returncode}); voir logs/{step}.json")
    return result


def write_command_log(
    logs_dir: Path,
    step: str,
    argv: list[str],
    returncode: int | None,
    stdout: str,
    stderr: str,
    duration: float,
) -> None:
    payload = {
        "argv": argv,
        "returncode": returncode,
        "duration_seconds": round(duration, 3),
        "stdout": stdout,
        "stderr": stderr,
    }
    (logs_dir / f"{step}.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_fixture(project: Path) -> None:
    files = {
        "AGENTS.md": """# Bac à sable SDD E2E\n\nCe dépôt jetable sert uniquement à tester le workflow SDD. Pendant les commandes\nSDD, écrire exclusivement sous `.specs/`; ne modifier aucun fichier applicatif.\nLa fonctionnalité service-state concerne ensemble le contrôleur Spring backend et\nla page React/Next.js frontend décrits dans `README.md`.\n""",
        "README.md": """# Full-stack service state fixture\n\n`backend/src/main/java/io/staaack/e2e/ServiceStateController.java` est le point\nd'entrée Spring lié à l'état de service. `frontend/app/page.tsx` est la page\nNext.js/React qui l'affichera. Le scénario E2E planifie leur évolution sans la\nréaliser.\n""",
        "pom.xml": """<project xmlns=\"http://maven.apache.org/POM/4.0.0\">\n  <modelVersion>4.0.0</modelVersion><groupId>io.staaack</groupId>\n  <artifactId>sdd-e2e</artifactId><version>1.0.0</version>\n  <packaging>pom</packaging><modules><module>backend</module></modules>\n</project>\n""",
        "backend/pom.xml": """<project xmlns=\"http://maven.apache.org/POM/4.0.0\">\n  <modelVersion>4.0.0</modelVersion><parent><groupId>org.springframework.boot</groupId>\n  <artifactId>spring-boot-starter-parent</artifactId><version>4.0.0</version>\n  <relativePath/></parent><groupId>io.staaack</groupId><artifactId>backend</artifactId>\n  <dependencies><dependency><groupId>org.springframework.boot</groupId>\n  <artifactId>spring-boot-starter-web</artifactId></dependency></dependencies>\n</project>\n""",
        "backend/src/main/java/io/staaack/e2e/ServiceStateController.java": """package io.staaack.e2e;\n\nimport org.springframework.web.bind.annotation.RestController;\n\n@RestController\npublic final class ServiceStateController {}\n""",
        "frontend/package.json": """{\n  \"private\": true,\n  \"dependencies\": {\"next\": \"16.0.0\", \"react\": \"19.0.0\", \"react-dom\": \"19.0.0\"}\n}\n""",
        "frontend/app/page.tsx": """export default function Page() {\n  return <main>Service state unavailable</main>;\n}\n""",
    }
    for relative, content in files.items():
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def project_snapshot(project: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for path in sorted(project.rglob("*")):
        relative = path.relative_to(project)
        if relative.parts and relative.parts[0] == ".specs":
            continue
        info = path.lstat()
        mode = stat.S_IMODE(info.st_mode)
        if stat.S_ISLNK(info.st_mode):
            value = f"symlink:{mode}:" + os.readlink(path)
        elif stat.S_ISDIR(info.st_mode):
            value = f"dir:{mode}"
        elif stat.S_ISREG(info.st_mode):
            value = f"file:{mode}:" + hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            value = f"other:{stat.S_IFMT(info.st_mode)}"
        snapshot[str(relative)] = value
    return snapshot


def assert_write_boundary(project: Path, baseline: dict[str, str]) -> None:
    current = project_snapshot(project)
    if current != baseline:
        changed = sorted(set(current) ^ set(baseline) | {key for key in current.keys() & baseline.keys() if current[key] != baseline[key]})
        raise E2EError("Écriture détectée hors de .specs: " + ", ".join(changed))
    specs = project / ".specs"
    if not specs.exists():
        return
    if specs.is_symlink() or not specs.is_dir():
        raise E2EError(".specs doit être un dossier réel, pas un lien")
    specs_real = specs.resolve(strict=True)
    for path in specs.rglob("*"):
        if path.is_symlink():
            raise E2EError(f"Lien symbolique refusé dans .specs: {path.relative_to(project)}")
        if not path.resolve(strict=True).is_relative_to(specs_real):
            raise E2EError(f"Chemin échappant à .specs: {path}")


def chat_turn(
    hermes_bin: str,
    profile: str,
    prompt: str,
    *,
    resume: str | None,
    project: Path,
    logs_dir: Path,
    timeout: float,
    step: str,
) -> str:
    argv = [hermes_bin, "--profile", profile, "chat", "-Q", "--source", "tool", "--pass-session-id"]
    if resume:
        argv.extend(["--resume", resume])
    argv.extend(["-q", prompt])
    result = run_command(argv, cwd=project, timeout=timeout, logs_dir=logs_dir, step=step)
    matches = SESSION_RE.findall(result.stderr)
    if not matches:
        raise E2EError(f"Hermes n'a pas exposé de session_id pendant {step}")
    return matches[-1]


def field(text: str, name: str) -> str | None:
    match = re.search(rf"(?mi)^\s*(?:[-*]\s*)?{re.escape(name)}\s*:\s*(.*?)\s*$", text)
    return match.group(1).strip() if match else None


def require_field(text: str, name: str, expected: str) -> None:
    actual = field(text, name)
    if actual != expected:
        raise E2EError(f"Champ {name!r}: attendu {expected!r}, obtenu {actual!r}")


def validate_provisional_review(review: Path) -> None:
    if not review.is_file():
        raise E2EError("02-spec-review.md absent après /sdd-spec-review")
    text = review.read_text(encoding="utf-8")
    require_field(text, "verdict", "ready-for-approval")
    evidence = field(text, "decision_evidence")
    if evidence not in {"en attente", "pending"}:
        raise E2EError(f"La revue provisoire contient déjà une décision: {evidence!r}")


def validate_final_review(review: Path) -> None:
    text = review.read_text(encoding="utf-8")
    require_field(text, "verdict", "approve")
    require_field(text, "decision_evidence", "approve")
    require_field(text, "decision_evidence_mode", "direct-response")
    reviewer = field(text, "reviewer")
    if reviewer != AUTOMATED_ACTOR:
        raise E2EError(
            f"La décision automatisée est attribuée à {reviewer!r}, attendu {AUTOMATED_ACTOR!r}; "
            "elle ne doit jamais être présentée comme une approbation humaine"
        )


def run_plan_oneshot(
    hermes_bin: str,
    profile: str,
    feature_id: str,
    *,
    project: Path,
    logs_dir: Path,
    timeout: float,
) -> str:
    usage_file = logs_dir / "06-sdd-plan-usage.json"
    prompt = (
        f"/sdd-plan {feature_id}\n\n"
        "Contexte du harness automatisé : ce processus utilise le canal stateless `hermes -z` de Hermes 0.19.0. "
        "Dans ce canal, `delegate_task` retourne les deux analyses de manière synchrone dans ce même tour. "
        "Après leur retour, traite-les et écris seulement `03-design.candidate.md` et `04-tasks.candidate.md`. "
        "Ne demande ni ne déduis l'approbation du plan, ne crée pas `.tdd-state.json` et ne modifie aucun code."
    )
    argv = [
        hermes_bin,
        "--profile",
        profile,
        "--usage-file",
        str(usage_file),
        "-z",
        prompt,
    ]
    run_command(argv, cwd=project, timeout=timeout, logs_dir=logs_dir, step="06-sdd-plan")
    try:
        usage = json.loads(usage_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise E2EError(f"Usage-file Hermes absent ou invalide: {exc}") from exc
    session_id = str(usage.get("session_id") or "").strip()
    if not session_id:
        raise E2EError("Hermes -z n'a pas inscrit session_id dans --usage-file")
    return session_id


def export_transcript(
    hermes_bin: str,
    profile: str,
    session_id: str,
    *,
    project: Path,
    logs_dir: Path,
    timeout: float,
    index: int,
) -> Path:
    output = logs_dir / f"session-{index:02d}-{session_id}.jsonl"
    argv = [
        hermes_bin,
        "--profile",
        profile,
        "sessions",
        "export",
        str(output),
        "--session-id",
        session_id,
        "--format",
        "jsonl",
        "--redact",
    ]
    run_command(argv, cwd=project, timeout=timeout, logs_dir=logs_dir, step=f"07-export-{index:02d}")
    if not output.is_file() or not output.read_text(encoding="utf-8").strip():
        raise E2EError(f"Export de session vide pour {session_id}")
    return output


def parse_test_id_definitions(tasks_text: str) -> tuple[list[str], list[str]]:
    headings = list(TASK_HEADING_RE.finditer(tasks_text))
    if not headings:
        raise E2EError("Aucune section de tâche structurée trouvée")

    task_ids: list[str] = []
    test_ids: list[str] = []
    for index, heading in enumerate(headings):
        task_id = heading.group(1)
        task_ids.append(task_id)
        end = headings[index + 1].start() if index + 1 < len(headings) else len(tasks_text)
        section_lines = tasks_text[heading.end():end].splitlines()
        definitions: list[str] = []

        for line_index, line in enumerate(section_lines):
            field_match = TEST_ID_FIELD_RE.match(line)
            if not field_match:
                continue
            definitions.extend(TEST_ID_RE.findall(field_match.group(1)))
            for continuation in section_lines[line_index + 1:]:
                definition_match = TEST_ID_DEFINITION_RE.match(continuation)
                if definition_match:
                    definitions.append(definition_match.group(1))
                    continue
                if continuation.strip() and not continuation.startswith((" ", "\t")):
                    break
                if re.match(r"^\s+[-*]\s+", continuation):
                    break

        if not definitions:
            raise E2EError(f"Aucune définition Test-ID structurée pour {task_id}")
        expected_prefix = f"{task_id}-T"
        mismatched = [test_id for test_id in definitions if not test_id.startswith(expected_prefix)]
        if mismatched:
            raise E2EError(
                f"Préfixe Test-ID incohérent pour {task_id}: " + ", ".join(mismatched)
            )
        test_ids.extend(definitions)

    duplicates = sorted({test_id for test_id in test_ids if test_ids.count(test_id) > 1})
    if duplicates:
        raise E2EError("Définitions Test-ID dupliquées: " + ", ".join(duplicates))
    return task_ids, test_ids


def validate_plan(project: Path, feature_id: str, plan_transcript: Path) -> dict[str, int]:
    feature = project / ".specs" / feature_id
    design = feature / "03-design.candidate.md"
    tasks = feature / "04-tasks.candidate.md"
    if not design.is_file() or not tasks.is_file():
        raise E2EError("Le plan synchrone n'a pas produit les deux artefacts candidats")
    forbidden = [feature / "03-design.md", feature / "04-tasks.md", feature / ".tdd-state.json"]
    existing = [path.name for path in forbidden if path.exists()]
    if existing:
        raise E2EError("Le plan a été approuvé ou initialisé sans décision dédiée: " + ", ".join(existing))

    design_text = design.read_text(encoding="utf-8")
    tasks_text = tasks.read_text(encoding="utf-8")
    if field(design_text, "status") != "draft" or field(design_text, "stacks") != "full-stack":
        raise E2EError("Le candidat de design doit rester draft et full-stack")
    for role in ("spring-architect", "react-nextjs-architect"):
        if role not in design_text:
            raise E2EError(f"Rôle absent du design candidat: {role}")
        if f"{role}:" not in tasks_text:
            raise E2EError(f"Origine de tâche absente: {role}")

    task_ids, test_ids = parse_test_id_definitions(tasks_text)
    if len(task_ids) < 2 or len(task_ids) != len(set(task_ids)):
        raise E2EError("Les Task-IDs full-stack sont absents ou non uniques")

    spec_text = (feature / "01-spec.md").read_text(encoding="utf-8")
    ac_ids = sorted(set(re.findall(r"\bAC-\d{3}\b", spec_text)))
    missing_acs = [ac_id for ac_id in ac_ids if ac_id not in tasks_text]
    if not ac_ids or missing_acs:
        raise E2EError("Couverture AC incomplète dans les tâches: " + ", ".join(missing_acs))

    transcript_text = plan_transcript.read_text(encoding="utf-8")
    if "delegate_task" not in transcript_text:
        raise E2EError("Le transcript ne prouve pas l'appel à delegate_task")
    for role in ("spring-architect", "react-nextjs-architect"):
        if role not in transcript_text and role not in design_text:
            raise E2EError(f"Aucune preuve de délégation pour {role}")
    return {"acceptance_criteria": len(ac_ids), "tasks": len(task_ids), "tests": len(test_ids)}


def validate_preserved_run(args: argparse.Namespace) -> int:
    if args.dry_run or args.cleanup_on_success:
        raise E2EError("--validate-run est incompatible avec --dry-run et --cleanup-on-success")
    if not args.feature_id:
        raise E2EError("--feature-id est obligatoire avec --validate-run")
    if len(args.feature_id) > 40 or not FEATURE_RE.fullmatch(args.feature_id):
        raise E2EError(f"feature-id invalide: {args.feature_id!r}")
    if not args.plan_transcript:
        raise E2EError("--plan-transcript est obligatoire avec --validate-run")

    run_dir = validate_run_sentinel(Path(args.validate_run))
    project = run_dir / "project"
    logs_dir = run_dir / "logs"
    for label, directory in (("project", project), ("logs", logs_dir)):
        if not directory.is_dir() or directory.is_symlink():
            raise E2EError(f"Run refusé: dossier {label} absent ou symbolique")

    supplied_transcript = Path(args.plan_transcript).expanduser()
    if supplied_transcript.is_symlink():
        raise E2EError("Transcript de plan symbolique refusé")
    transcript = supplied_transcript.resolve(strict=True)
    logs_real = logs_dir.resolve(strict=True)
    if transcript.parent != logs_real:
        raise E2EError("Le transcript de plan doit être un fichier direct de logs/")
    if not transcript.is_file() or not transcript.name.startswith("session-") or transcript.suffix != ".jsonl":
        raise E2EError("Transcript de plan inattendu; choisir explicitement un fichier session-*.jsonl")

    counts = validate_plan(project, args.feature_id, transcript)
    result = {
        "status": "revalidated",
        "run_dir": str(run_dir),
        "feature_id": args.feature_id,
        "plan_transcript": str(transcript),
        "llm_calls": 0,
        "checks": counts,
    }
    print(json.dumps(result, indent=2))
    return 0


def dry_run_plan(args: argparse.Namespace) -> None:
    feature_id = args.feature_id or f"{dt.date.today().isoformat()}-service-state-e2e"
    commands = [
        [args.hermes_bin, "--version"],
        [args.hermes_bin, "profile", "info", args.profile],
        [args.hermes_bin, "--profile", args.profile, "chat", "-Q", "--source", "tool", "--pass-session-id", "-q", "/sdd-help"],
        [args.hermes_bin, "--profile", args.profile, "chat", "-Q", "--source", "tool", "--pass-session-id", "--resume", "{SESSION_ID}", "-q", "/sdd-status"],
        ["...", "/sdd-spec ..."],
        ["...", f"/sdd-spec-review {feature_id}"],
        ["...", "approve  # appel séparé; acteur automated-e2e"],
        [args.hermes_bin, "--profile", args.profile, "--usage-file", "{LOGS}/plan-usage.json", "-z", f"/sdd-plan {feature_id} ..."],
        [args.hermes_bin, "--profile", args.profile, "sessions", "export", "{LOGS}/session.jsonl", "--session-id", "{SESSION_ID}", "--format", "jsonl", "--redact"],
    ]
    print(json.dumps({"dry_run": True, "creates_sandbox": False, "feature_id": feature_id, "commands": commands}, indent=2))


def execute(args: argparse.Namespace) -> int:
    if args.validate_run:
        return validate_preserved_run(args)
    if args.dry_run:
        dry_run_plan(args)
        return 0
    if args.timeout <= 0:
        raise E2EError("--timeout doit être strictement positif")
    feature_id = args.feature_id or f"{dt.date.today().isoformat()}-service-state-e2e"
    if len(feature_id) > 40 or not FEATURE_RE.fullmatch(feature_id):
        raise E2EError(f"feature-id invalide: {feature_id!r}")
    hermes_bin = resolve_hermes_binary(args.hermes_bin)
    temp_root = validated_temp_root(args.temp_root)
    run_dir: Path | None = None
    success = False

    with profile_lock(temp_root, args.profile, hermes_bin):
        run_dir = create_run_dir(temp_root)
        project = run_dir / "project"
        logs_dir = run_dir / "logs"
        try:
            version_result = run_command([hermes_bin, "--version"], cwd=project, timeout=args.timeout, logs_dir=logs_dir, step="00-hermes-version")
            hermes_version = parse_version(version_result.stdout + version_result.stderr, "Hermes")
            if hermes_version < MIN_HERMES_VERSION:
                raise E2EError(f"Hermes {version_text(hermes_version)} < {version_text(MIN_HERMES_VERSION)}")

            profile_result = run_command([hermes_bin, "profile", "info", args.profile], cwd=project, timeout=args.timeout, logs_dir=logs_dir, step="00-profile-info")
            profile_version = parse_version(profile_result.stdout + profile_result.stderr, "du profil")
            if profile_version < MIN_PROFILE_VERSION:
                raise E2EError(f"Profil {version_text(profile_version)} < {version_text(MIN_PROFILE_VERSION)}")

            write_fixture(project)
            baseline = project_snapshot(project)
            session_ids: list[str] = []

            session_id = chat_turn(hermes_bin, args.profile, "/sdd-help", resume=None, project=project, logs_dir=logs_dir, timeout=args.timeout, step="01-sdd-help")
            session_ids.append(session_id)
            assert_write_boundary(project, baseline)
            session_id = chat_turn(hermes_bin, args.profile, "/sdd-status", resume=session_id, project=project, logs_dir=logs_dir, timeout=args.timeout, step="02-sdd-status")
            session_ids.append(session_id)
            assert_write_boundary(project, baseline)

            spec_prompt = (
                f"/sdd-spec Utilise exactement le feature-id `{feature_id}`. "
                "Source: scénario local fourni dans cette conversation, sans ticket externe. "
                "Un opérateur consulte un tableau de bord full-stack. Le backend Spring doit exposer GET /api/service-state "
                "sans authentification, sans persistance et sans pagination; il répond HTTP 200 avec le JSON exact "
                "{\"state\":\"operational\"}. La page React/Next.js doit afficher le texte exact `Service operational`. "
                "Les erreurs réseau affichent exactement `Service state unavailable`. Aucun autre comportement n'est dans le périmètre. "
                f"Ce scénario est automatisé: toute décision ultérieure doit être attribuée à `{AUTOMATED_ACTOR}`, jamais à un humain."
            )
            session_id = chat_turn(hermes_bin, args.profile, spec_prompt, resume=session_id, project=project, logs_dir=logs_dir, timeout=args.timeout, step="03-sdd-spec")
            session_ids.append(session_id)
            assert_write_boundary(project, baseline)
            spec = project / ".specs" / feature_id / "01-spec.md"
            if not spec.is_file():
                raise E2EError(f"Spécification absente: {spec}")

            review_prompt = (
                f"/sdd-spec-review {feature_id}\n"
                f"Le prochain tour de décision proviendra de l'acteur de test `{AUTOMATED_ACTOR}`. "
                "S'il répond approve, consigne ce nom exact comme reviewer; ce n'est pas une approbation humaine."
            )
            session_id = chat_turn(hermes_bin, args.profile, review_prompt, resume=session_id, project=project, logs_dir=logs_dir, timeout=args.timeout, step="04-sdd-spec-review")
            session_ids.append(session_id)
            assert_write_boundary(project, baseline)
            review = project / ".specs" / feature_id / "02-spec-review.md"
            validate_provisional_review(review)

            # Deliberately a separate process and conversation turn. Do not append
            # metadata here: the review guard requires the exact direct response.
            session_id = chat_turn(hermes_bin, args.profile, "approve", resume=session_id, project=project, logs_dir=logs_dir, timeout=args.timeout, step="05-explicit-approval")
            session_ids.append(session_id)
            assert_write_boundary(project, baseline)
            validate_final_review(review)

            plan_session_id = run_plan_oneshot(hermes_bin, args.profile, feature_id, project=project, logs_dir=logs_dir, timeout=args.timeout)
            session_ids.append(plan_session_id)
            assert_write_boundary(project, baseline)

            unique_ids = list(dict.fromkeys(session_ids))
            transcript_paths = [
                export_transcript(hermes_bin, args.profile, sid, project=project, logs_dir=logs_dir, timeout=args.timeout, index=index)
                for index, sid in enumerate(unique_ids, start=1)
            ]
            assert_write_boundary(project, baseline)
            plan_index = unique_ids.index(plan_session_id)
            counts = validate_plan(project, feature_id, transcript_paths[plan_index])
            assert_write_boundary(project, baseline)

            result = {
                "status": "passed",
                "run_dir": str(run_dir),
                "project": str(project),
                "profile": args.profile,
                "profile_version": version_text(profile_version),
                "hermes_version": version_text(hermes_version),
                "feature_id": feature_id,
                "approval_actor": AUTOMATED_ACTOR,
                "approval_is_human": False,
                "session_ids": unique_ids,
                "checks": {
                    "exact_session_resume": True,
                    "approval_separate_turn": True,
                    "writes_only_under_specs": True,
                    "application_code_unchanged": True,
                    "full_stack_delegation_proved": True,
                    **counts,
                },
            }
            (logs_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            success = True
            print(json.dumps(result, indent=2))
        except BaseException as exc:
            failure = {
                "status": "failed",
                "error": str(exc),
                "run_dir": str(run_dir),
                "preserved": True,
                "approval_actor": AUTOMATED_ACTOR,
                "approval_is_human": False,
            }
            (logs_dir / "failure.json").write_text(json.dumps(failure, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(failure, indent=2), file=sys.stderr)
            if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                raise
            return 1
        finally:
            if success and args.cleanup_on_success:
                cleanup_target = validate_cleanup_target(run_dir, temp_root)
                shutil.rmtree(cleanup_target)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="staaack", help="Alias du profil Hermes (défaut: staaack)")
    parser.add_argument("--hermes-bin", default="hermes", help="Binaire Hermes ou chemin absolu")
    parser.add_argument("--timeout", type=float, default=900.0, help="Délai maximal par commande en secondes")
    parser.add_argument("--temp-root", help="Racine autorisée pour mktemp (défaut: TMPDIR système)")
    parser.add_argument("--feature-id", help="Feature-id déterministe; défaut basé sur la date locale")
    parser.add_argument("--validate-run", help="Revalider hors LLM un run E2E préservé et marqué")
    parser.add_argument("--plan-transcript", help="Transcript session-*.jsonl exact du plan pour --validate-run")
    parser.add_argument("--cleanup-on-success", action="store_true", help="Supprimer le bac à sable uniquement après succès complet")
    parser.add_argument("--dry-run", action="store_true", help="Afficher les appels sans exécuter Hermes ni créer de bac à sable")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        return execute(build_parser().parse_args(argv))
    except E2EError as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
