from __future__ import annotations

import json
import re
import time
from typing import Any

import requests


DEFAULT_FALLBACK_MODEL = "openai/gpt-4o-mini"
SYSTEM_PROMPT = (
    "You are an interview summarization assistant. "
    "Return JSON only with keys: summary, recommendation, reason. "
    "All keys are required. Do not wrap in markdown or code fences. "
    "Use this exact schema: {\"summary\": \"- ...\", "
    "\"recommendation\": \"Hire|Borderline|No Hire\", "
    "\"reason\": \"...\"}."
)


def _build_prompt(payload: dict[str, Any]) -> str:
    return (
        "Summarize the interview based on the data below. "
        "Summary must be 5-8 detailed bullet points in a single string. "
        "Include evidence from asked questions, ratings, and notes. "
        "Make the recommendation and reason specific and actionable. "
        "Use only asked questions, scores, and provided notes.\n\n"
        f"Candidate: {payload['candidate_name']}\n"
        f"Role: {payload['role']}\n"
        f"Degree/Year: {payload['degree']} / {payload['year']}\n"
        f"Branch: {payload['branch']}\n"
        f"Skills: {', '.join(payload['skills']) if payload['skills'] else 'N/A'}\n\n"
        "Scores:\n"
        + "\n".join(payload["scores"]) +
        "\n\nAsked Questions (with notes):\n"
        + "\n".join(payload["asked_questions"]) +
        ("\n\nTranscript:\n" + payload["transcript"] if payload.get("transcript") else "")
        + "\n\nReturn JSON only."
    )


def _try_parse_json(text: str) -> dict[str, Any] | None:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json\n", "", 1).strip()
    if cleaned.startswith("\"") and cleaned.endswith("\""):
        try:
            cleaned = json.loads(cleaned)
        except json.JSONDecodeError:
            pass
    if cleaned.startswith('{\\"'):
        cleaned = cleaned.replace("\\\"", "\"").replace("\\n", "\n")
    try:
        loaded = json.loads(cleaned)
        if isinstance(loaded, str) and loaded.strip().startswith("{"):
            try:
                return json.loads(loaded)
            except json.JSONDecodeError:
                return None
        if isinstance(loaded, dict):
            return loaded
        return None
    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError:
            return None
    return None


def _extract_json_field(text: str, field: str) -> str | None:
    pattern = rf'"{re.escape(field)}"\s*:\s*"(?P<value>(?:\\.|[^"\\])*)"'
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        return None
    raw_value = match.group("value")
    try:
        return json.loads(f'"{raw_value}"')
    except json.JSONDecodeError:
        return raw_value


def _extract_labeled_field(text: str, label: str) -> str | None:
    pattern = rf"{re.escape(label)}\s*[:\-]\s*(?P<value>.+)"
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return None
    return match.group("value").strip()


def _extract_field_loose(text: str, field: str, next_fields: list[str]) -> str | None:
    field_pattern = rf'"?{re.escape(field)}"?'
    next_pattern = "|".join(re.escape(name) for name in next_fields)
    pattern = rf"{field_pattern}\s*:\s*(?P<value>.+?)(?=,\s*\"?(?:{next_pattern})\"?\s*:|\s*\}})"
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    raw_value = match.group("value").strip().rstrip(",")
    if raw_value.startswith("\"") and raw_value.endswith("\""):
        raw_value = raw_value[1:-1]
    return raw_value.strip()


def _clean_summary(summary_text: str) -> str:
    cleaned = summary_text.strip()
    if "summary" in cleaned:
        candidate = _extract_json_field(cleaned, "summary")
        if not candidate:
            candidate = _extract_field_loose(
                cleaned,
                "summary",
                ["recommendation", "reason", "recommendation_reason", "justification", "rationale"],
            )
        if candidate:
            return candidate.strip()
    cleaned = re.sub(r'^\s*\{\s*"summary"\s*:\s*"?', "", cleaned)
    cleaned = re.sub(r'"?\s*\}\s*$', "", cleaned)
    cleaned = cleaned.strip().strip('"')
    return cleaned


