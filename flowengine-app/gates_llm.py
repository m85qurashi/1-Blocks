"""
Quality Gates Implementation with Real LLM Review
Extends gates_simple.py with actual Claude API integration for Gate 5
"""
import time
import os
from typing import Tuple, Dict, Any
import anthropic

# Import base gates from simplified version
from gates_simple import (
    QualityGate,
    ContractValidationGate,
    UnitCoverageGate,
    MutationTestingGate,
    SecurityScanGate
)


class LLMReviewGate(QualityGate):
    """Gate 5: Real LLM-powered code review using Claude"""

    def __init__(self):
        super().__init__("LLM Review")
        self.client = None
        self.fallback_to_heuristic = False

    def _init_client(self):
        """Lazy initialization of Anthropic client"""
        if self.client is None:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                print("Warning: ANTHROPIC_API_KEY not set, falling back to heuristic scoring")
                self.fallback_to_heuristic = True
                return

            try:
                # Simple initialization without proxies
                self.client = anthropic.Anthropic(api_key=api_key)
            except Exception as e:
                print(f"Warning: Failed to initialize Anthropic client: {e}")
                print("Falling back to heuristic scoring")
                self.fallback_to_heuristic = True

    def run(self, code: str, context: Dict[str, Any]) -> Tuple[bool, float, Dict[str, Any], float, float]:
        start = time.time()

        # Initialize client if needed
        if self.client is None and not self.fallback_to_heuristic:
            self._init_client()

        # If we should use heuristics (no API key or client init failed)
        if self.fallback_to_heuristic or self.client is None:
            return self._heuristic_review(code, start)

        # Try real LLM review
        try:
            return self._llm_review(code, context, start)
        except Exception as e:
            print(f"LLM review failed: {e}, falling back to heuristic")
            return self._heuristic_review(code, start)

    def _llm_review(self, code: str, context: Dict[str, Any], start: float) -> Tuple[bool, float, Dict[str, Any], float, float]:
        """Perform actual LLM-based code review"""

        prompt = f"""You are a code quality reviewer. Review the following Python code and provide a quality score from 0 to 1.

Code to review:
```python
{code}
```

Evaluate based on:
1. Code structure and organization (30%)
2. Error handling and validation (25%)
3. Code clarity and readability (20%)
4. Performance and efficiency (15%)
5. Best practices adherence (10%)

Respond with ONLY a JSON object in this exact format:
{{"score": 0.85, "reasoning": "Brief explanation of the score"}}

Do not include any other text, markdown formatting, or code blocks. Just the JSON object."""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # Parse response
        response_text = response.content[0].text.strip()

        # Try to extract JSON (handle if Claude wrapped it in markdown)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        import json
        result = json.loads(response_text)

        score = float(result.get("score", 0.5))
        reasoning = result.get("reasoning", "No reasoning provided")

        # Calculate cost (Claude Sonnet 4.5: $3/M input, $15/M output)
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = (input_tokens / 1_000_000 * 3) + (output_tokens / 1_000_000 * 15)

        duration = time.time() - start
        passed = score >= 0.70

        return passed, score, {
            "score": score,
            "reasoning": reasoning,
            "threshold": 0.70,
            "llm_model": "Claude Sonnet 4.5",
            "tokens": {"input": input_tokens, "output": output_tokens},
            "message": f"LLM review score: {score:.2f} - {reasoning}"
        }, duration, cost

    def _heuristic_review(self, code: str, start: float) -> Tuple[bool, float, Dict[str, Any], float, float]:
        """Fallback heuristic scoring (same as stub)"""

        score_components = {
            "code_length": self._score_code_length(code),
            "complexity": self._score_complexity(code),
            "naming": self._score_naming(code),
            "structure": self._score_structure(code),
        }

        weights = {"code_length": 0.2, "complexity": 0.3, "naming": 0.2, "structure": 0.3}
        score = sum(score_components[k] * weights[k] for k in weights)

        passed = score >= 0.70
        duration = time.time() - start

        return passed, score, {
            "score": score,
            "components": score_components,
            "threshold": 0.70,
            "fallback": True,
            "message": f"Heuristic review score: {score:.2f} (fallback - LLM unavailable)"
        }, duration, 0.0

    def _score_code_length(self, code: str) -> float:
        lines = len([l for l in code.split('\n') if l.strip()])
        if 10 <= lines <= 100:
            return 1.0
        elif lines < 10:
            return 0.5
        else:
            return 0.7

    def _score_complexity(self, code: str) -> float:
        decision_points = code.count('if ') + code.count('for ') + code.count('while ') + code.count('elif ')
        if decision_points <= 10:
            return 1.0
        elif decision_points <= 20:
            return 0.7
        else:
            return 0.5

    def _score_naming(self, code: str) -> float:
        has_descriptive_names = any(len(word) > 5 for word in code.split())
        uses_snake_case = '_' in code and not any(c.isupper() for c in code.replace('UPPER', ''))

        score = 0.5
        if has_descriptive_names:
            score += 0.25
        if uses_snake_case or 'def ' in code:
            score += 0.25
        return min(score, 1.0)

    def _score_structure(self, code: str) -> float:
        score = 0.0
        if 'def ' in code:
            score += 0.3
        if 'class ' in code:
            score += 0.2
        if 'return ' in code:
            score += 0.2
        if code.count('\n\n') >= 1:
            score += 0.15
        if '"""' in code or "'''" in code:
            score += 0.15
        return min(score, 1.0)


class QualityGateRunner:
    """Orchestrates running all quality gates with real LLM"""

    def __init__(self):
        self.gates = [
            ContractValidationGate(),
            UnitCoverageGate(),
            MutationTestingGate(),
            SecurityScanGate(),
            LLMReviewGate(),  # 5th gate (real LLM with heuristic fallback)
        ]

    def run_all(self, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run all quality gates in sequence
        Returns comprehensive results
        """
        results = {
            "total_gates": len(self.gates),
            "passed_gates": 0,
            "failed_gates": 0,
            "total_duration": 0.0,
            "total_cost": 0.0,
            "gates": []
        }

        for gate in self.gates:
            passed, score, details, duration, cost = gate.run(code, context)

            gate_result = {
                "name": gate.name,
                "passed": passed,
                "score": score,
                "details": details,
                "duration": duration,
                "cost": cost
            }

            results["gates"].append(gate_result)
            results["total_duration"] += duration
            results["total_cost"] += cost

            if passed:
                results["passed_gates"] += 1
            else:
                results["failed_gates"] += 1

        results["all_passed"] = results["passed_gates"] == results["total_gates"]
        results["success_rate"] = results["passed_gates"] / results["total_gates"]

        return results
