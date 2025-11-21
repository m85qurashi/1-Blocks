import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from llm_orchestrator import LLMOrchestrator, LLMResult  # noqa: E402


def _result(model: str, success: bool = True) -> LLMResult:
    return LLMResult(
        model=model,
        code=f"{model} code block",
        duration=0.5,
        cost=0.01,
        tokens={"input": 100, "output": 200},
        error=None if success else "failure",
    )


def test_generate_parallel_prefers_claude(monkeypatch):
    orchestrator = LLMOrchestrator()

    monkeypatch.setattr(orchestrator, "call_claude", lambda *_: _result("Claude Sonnet 4.5"))
    monkeypatch.setattr(orchestrator, "call_gpt4", lambda *_: _result("GPT-4 Turbo"))
    monkeypatch.setattr(orchestrator, "call_gemini", lambda *_: _result("Gemini Pro"))

    payload = orchestrator.generate_parallel("compliance", "policy", "repo-1", {})

    assert payload["success"] is True
    assert payload["primary_model"] == "Claude Sonnet 4.5"
    assert set(payload["successful_models"]) == {"Claude Sonnet 4.5", "GPT-4 Turbo", "Gemini Pro"}
    assert payload["total_cost"] > 0


def test_generate_parallel_falls_back_when_models_fail(monkeypatch):
    orchestrator = LLMOrchestrator()

    monkeypatch.setattr(orchestrator, "call_claude", lambda *_: _result("Claude Sonnet 4.5", success=False))
    monkeypatch.setattr(orchestrator, "call_gpt4", lambda *_: _result("GPT-4 Turbo"))
    monkeypatch.setattr(orchestrator, "call_gemini", lambda *_: _result("Gemini Pro", success=False))

    payload = orchestrator.generate_parallel("security", "scan", "repo-2", {})

    assert payload["success"] is True
    assert payload["primary_model"] == "GPT-4 Turbo"
    assert "Claude Sonnet 4.5" in payload["failed_models"]
    assert payload["total_cost"] > 0


def test_generate_parallel_reports_errors(monkeypatch):
    orchestrator = LLMOrchestrator()

    monkeypatch.setattr(orchestrator, "call_claude", lambda *_: _result("Claude Sonnet 4.5", success=False))
    monkeypatch.setattr(orchestrator, "call_gpt4", lambda *_: _result("GPT-4 Turbo", success=False))
    monkeypatch.setattr(orchestrator, "call_gemini", lambda *_: _result("Gemini Pro", success=False))

    payload = orchestrator.generate_parallel("deploy", "rollout", "repo-3", {})

    assert payload["success"] is False
    assert "All LLM calls failed" in payload["error"]
