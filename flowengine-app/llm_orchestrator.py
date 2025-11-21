"""
Multi-LLM Orchestration
Calls Claude Sonnet 4.5, GPT-4 Turbo, and Gemini Pro in parallel
"""
import os
import time
import asyncio
from typing import Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import anthropic
from openai import OpenAI
import google.generativeai as genai


class LLMResult:
    """Result from a single LLM call"""

    def __init__(self, model: str, code: str, duration: float, cost: float, tokens: Dict[str, int], error: str = None):
        self.model = model
        self.code = code
        self.duration = duration
        self.cost = cost
        self.tokens = tokens
        self.error = error
        self.success = error is None


class LLMOrchestrator:
    """Orchestrates calls to multiple LLM providers"""

    def __init__(self):
        # Initialize clients lazily to avoid constructor issues
        self.anthropic_client = None
        self.openai_client = None
        self.gemini_configured = False

    def call_claude(self, prompt: str, context: Dict[str, Any]) -> LLMResult:
        """Call Claude Sonnet 4.5"""
        start = time.time()

        try:
            # Lazy initialization
            if self.anthropic_client is None:
                self.anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

            response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            code = response.content[0].text
            duration = time.time() - start

            # Calculate cost (Claude Sonnet 4.5: $3/M input, $15/M output)
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = (input_tokens / 1_000_000 * 3) + (output_tokens / 1_000_000 * 15)

            return LLMResult(
                model="Claude Sonnet 4.5",
                code=code,
                duration=duration,
                cost=cost,
                tokens={"input": input_tokens, "output": output_tokens}
            )

        except Exception as e:
            return LLMResult(
                model="Claude Sonnet 4.5",
                code="",
                duration=time.time() - start,
                cost=0.0,
                tokens={},
                error=str(e)
            )

    def call_gpt4(self, prompt: str, context: Dict[str, Any]) -> LLMResult:
        """Call GPT-4 Turbo"""
        start = time.time()

        try:
            # Lazy initialization
            if self.openai_client is None:
                self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                max_tokens=4096,
                temperature=0.7
            )

            code = response.choices[0].message.content
            duration = time.time() - start

            # Calculate cost (GPT-4 Turbo: $10/M input, $30/M output)
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = (input_tokens / 1_000_000 * 10) + (output_tokens / 1_000_000 * 30)

            return LLMResult(
                model="GPT-4 Turbo",
                code=code,
                duration=duration,
                cost=cost,
                tokens={"input": input_tokens, "output": output_tokens}
            )

        except Exception as e:
            return LLMResult(
                model="GPT-4 Turbo",
                code="",
                duration=time.time() - start,
                cost=0.0,
                tokens={},
                error=str(e)
            )

    def call_gemini(self, prompt: str, context: Dict[str, Any]) -> LLMResult:
        """Call Gemini Pro"""
        start = time.time()

        try:
            # Lazy configuration
            if not self.gemini_configured:
                genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
                self.gemini_configured = True

            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)

            code = response.text
            duration = time.time() - start

            # Calculate cost (Gemini Pro: $0.50/M input, $1.50/M output - estimates)
            # Note: Gemini doesn't provide token counts in response
            # Estimate: ~1 token per 4 characters
            input_tokens = len(prompt) // 4
            output_tokens = len(code) // 4
            cost = (input_tokens / 1_000_000 * 0.5) + (output_tokens / 1_000_000 * 1.5)

            return LLMResult(
                model="Gemini Pro",
                code=code,
                duration=duration,
                cost=cost,
                tokens={"input": input_tokens, "output": output_tokens}
            )

        except Exception as e:
            return LLMResult(
                model="Gemini Pro",
                code="",
                duration=time.time() - start,
                cost=0.0,
                tokens={},
                error=str(e)
            )

    def generate_parallel(self, family: str, block_type: str, repo: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call all three LLMs in parallel and synthesize results
        """
        # Construct prompt
        prompt = f"""Generate a high-quality Python code block for:

Family: {family}
Block Type: {block_type}
Repository: {repo}

Requirements:
- Include comprehensive docstrings
- Add type hints
- Include error handling
- Add input validation
- Write production-ready code

Generate only the code, no explanations."""

        # Call LLMs in parallel using ThreadPoolExecutor
        start_total = time.time()
        results = []

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(self.call_claude, prompt, context): "claude",
                executor.submit(self.call_gpt4, prompt, context): "gpt4",
                executor.submit(self.call_gemini, prompt, context): "gemini"
            }

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

        total_duration = time.time() - start_total

        # Choose best result (for MVP: use Claude if available, fallback to others)
        best_result = None
        for result in results:
            if result.success and result.code:
                best_result = result
                if result.model == "Claude Sonnet 4.5":
                    break  # Prefer Claude

        # If all failed, return error
        if not best_result:
            return {
                "success": False,
                "error": "All LLM calls failed",
                "results": [{"model": r.model, "error": r.error} for r in results],
                "duration": total_duration,
                "cost": 0.0
            }

        # Calculate totals
        total_cost = sum(r.cost for r in results if r.success)
        successful_models = [r.model for r in results if r.success]
        failed_models = [r.model for r in results if not r.success]

        return {
            "success": True,
            "code": best_result.code,
            "primary_model": best_result.model,
            "successful_models": successful_models,
            "failed_models": failed_models,
            "total_duration": total_duration,
            "total_cost": total_cost,
            "model_results": [
                {
                    "model": r.model,
                    "success": r.success,
                    "duration": r.duration,
                    "cost": r.cost,
                    "tokens": r.tokens,
                    "error": r.error,
                    "code_length": len(r.code) if r.code else 0
                }
                for r in results
            ]
        }
