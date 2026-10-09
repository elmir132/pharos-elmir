"""Explanations from a Weights & Biases serverless-inference model, checked against the evidence.

The model may only restate the measured numbers. If its sentence contains any number that is not in the
evidence, or the call fails, a deterministic sentence is used instead. So a flag never carries an invented figure.
"""
from __future__ import annotations

import os
import re

try:  # optional: Weave tracing counts as a Weights & Biases tool
    import weave

    op = weave.op
except Exception:  # pragma: no cover
    def op(fn=None, **_):
        return fn if fn else (lambda f: f)

BASE_URL = "https://api.inference.wandb.ai/v1"
MODEL = os.environ.get("PHAROS_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
NUM = re.compile(r"\d+(?:\.\d+)?")


def template_explanation(ev: dict) -> str:
    e = ev["evidence"]
    a, b = ev["classes"]
    ttc = e.get("ttc_s_at_peak_closing")
    ttc_txt = f", time to collision {ttc} s" if ttc is not None else ""
    return (f"A {a} and a {b} came within {e['min_gap_body_units']} body units of each other at "
            f"{ev['t_closest']:.1f} s (closing at {e['peak_closing_body_units_per_s']} body units per second{ttc_txt}) "
            f"and then moved apart.")


def allowed_numbers(ev: dict) -> set[str]:
    e = ev["evidence"]
    vals = {ev["t_closest"], ev["t_start"], ev["t_end"], ev["severity"], *[v for v in e.values() if isinstance(v, (int, float))]}
    out = set()
    for v in vals:
        for d in (0, 1, 2, 3):
            out.add(f"{float(v):.{d}f}")
        out.add(str(v))
        out.add(str(int(v)) if float(v).is_integer() else str(v))
    return out


def is_grounded(text: str, ev: dict) -> bool:
    ok = allowed_numbers(ev)
    return all(n in ok or n.rstrip("0").rstrip(".") in ok for n in NUM.findall(text))


def _client():
    import openai

    key = os.environ.get("WANDB_API_KEY")
    if not key:
        raise RuntimeError("WANDB_API_KEY not set")
    kwargs = {"base_url": BASE_URL, "api_key": key}
    if os.environ.get("WANDB_PROJECT"):
        kwargs["project"] = os.environ["WANDB_PROJECT"]
    return openai.OpenAI(**kwargs)


@op
def explain(ev: dict, scene: str = "") -> dict:
    """Return {"text": ..., "source": "model" | "template"}."""
    fallback = {"text": template_explanation(ev), "source": "template"}
    try:
        facts = template_explanation(ev)
        prompt = (
            "Write one short, plain sentence describing a possible near miss for a safety reviewer. "
            "Use ONLY the facts below and do not add any number that is not listed.\n"
            f"Facts: {facts}\nScene notes: {scene or 'none'}"
        )
        r = _client().chat.completions.create(
            model=MODEL, temperature=0,
            messages=[{"role": "system", "content": "You write careful, factual safety notes."},
                      {"role": "user", "content": prompt}],
        )
        text = r.choices[0].message.content.strip()
        if text and is_grounded(text, ev):
            return {"text": text, "source": "model"}
        return fallback
    except Exception:
        return fallback
