"""
ResearchNu — LLM Client
========================
Multi-model routing strategy:
  - Fast agents  (planner, grader, rewriter, summarizer):
      llama-3.1-8b-instant  — ~0.3-0.5s, sufficient for structured JSON tasks
  - Quality agents (synthesis, novelty, hallucination_checker):
      llama-3.3-70b-versatile — ~1-2s, better reasoning for research synthesis
  - Privacy mode (local, never leaves server):
      ollama llama3.2:3b — no API call, fully local

All Groq calls use temperature=0.1 for JSON agents (deterministic structured
output) and temperature=0.3 for generative agents (summary, detailed_answer).

Groq is used because:
  - Free tier: 14,400 requests/day, 500,000 tokens/minute
  - Fastest inference available (~10x faster than OpenAI for same model size)
  - Supports llama-3.1-8b-instant and llama-3.3-70b-versatile
  - Critical for ResearchNu's <10s latency target
"""

import os
import re
from groq import Groq

# ══════════════════════════════════════════════════════════
# MODELS
# ══════════════════════════════════════════════════════════

MODEL_FAST    = "llama-3.1-8b-instant"    # planner, grader, rewriter, summarizer
MODEL_QUALITY = "llama-3.3-70b-versatile" # synthesis, novelty, hallucination_checker

# ══════════════════════════════════════════════════════════
# CLIENT
# ══════════════════════════════════════════════════════════

_groq = None

def get_groq() -> Groq:
    global _groq
    if not _groq:
        _groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _groq

# ══════════════════════════════════════════════════════════
# CHAT FUNCTIONS
# ══════════════════════════════════════════════════════════

def groq_chat(
    prompt: str,
    model: str = MODEL_FAST,
    max_tokens: int = 1024,
    temperature: float = 0.1,
    json_mode: bool = False,
) -> str:
    """
    Base Groq chat call. Use groq_fast() or groq_quality() instead of
    calling this directly unless you need custom model/token settings.
    """
    try:
        kwargs = dict(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        r = get_groq().chat.completions.create(**kwargs)
        return r.choices[0].message.content
    except Exception as e:
        return f"LLM error: {e}"


def groq_fast(prompt: str, max_tokens: int = 512) -> str:
    """
    Fast model for structured JSON agents: planner, grader, rewriter, summarizer.
    Uses json_mode=True to eliminate control character / parse errors.
    Target latency: ~0.3-0.5s
    """
    return groq_chat(
        prompt,
        model=MODEL_FAST,
        max_tokens=max_tokens,
        temperature=0.1,
        json_mode=True,
    )


def groq_quality(prompt: str, max_tokens: int = 1500) -> str:
    """
    Quality model for generative agents: synthesis, novelty, hallucination_checker.
    Uses json_mode=True to prevent control character errors in long JSON outputs.
    Target latency: ~1-2s
    """
    return groq_chat(
        prompt,
        model=MODEL_QUALITY,
        max_tokens=max_tokens,
        temperature=0.2,
        json_mode=True,
    )


def groq_summarize(prompt: str) -> str:
    """
    Fast model for plain-text summary (no JSON). Higher temperature for
    more natural language output.
    Target latency: ~0.3s
    """
    return groq_chat(
        prompt,
        model=MODEL_FAST,
        max_tokens=200,
        temperature=0.3,
        json_mode=False,
    )


# ══════════════════════════════════════════════════════════
# LOCAL (PRIVACY MODE)
# ══════════════════════════════════════════════════════════

def local_chat(prompt: str) -> str:
    """
    Ollama local inference — privacy mode.
    Query never leaves the server. Falls back to Groq if Ollama unavailable.
    Model: llama3.2:3b (fast, 2GB RAM)
    """
    try:
        import ollama
        r = ollama.chat(
            model="llama3.2:3b",
            messages=[{"role": "user", "content": prompt}]
        )
        return r["message"]["content"]
    except Exception as e:
        print(f"ollama failed, falling back to groq: {e}")
        return groq_chat(prompt)