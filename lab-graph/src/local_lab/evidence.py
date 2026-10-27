"""Run evidence fingerprint (TEST_STRATEGY.md minimal evidence)."""

from __future__ import annotations

import hashlib
import platform
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class RunEvidence:
    timestamp_utc: str
    project_id: str
    python_version: str
    platform: str
    command: str
    gguf_path_hash: str
    status: str = "NOT_RUN"
    notes: str = ""


def build_evidence(
    project_id: str,
    command: str,
    gguf_path: str,
    status: str = "NOT_RUN",
    notes: str = "",
) -> RunEvidence:
    fingerprint = hashlib.sha256(gguf_path.encode()).hexdigest()[:16]
    return RunEvidence(
        timestamp_utc=datetime.now(UTC).isoformat(),
        project_id=project_id,
        python_version=sys.version.split()[0],
        platform=platform.platform(),
        command=command,
        gguf_path_hash=fingerprint,
        status=status,
        notes=notes,
    )


def evidence_to_dict(evidence: RunEvidence) -> dict:
    return asdict(evidence)
