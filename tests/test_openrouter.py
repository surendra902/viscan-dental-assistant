import os
import pytest
from app.llm import LLMEngine

def test_openrouter_nemotron_initialization(monkeypatch):
    """
    Verifies that OpenRouter provider correctly configures nemotron-3.5-lightning
    and supports both authenticated client mode and resilient offline mode.
    """
    # 1. Test offline/no-key mode (clean checkout default)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    offline_engine = LLMEngine()
    assert offline_engine.openrouter_model == "nvidia/nemotron-3.5-lightning:free"
    assert offline_engine.client is None

    # 2. Test authenticated client initialization
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-mock-test-key-for-provider-test")
    online_engine = LLMEngine()
    assert online_engine.client is not None
    assert online_engine.openrouter_key.startswith("sk-or-v1-")

def test_openrouter_dictation_parsing_fallback_resilience():
    """
    Verifies that dictation parsing safely produces structured findings
    using either OpenRouter or graceful deterministic fallback.
    """
    engine = LLMEngine()
    findings = engine.parse_dictation("Lower right third molar is horizontally impacted")
    assert len(findings) >= 1
    assert "lower right third molar" in findings[0]["anatomical_site"].lower()
    assert "horizontally impacted" in findings[0]["observation"].lower()
