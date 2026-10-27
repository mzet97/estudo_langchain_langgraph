"""P20 tests: pipeline, task isolada e zeros."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from p20_func.api import add, double, pipeline


def test_pipeline_doubles_then_adds():
    # Given: payload com dois números
    # When: entrypoint completo
    result = pipeline.invoke({"n": 3, "m": 4})
    # Then: (3*2) + (4*2)
    assert result == 14


def test_task_runs_standalone():
    # Given: função pura por trás da task (fora de entrypoint)
    # When/Then: lógica isolada funciona sozinha
    assert double.func(5) == 10
    assert add.func(2, 3) == 5


def test_zeros_flow_through():
    # Given: zeros
    # When: pipeline
    result = pipeline.invoke({"n": 0, "m": 0})
    # Then: zero, sem erro
    assert result == 0
