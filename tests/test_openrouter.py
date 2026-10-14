import os
import pytest
from app.llm import LLMEngine

def test_openrouter_nemotron_initialization():
    """
    Verifies that OpenRouter provider correctly initializes with nemotron-3.5-lightning.
    """
    engine = LLMEngine()
    assert engine.openrouter_model == "nvidia/nemotron-3.5-lightning:free"
    assert engine.client is not None
    assert engine.openrouter_key.startswith("sk-or-v1-")

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
