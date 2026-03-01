"""
Phase 3: Mistral API Connectivity Tests
Tests pydantic-ai Agent with Mistral model for structured output.
All operations are timed with [elapsed] output and total summary.

USER TESTING INSTRUCTIONS:
1. Ensure MISTRAL_API_KEY is set in .env
2. Run: uv run pytest src/tests/test_phase3_mistral.py -v -s
3. Verify structured output is returned and response time is < 10s
"""
import time
import pytest
from pydantic import BaseModel, Field
from pydantic_ai import Agent

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.config import settings

# Ensure MISTRAL_API_KEY is available as env var for pydantic-ai provider
os.environ.setdefault("MISTRAL_API_KEY", settings.mistral_api_key)


class TimedStep:
    def __init__(self):
        self.steps: list[tuple[str, float]] = []
        self.total_start = time.time()

    def step(self, label: str):
        return _StepCtx(self, label)

    def summary(self):
        total = time.time() - self.total_start
        print(f"\n{'='*60}")
        print(f"TOTAL ELAPSED: [{total:.3f}s]")
        for label, elapsed in self.steps:
            print(f"  [{elapsed:.3f}s] {label}")
        print(f"{'='*60}")


class _StepCtx:
    def __init__(self, timer: TimedStep, label: str):
        self.timer = timer
        self.label = label

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        elapsed = time.time() - self.start
        self.timer.steps.append((self.label, elapsed))
        print(f"[{elapsed:.3f}s] {self.label}")


@pytest.fixture
def timer():
    return TimedStep()


# Simple model for structured output (prefix _ to avoid pytest collection)
class _IncidentClassification(BaseModel):
    category: str = Field(description="Category: emergency | non_emergency")
    severity: str = Field(description="low | medium | high")
    reasoning: str = Field(description="Brief explanation")


class TestMistralConnectivity:
    @pytest.mark.asyncio
    async def test_structured_output_via_pydantic_ai(self, timer):
        """Test that pydantic-ai can call Mistral and return a validated structured output."""
        test_agent = Agent(
            "mistral:mistral-large-latest",
            output_type=_IncidentClassification,
            system_prompt="Classify the following incident report. Return structured output.",
        )

        with timer.step("pydantic-ai Agent.run() with Mistral"):
            result = await test_agent.run(
                "A car crashed into a building on Market Street. Two people are injured.",
            )

        with timer.step("Validate structured output"):
            output = result.output
            assert isinstance(output, _IncidentClassification)
            assert output.category in ("emergency", "non_emergency")
            assert output.severity in ("low", "medium", "high")
            assert len(output.reasoning) > 0
            print(f"  Category: {output.category}")
            print(f"  Severity: {output.severity}")
            print(f"  Reasoning: {output.reasoning}")

        # Verify timing
        total_time = sum(e for _, e in timer.steps)
        assert total_time < 10.0, f"Mistral response took {total_time:.1f}s, expected < 10s"

        timer.summary()

    def test_native_mistral_client(self, timer):
        """Test native mistralai client connectivity (used for vision calls)."""
        from mistralai import Mistral

        client = Mistral(api_key=settings.mistral_api_key)

        with timer.step("Native Mistral client chat.complete()"):
            response = client.chat.complete(
                model=settings.mistral_vision_model,
                messages=[{
                    "role": "user",
                    "content": "Say 'connected' if you can read this.",
                }],
            )

        with timer.step("Validate native client response"):
            content = response.choices[0].message.content
            assert len(content) > 0
            print(f"  Response: {content}")

        timer.summary()