def generate_llm_summary(
    *,
    payload: dict[str, Any],
    model: str,
    token: str,
    timeout: int = 30,
    base_url: str | None = None,
    extra_headers: dict[str, str] | None = None,
) -> tuple[str | None, str | None, str | None]:
    if not token:
        raise RuntimeError("HF_API_TOKEN is missing")

    prompt = _build_prompt(payload)

    def _call_model(model_id: str, messages: list[dict[str, str]]) -> str:
        last_error = None
        for attempt in range(3):
            headers = {"Authorization": f"Bearer {token}"}
            if extra_headers:
                headers.update(extra_headers)
            response = requests.post(
                base_url or "https://router.huggingface.co/v1/chat/completions",
                headers=headers,
                json={
                    "model": model_id,
                    "messages": messages,
                    "temperature": 0.4,
                    "max_tokens": 400,
                    "response_format": {"type": "json_object"},
                },
                timeout=timeout,
            )

            if response.status_code == 429 and attempt < 2:
                time.sleep(2 ** attempt)
                continue

            if response.status_code >= 400:
                try:
                    error_payload = response.json().get("error")
                    if isinstance(error_payload, dict):
                        code = error_payload.get("code")
                        message = error_payload.get("message", "")
                    else:
                        code = None
                        message = str(error_payload)
                except ValueError:
                    code = None
                    message = response.text
                last_error = RuntimeError(f"HF API error: {response.status_code} {code or ''} {message}")
                break

            data = response.json()
            if isinstance(data, dict) and data.get("error"):
                raise RuntimeError(f"HF API error: {data.get('error')}")

            if isinstance(data, dict) and data.get("choices"):
                return data["choices"][0]["message"].get("content", "")
            return str(data)

        raise last_error or RuntimeError("HF API error: 429 rate limited")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    try:
        text = _call_model(model, messages)
    except RuntimeError as exc:
        message = str(exc)
        if "model_not_supported" in message or "not supported" in message:
            if model != DEFAULT_FALLBACK_MODEL:
                text = _call_model(DEFAULT_FALLBACK_MODEL, messages)
            else:
                raise
        else:
            raise

    parsed = _try_parse_json(text)
    if not parsed:
        fallback_text = text
        if '\\"' in fallback_text:
            fallback_text = fallback_text.replace("\\\"", '"').replace("\\n", "\n")
        summary_fallback = _extract_json_field(fallback_text, "summary")
        recommendation_fallback = _extract_json_field(fallback_text, "recommendation")
        reason_fallback = _extract_json_field(fallback_text, "reason")
        if not summary_fallback:
            summary_fallback = _extract_field_loose(
                fallback_text,
                "summary",
                ["recommendation", "reason", "recommendation_reason", "justification", "rationale"],
            )
        if not recommendation_fallback:
            recommendation_fallback = _extract_field_loose(
                fallback_text,
                "recommendation",
                ["reason", "recommendation_reason", "justification", "rationale"],
            )
        if not reason_fallback:
            reason_fallback = _extract_field_loose(
                fallback_text,
                "reason",
                ["recommendation_reason", "justification", "rationale"],
            )
        if not reason_fallback:
            reason_fallback = (
                _extract_json_field(text, "recommendation_reason")
                or _extract_json_field(text, "justification")
                or _extract_json_field(text, "rationale")
                or _extract_labeled_field(text, "Reason")
                or _extract_labeled_field(text, "Recommendation justification")
            )
        if summary_fallback or recommendation_fallback or reason_fallback:
            return summary_fallback, recommendation_fallback, reason_fallback
        repair_prompt = (
            "Convert the content below to valid JSON with keys summary, recommendation, reason. "
            "Do not add new facts. Return JSON only.\n\n"
            f"Content:\n{text}"
        )
        repair_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": repair_prompt},
        ]
        repaired_text = _call_model(model, repair_messages)
        repaired = _try_parse_json(repaired_text)
        if repaired:
            parsed = repaired
        else:
            return text.strip() or None, None, None

    summary_value = parsed.get("summary")
    recommendation = parsed.get("recommendation") or parsed.get("decision")
    reason = (
        parsed.get("reason")
        or parsed.get("recommendation_reason")
        or parsed.get("justification")
        or parsed.get("rationale")
    )

    if isinstance(summary_value, list):
        summary = "\n".join(f"- {item}" for item in summary_value if str(item).strip())
    else:
        summary = str(summary_value).strip() if summary_value is not None else None

    if summary:
        summary = _clean_summary(summary)

    if isinstance(recommendation, list):
        recommendation = " ".join(str(item) for item in recommendation).strip()
    elif recommendation is not None:
        recommendation = str(recommendation).strip()

    if isinstance(reason, list):
        reason = " ".join(str(item) for item in reason).strip()
    elif reason is not None:
        reason = str(reason).strip()

    return summary or None, recommendation or None, reason or None
