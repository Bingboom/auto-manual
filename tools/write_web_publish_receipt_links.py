#!/usr/bin/env python3
"""Register Document_link.HTML_link after the publish PR merges and deploys.

REV-07 (M2, 方案一): the queue lane no longer writes ``HTML_link`` at build
time — build time proves a candidate exists, not that readers can open it.
This tool is the post-merge receipt lane, run by ``web-publish-receipt.yml``
on the Hello-Docs business plane when a ``main`` push touches
``docs/publish/**``:

1. Read ``docs/publish/publish_manifest.json`` from the merged tree and select
   the targets that carry ``queue_record_ids`` (threaded through assembly from
   the queue run's release metadata). Git-only targets record no queue rows and
   are deliberately out of scope — that path never writes ``HTML_link``.
2. Wait for the Read the Docs deployment of exactly this tree: poll
   ``verify_targets_against_source`` (frozen-source fingerprint, byte
   identity, and the expected RTD project slug) with a fresh ``FetchSession``
   per attempt until every registrable target verifies or the deploy timeout
   expires. A deployment that never verifies is never registered as online.
3. For each verified target, write the canonical nested URL to every recorded
   queue row idempotently: read the current value first (same value -> no
   write), write through the shared upsert path otherwise, then read the same
   record back and require the stored value to match. A failed registration
   leaves the run red for an independent retry (re-run the workflow); it never
   re-publishes the manual.

Rate limiting is undecided, not disproof: a run that ends throttled exits 75
(sysexits EX_TEMPFAIL) so CI can say "re-run", mirroring
``verify_web_deployment_targets.py``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Any

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root


ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools import rtd_deployment_receipt as receipt  # noqa: E402
from tools.document_link_queue import scalar_text  # noqa: E402
from tools.listen_build_queue_lark import fetch_field_id_map  # noqa: E402
from tools.manual_operations_online_health import publication_url  # noqa: E402
from tools.phase2_support import LarkCliSource, cli_bin, load_config, phase2_identity  # noqa: E402
from tools.publish_locale_identity import safe_queue_record_ids  # noqa: E402
from tools.queue_bound_binding import (  # noqa: E402
    collect_queue_preflight_errors,
    resolve_document_link_binding,
)
from tools.queue_bound_lark_ops import run_lark_cli_json  # noqa: E402
from tools.utils.path_utils import PathSegments  # noqa: E402
from tools.verify_web_deployment_targets import (  # noqa: E402
    PUBLISH_MANIFEST,
    expected_project_slug,
    manifest_targets,
    verify_targets_against_source,
)
from tools.write_publish_html_link import resolve_html_link_field_name  # noqa: E402


REPORT_SCHEMA = "auto-manual-web-publish-receipt/v1"
EXIT_OK = 0
EXIT_FAILED = 1
# sysexits EX_TEMPFAIL: the deployment is undecided (rate limited), not wrong.
EXIT_THROTTLED = 75
DEFAULT_RPS = 2.0
DEFAULT_DEPLOY_TIMEOUT_SECONDS = 1800.0
DEFAULT_POLL_INTERVAL_SECONDS = 60.0
# Bitable writes land with seconds of lag; pause before the verify read.
DEFAULT_READBACK_DELAY_SECONDS = 2.0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Write Document_link.HTML_link for queue-built Web targets after the "
            "merged docs/publish tree verifies against the live RTD deployment."
        )
    )
    parser.add_argument("--config", required=True, help="Config YAML path")
    parser.add_argument("--publish-root", type=Path, default=Path("docs/publish"))
    parser.add_argument("--base-url", default=receipt.DEFAULT_RTD_BASE_URL)
    parser.add_argument(
        "--expected-project-slug",
        default=None,
        help="Override the slug derived from --base-url (required for custom domains)",
    )
    parser.add_argument(
        "--record-id",
        action="append",
        default=[],
        help="Optional queue record_id filter for a scoped retry. Repeatable.",
    )
    parser.add_argument("--rps", type=float, default=DEFAULT_RPS)
    parser.add_argument(
        "--retry-budget",
        type=float,
        default=receipt.DEFAULT_RETRY_BUDGET_SECONDS,
        help="Seconds each verification attempt may sleep on rate-limit backoff.",
    )
    parser.add_argument(
        "--deploy-timeout-seconds",
        type=float,
        default=DEFAULT_DEPLOY_TIMEOUT_SECONDS,
        help="Total seconds to wait for the RTD deployment to verify (0 = single attempt).",
    )
    parser.add_argument(
        "--poll-interval-seconds",
        type=float,
        default=DEFAULT_POLL_INTERVAL_SECONDS,
        help="Seconds between verification attempts while waiting for the deployment.",
    )
    parser.add_argument(
        "--asset-scope",
        choices=("markup", "full"),
        default="markup",
        help="Which discovered resources each verification attempt re-downloads.",
    )
    parser.add_argument("--report-json", type=Path, default=None)
    return parser.parse_args(argv)


def resolve_repo_path(value: Path | str) -> Path:
    path = Path(value)
    return (path if path.is_absolute() else ROOT / path).resolve()


def registrable_targets(
    payload: dict[str, Any], *, manifest_path: Path
) -> list[dict[str, Any]]:
    """Manifest targets that recorded queue rows, with validated record ids.

    The manifest is data, not trust: identities, routes and manual names are
    validated by ``manifest_targets``; the record ids re-run the same
    fail-closed validation the assembler applied when it stored them.
    """
    targets = manifest_targets(payload)
    ids_by_identity: dict[tuple[str, str, str], tuple[str, ...]] = {}
    for item in payload.get("targets", []):
        identity = (str(item.get("model")), str(item.get("region")), str(item.get("lang")))
        if identity in ids_by_identity:
            raise ValueError(
                "Publish manifest lists a duplicate target identity: " + "/".join(identity)
            )
        ids_by_identity[identity] = safe_queue_record_ids(item, source=manifest_path)
    selected: list[dict[str, Any]] = []
    for target in targets:
        record_ids = ids_by_identity.get((target["model"], target["region"], target["lang"]), ())
        if record_ids:
            selected.append({**target, "queue_record_ids": record_ids})
    return selected


def filter_targets_by_record_ids(
    targets: list[dict[str, Any]], explicit_record_ids: tuple[str, ...]
) -> list[dict[str, Any]]:
    explicit = {item.strip() for item in explicit_record_ids if item.strip()}
    if not explicit:
        return targets
    selected: list[dict[str, Any]] = []
    for target in targets:
        matched = tuple(
            sorted(explicit.intersection(target["queue_record_ids"]))
        )
        if matched:
            selected.append({**target, "queue_record_ids": matched})
    if not selected:
        raise RuntimeError(
            "No registrable publish target matched the requested queue record ids: "
            + ", ".join(sorted(explicit))
        )
    return selected


def _new_session(args: argparse.Namespace) -> receipt.FetchSession:
    rps = float(args.rps)
    if rps < 0:
        raise ValueError("--rps must not be negative")
    return receipt.FetchSession(
        min_interval=0.0 if rps == 0 else 1.0 / rps,
        retry_budget=float(args.retry_budget),
    )


def wait_for_verified_deployment(
    *,
    web_root: Path,
    base_url: str,
    targets: list[dict[str, Any]],
    project_slug: str,
    args: argparse.Namespace,
    verify_fn: Any = None,
    sleep_fn: Any = time.sleep,
    monotonic_fn: Any = time.monotonic,
) -> tuple[str, list[dict[str, str]], int]:
    """Poll the live site until every registrable target verifies or time runs out.

    Each attempt uses a fresh ``FetchSession``: the session cache is
    run-scoped by design, and a poll loop must observe the *new* deployment,
    not replay the previous attempt's bytes. Returns the final per-target
    results, the overall status (``verified`` / ``failed`` / ``throttled``),
    and the number of attempts made.
    """
    verify = verify_fn or verify_targets_against_source
    include_dependency = None if args.asset_scope == "full" else receipt.markup_dependency
    deadline = monotonic_fn() + max(0.0, float(args.deploy_timeout_seconds))
    attempts = 0
    while True:
        attempts += 1
        results = verify(
            web_root,
            base_url=base_url,
            targets=targets,
            project_slug=project_slug,
            session=_new_session(args),
            include_dependency=include_dependency,
        )
        statuses = {entry["status"] for entry in results}
        if statuses <= {"ok"}:
            return "verified", results, attempts
        if monotonic_fn() >= deadline:
            return ("failed" if "failed" in statuses else "throttled"), results, attempts
        sleep_fn(max(0.0, float(args.poll_interval_seconds)))


def fetch_record_fields(
    *,
    cli_bin: str,
    identity: str,
    base_token: str,
    table_id: str,
    record_id: str,
    run_json: Any = run_lark_cli_json,
) -> dict[str, Any]:
    """Read one Document_link row (positional arrays -> field-name map)."""
    payload = run_json(
        cli_bin=cli_bin,
        args=[
            "base", "+record-get", "--as", identity,
            "--base-token", base_token, "--table-id", table_id,
            "--record-id", record_id, "--format", "json",
        ],
    )
    data = payload.get("data")
    if not isinstance(data, dict):
        raise RuntimeError(f"Lark CLI record-get response is missing data payload: {record_id}")
    names = data.get("fields")
    rows = data.get("data")
    if (
        not isinstance(names, list)
        or not all(isinstance(name, str) for name in names)
        or not isinstance(rows, list)
        or not rows
        or not isinstance(rows[0], list)
    ):
        raise RuntimeError(f"Lark CLI record-get response has an invalid shape: {record_id}")
    row = rows[0]
    return {name: row[index] if index < len(row) else None for index, name in enumerate(names)}


def register_target_links(
    *,
    source: Any,
    binding: Any,
    resolved_cli_bin: str,
    identity: str,
    field_name: str,
    target: dict[str, Any],
    url: str,
    readback_delay_seconds: float = DEFAULT_READBACK_DELAY_SECONDS,
    sleep_fn: Any = time.sleep,
    fetch_fields: Any = None,
) -> list[dict[str, str]]:
    """Idempotent per-row registration: read, compare, write, read back."""
    fetch = fetch_fields or fetch_record_fields
    outcomes: list[dict[str, str]] = []
    for record_id in target["queue_record_ids"]:
        before_fields = fetch(
            cli_bin=resolved_cli_bin,
            identity=identity,
            base_token=binding.base_token,
            table_id=binding.table_id,
            record_id=record_id,
        )
        before = scalar_text(before_fields.get(field_name)).strip()
        if before == url:
            print(f"[web-receipt] SKIP {record_id}: {field_name} already registered ({url})")
            outcomes.append({"record_id": record_id, "action": "already-registered"})
            continue
        source.upsert_record(
            base_token=binding.base_token,
            table_id=binding.table_id,
            record_id=record_id,
            record={field_name: url},
        )
        if readback_delay_seconds > 0:
            sleep_fn(readback_delay_seconds)
        after_fields = fetch(
            cli_bin=resolved_cli_bin,
            identity=identity,
            base_token=binding.base_token,
            table_id=binding.table_id,
            record_id=record_id,
        )
        after = scalar_text(after_fields.get(field_name)).strip()
        if after != url:
            raise RuntimeError(
                f"HTML_link readback mismatch for {record_id}: wrote {url!r}, "
                f"read back {after!r}"
            )
        print(f"[web-receipt] WROTE {record_id}: {field_name}={url} (readback verified)")
        outcomes.append({"record_id": record_id, "action": "written"})
    return outcomes


def run(
    args: argparse.Namespace,
    *,
    verify_fn: Any = None,
    sleep_fn: Any = time.sleep,
    monotonic_fn: Any = time.monotonic,
    fetch_fields: Any = None,
    lark_source_factory: Any = None,
) -> tuple[int, dict[str, Any]]:
    publish_root = resolve_repo_path(args.publish_root)
    manifest_path = publish_root / PUBLISH_MANIFEST
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    base_url = str(args.base_url)
    project_slug = expected_project_slug(base_url, args.expected_project_slug)
    report: dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "base_url": base_url,
        "expected_project_slug": project_slug,
        "targets": [],
    }

    targets = registrable_targets(payload, manifest_path=manifest_path)
    targets = filter_targets_by_record_ids(
        targets,
        tuple(str(item) for item in args.record_id),
    )
    if not targets:
        report["status"] = "no-queue-rows"
        print(
            "[web-receipt] No stored publish target records queue rows; nothing to "
            "register (Git-only targets never write HTML_link)."
        )
        return EXIT_OK, report

    status, results, attempts = wait_for_verified_deployment(
        web_root=publish_root / PathSegments.WEB,
        base_url=base_url,
        targets=targets,
        project_slug=project_slug,
        args=args,
        verify_fn=verify_fn,
        sleep_fn=sleep_fn,
        monotonic_fn=monotonic_fn,
    )
    report["verify_status"] = status
    report["verify_attempts"] = attempts
    verified_targets: list[dict[str, Any]] = []
    for target, result in zip(targets, results):
        entry: dict[str, Any] = {
            "model": target["model"],
            "region": target["region"],
            "lang": target["lang"],
            "page": target["page"],
            "verify": result["status"],
            "records": [],
        }
        if result["status"] == "ok":
            verified_targets.append(target)
        else:
            entry["error"] = result.get("error", "")
            print(
                f"[web-receipt] NOT REGISTERED {target['model']}/{target['region']}/"
                f"{target['lang']}: deployment {result['status']} — "
                f"{result.get('error', 'no detail')}"
            )
        report["targets"].append(entry)

    if verified_targets:
        cfg = load_config(resolve_repo_path(args.config))
        errors = collect_queue_preflight_errors(cfg)
        if errors:
            raise RuntimeError(
                "Web receipt HTML_link writeback preflight failed:\n- " + "\n- ".join(errors)
            )
        binding = resolve_document_link_binding(cfg)
        resolved_cli_bin = cli_bin(cfg)
        identity = phase2_identity()
        source = (
            lark_source_factory(cli_bin=resolved_cli_bin, identity=identity)
            if lark_source_factory
            else LarkCliSource(cli_bin=resolved_cli_bin, identity=identity)
        )
        field_id_map = fetch_field_id_map(
            cli_bin=resolved_cli_bin,
            base_token=binding.base_token,
            table_id=binding.table_id,
            identity=identity,
            run_lark_cli_json=run_lark_cli_json,
        )
        field_name = resolve_html_link_field_name(field_id_map)
        if not field_name:
            raise RuntimeError("Document_link does not expose a writable HTML_link field")
        entries_by_identity = {
            (entry["model"], entry["region"], entry["lang"]): entry
            for entry in report["targets"]
        }
        for target in verified_targets:
            url = publication_url(base_url, target["page"])
            outcomes = register_target_links(
                source=source,
                binding=binding,
                resolved_cli_bin=resolved_cli_bin,
                identity=identity,
                field_name=field_name,
                target=target,
                url=url,
                sleep_fn=sleep_fn,
                fetch_fields=fetch_fields,
            )
            entry = entries_by_identity[(target["model"], target["region"], target["lang"])]
            entry["url"] = url
            entry["records"] = outcomes

    written = sum(
        1
        for entry in report["targets"]
        for outcome in entry["records"]
        if outcome["action"] == "written"
    )
    skipped = sum(
        1
        for entry in report["targets"]
        for outcome in entry["records"]
        if outcome["action"] == "already-registered"
    )
    report["records_written"] = written
    report["records_already_registered"] = skipped
    if status == "verified":
        report["status"] = "registered"
        exit_code = EXIT_OK
    elif status == "throttled":
        report["status"] = "throttled"
        exit_code = EXIT_THROTTLED
    else:
        report["status"] = "failed"
        exit_code = EXIT_FAILED
    print(
        f"[web-receipt] {report['status']}: {written} written, {skipped} already "
        f"registered across {len(targets)} registrable target(s) "
        f"(verify {status} after {attempts} attempt(s))"
    )
    return exit_code, report


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        exit_code, report = run(args)
    except Exception as exc:
        print(f"[web-receipt] ERROR: {exc}", file=sys.stderr)
        return EXIT_FAILED
    if args.report_json is not None:
        report_path = Path(args.report_json)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
