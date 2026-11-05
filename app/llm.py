"""OpenAI-compatible chat client that rotates over several free-tier providers/keys.

Env:
  GEMINI_API_KEYS=key1,key2,...     (Google AI Studio keys)
  GEMINI_MODEL=gemini-3.5-flash,gemini-3-flash-preview
  GROQ_API_KEYS=key1,...            (fallback)
  GROQ_MODEL=openai/gpt-oss-120b
  LLM_ORDER=gemini,groq
"""
import asyncio
import itertools
import logging
import os
import time
import uuid

from openai import AsyncOpenAI

log = logging.getLogger("llm")

FAMILIES = {
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "keys_env": "GEMINI_API_KEYS",
        "model_env": "GEMINI_MODEL",
        "default_model": "gemini-3.5-flash,gemini-3-flash-preview",
        "reasoning_env": "GEMINI_REASONING",
        "default_reasoning": "low",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "keys_env": "GROQ_API_KEYS",
        "model_env": "GROQ_MODEL",
        "default_model": "openai/gpt-oss-120b",
        "reasoning_env": "GROQ_REASONING",
        "default_reasoning": "medium",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "keys_env": "OPENROUTER_API_KEYS",
        "model_env": "OPENROUTER_MODEL",
        "default_model": "openai/gpt-oss-120b:free",
        "reasoning_env": "OPENROUTER_REASONING",
        "default_reasoning": "",
    },
}


class Provider:
    def __init__(self, family: str, key: str, idx: int, model: str):
        f = FAMILIES[family]
        self.family = family
        self.name = f"{family}#{idx}:{model}"
        self.model = model
        self.reasoning = os.getenv(f["reasoning_env"], f["default_reasoning"])
        self.client = AsyncOpenAI(api_key=key, base_url=f["base_url"], timeout=45, max_retries=0)
        self.cooldown_until = 0.0

    def available(self) -> bool:
        return time.time() >= self.cooldown_until


def _load() -> dict[str, list[Provider]]:
    out = {}
    for fam, f in FAMILIES.items():
        keys = [k.strip() for k in os.getenv(f["keys_env"], "").replace(";", ",").split(",") if k.strip()]
        models = [m.strip() for m in os.getenv(f["model_env"], f["default_model"]).split(",") if m.strip()]
        # order: model1 x all keys, then model2 x all keys ...
        out[fam] = [Provider(fam, k, i + 1, m) for m in models for i, k in enumerate(keys)]
    return out


_providers: dict[str, list[Provider]] | None = None
_rr: dict[str, itertools.count] = {}


def providers() -> dict[str, list[Provider]]:
    global _providers
    if _providers is None:
        _providers = _load()
        for fam in _providers:
            _rr[fam] = itertools.count()
    return _providers


def configured() -> list[str]:
    return [p.name + " (" + p.model + ")" for ps in providers().values() for p in ps]


def _ordered() -> list[Provider]:
    order = [x.strip() for x in os.getenv("LLM_ORDER", "gemini,groq,openrouter").split(",") if x.strip()]
    res = []
    for fam in order:
        ps = providers().get(fam, [])
        if not ps:
            continue
        rr = os.getenv("LLM_ROUND_ROBIN", "1") != "0"
        start = next(_rr[fam]) % len(ps) if rr else 0  # round-robin start inside a family
        res += ps[start:] + ps[:start]
    return res


def _clean_messages(messages: list[dict], family: str) -> list[dict]:
    """Strip provider-specific extras when a conversation moves to another provider family."""
    out = []
    for m in messages:
        m = dict(m)
        fam = m.pop("_family", None)
        if m.get("role") == "assistant" and fam != family:
            keep = {"role": "assistant", "content": m.get("content") or ""}
            if m.get("tool_calls"):
                keep["tool_calls"] = [
                    {"id": tc["id"], "type": "function",
                     "function": {"name": tc["function"]["name"], "arguments": tc["function"]["arguments"]}}
                    for tc in m["tool_calls"]
                ]
            m = keep
        out.append(m)
    return out


class AllProvidersFailed(RuntimeError):
    pass


async def chat(messages: list[dict], tools: list[dict] | None = None, prefer: str | None = None,
               deadline: float | None = None) -> tuple[dict, Provider]:
    """Returns (assistant_message_dict, provider). Tries providers until one succeeds."""
    cands = [p for p in _ordered() if p.available()] or _ordered()
    if prefer:
        cands.sort(key=lambda p: p.name != prefer)
    if not cands:
        raise AllProvidersFailed("No LLM API keys configured (set GEMINI_API_KEYS and/or GROQ_API_KEYS).")
    errors = []
    for p in cands:
        if deadline and time.time() > deadline - 3:
            break
        kwargs = dict(model=p.model, messages=_clean_messages(messages, p.family), temperature=0)
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        if p.reasoning:
            kwargs["reasoning_effort"] = p.reasoning
        try:
            timeout = 45 if not deadline else max(5, min(45, deadline - time.time() - 2))
            resp = await asyncio.wait_for(p.client.chat.completions.create(**kwargs), timeout=timeout)
            msg = resp.choices[0].message
            d = msg.model_dump(exclude_none=True)
            d["role"] = "assistant"
            d.setdefault("content", "")
            for tc in d.get("tool_calls") or []:
                if not tc.get("id"):
                    tc["id"] = "call_" + uuid.uuid4().hex[:12]
            d["_family"] = p.family
            if not d.get("content") and not d.get("tool_calls"):
                raise RuntimeError("empty response")
            return d, p
        except Exception as e:  # noqa: BLE001
            s = str(e)
            status = getattr(e, "status_code", None)
            log.warning("LLM %s failed (%s): %s", p.name, status, s[:300])
            errors.append(f"{p.name}: {status} {s[:120]}")
            if status == 429 or "quota" in s.lower() or "rate" in s.lower():
                p.cooldown_until = time.time() + 60
            elif status in (401, 403):
                p.cooldown_until = time.time() + 3600
            elif status and status >= 500:
                p.cooldown_until = time.time() + 20
            elif isinstance(e, asyncio.TimeoutError):
                p.cooldown_until = time.time() + 30
    raise AllProvidersFailed("; ".join(errors) or "deadline reached")
