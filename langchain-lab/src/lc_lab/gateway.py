"""Deny-by-default tool gateway for the LC05 security tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class DeniedError(Exception):
    """Typed denial: which tool was refused and why."""

    tool: str
    reason: str

    def __str__(self) -> str:
        return f"denied tool={self.tool} reason={self.reason}"


@dataclass(frozen=True, slots=True)
class AuditRecord:
    """One frozen audit row per gateway decision."""

    identity: str
    tool: str
    verdict: str


def _add(a: int, b: int) -> int:
    return a + b


@dataclass(frozen=True, slots=True)
class ToolGateway:
    """Allowlisted tools, authorized identity, sandboxed reads."""

    allowed_identity: str
    sandbox: Path
    audit: list[AuditRecord] = field(default_factory=list)

    def call(self, identity: str, tool: str, args: dict[str, str | int]) -> str:
        """Execute an allowlisted tool or record a denial and raise."""
        if tool not in ("add", "read"):
            self.audit.append(AuditRecord(identity, tool, "denied:unknown-tool"))
            raise DeniedError(tool, "unknown-tool")
        if identity != self.allowed_identity:
            self.audit.append(AuditRecord(identity, tool, "denied:identity"))
            raise DeniedError(tool, "not allowed")
        if tool == "add":
            return str(_add(int(args["a"]), int(args["b"])))
        return self._read(str(args["path"]))

    def _read(self, rel: str) -> str:
        target = (self.sandbox / rel).resolve()
        if self.sandbox.resolve() not in target.parents:
            self.audit.append(AuditRecord("reader", "read", "denied:path-escape"))
            raise DeniedError("read", "path-escape")
        content = target.read_text(encoding="utf-8")
        self.audit.append(AuditRecord("reader", "read", "allowed"))
        return content


def make_gateway(sandbox: Path) -> ToolGateway:
    """Build a gateway whose only authorized identity is 'reader'."""
    return ToolGateway(allowed_identity="reader", sandbox=sandbox)
