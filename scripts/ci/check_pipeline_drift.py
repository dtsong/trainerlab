#!/usr/bin/env python3
"""Fail CI when pipeline router/scheduler/docs drift.

Checks:
1) Every scheduler endpoint in Terraform exists in pipeline router endpoints.
2) Scheduler endpoints in Terraform match scheduler table endpoints in docs/SPEC.md.
3) Key pipeline command references are present in docs/SCRIPTS.md.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

PIPELINE_ENDPOINT_RE = re.compile(r"/api/v1/pipeline/[a-z0-9-]+")
ROUTER_POST_RE = re.compile(r'@router\.post\(\s*"(?P<path>/[a-z0-9-]+)"', re.MULTILINE)

KEY_DOC_PIPELINE_REFERENCES = {
    "sync-jp-cards",
    "sync-events",
}


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def get_router_pipeline_endpoints() -> set[str]:
    text = _read("apps/api/src/routers/pipeline.py")
    return {
        f"/api/v1/pipeline{match.group('path')}"
        for match in ROUTER_POST_RE.finditer(text)
    }


def get_terraform_scheduler_endpoints() -> set[str]:
    text = _read("terraform/modules/scheduler/main.tf")
    return set(PIPELINE_ENDPOINT_RE.findall(text))


def get_spec_scheduler_endpoints() -> set[str]:
    text = _read("docs/SPEC.md")
    # Restrict to scheduler table block if present.
    section_start = text.find("Cloud Scheduler jobs:")
    section_end = text.find("\n---\n", section_start) if section_start >= 0 else -1
    scoped = (
        text[section_start:section_end]
        if section_start >= 0 and section_end > section_start
        else text
    )
    return set(PIPELINE_ENDPOINT_RE.findall(scoped))


def check_scripts_key_references() -> list[str]:
    text = _read("docs/SCRIPTS.md")
    missing = [name for name in sorted(KEY_DOC_PIPELINE_REFERENCES) if name not in text]
    if not missing:
        return []
    return ["docs/SCRIPTS.md is missing key pipeline references: " + ", ".join(missing)]


def main() -> int:
    errors: list[str] = []

    router_endpoints = get_router_pipeline_endpoints()
    terraform_endpoints = get_terraform_scheduler_endpoints()
    spec_endpoints = get_spec_scheduler_endpoints()

    missing_in_router = sorted(terraform_endpoints - router_endpoints)
    if missing_in_router:
        errors.append(
            "Terraform scheduler endpoints missing in apps/api/src/routers/pipeline.py: "
            + ", ".join(missing_in_router)
        )

    missing_in_spec = sorted(terraform_endpoints - spec_endpoints)
    extra_in_spec = sorted(spec_endpoints - terraform_endpoints)
    if missing_in_spec:
        errors.append(
            "docs/SPEC.md scheduler table missing Terraform endpoints: "
            + ", ".join(missing_in_spec)
        )
    if extra_in_spec:
        errors.append(
            "docs/SPEC.md scheduler table has endpoints not in Terraform: "
            + ", ".join(extra_in_spec)
        )

    errors.extend(check_scripts_key_references())

    if errors:
        print("Pipeline drift check failed:", file=sys.stderr)
        for err in errors:
            print(f"- {err}", file=sys.stderr)
        return 1

    print("Pipeline drift check passed.")
    print(f"- Router endpoints: {len(router_endpoints)}")
    print(f"- Terraform scheduler endpoints: {len(terraform_endpoints)}")
    print(f"- SPEC scheduler endpoints: {len(spec_endpoints)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
