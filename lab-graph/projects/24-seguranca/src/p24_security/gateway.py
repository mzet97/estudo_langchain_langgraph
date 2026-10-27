"""P24: gateway de tools deny-by-default com sandbox e auditoria."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Denied(Exception):
    """Negação tipada: ferramenta bloqueada, com motivo auditável."""

    reason: str

    def __str__(self) -> str:
        return f"denied: {self.reason}"


@dataclass
class ToolGateway:
    """Registro estático + allowlist por identidade + trilha de auditoria."""

    sandbox: Path
    tools: dict[str, tuple[Callable, set[str]]] = field(default_factory=dict)
    audit: list[dict] = field(default_factory=list)

    def register(
        self, name: str, fn: Callable, identities: set[str] | list[str]
    ) -> None:
        """Registra tool com o conjunto de identidades autorizadas."""
        self.tools[name] = (fn, set(identities))

    def _log(self, identity: str, tool: str, args: dict, verdict: str) -> None:
        """Audita sem valores de args (só nomes de chaves)."""
        self.audit.append(
            {
                "identity": identity,
                "tool": tool,
                "arg_keys": sorted(args),
                "verdict": verdict,
            }
        )

    def call(self, identity: str, tool: str, args: dict) -> object:
        """Executa se permitido; nega com motivo auditado caso contrário."""
        if tool not in self.tools:
            self._log(identity, tool, args, "denied:unknown-tool")
            raise Denied(f"unknown tool '{tool}'")
        fn, allowed = self.tools[tool]
        if identity not in allowed:
            self._log(identity, tool, args, "denied:identity")
            raise Denied(f"identity '{identity}' not allowed for '{tool}'")
        try:
            result = fn(self, args)
        except Denied as denied:
            self._log(identity, tool, args, f"denied:{denied.reason}")
            raise
        self._log(identity, tool, args, "allowed")
        return result


def make_gateway(sandbox: Path) -> ToolGateway:
    """Gateway com read_file sandboxed registrado para 'reader'."""

    def read_file(gateway: ToolGateway, args: dict) -> str:
        target = (gateway.sandbox / args["path"]).resolve()
        if target != gateway.sandbox.resolve() and (
            gateway.sandbox.resolve() not in target.parents
        ):
            raise Denied("path escapes sandbox")
        return target.read_text(encoding="utf-8")

    gateway = ToolGateway(sandbox=sandbox)
    gateway.register("read_file", read_file, {"reader"})
    return gateway
