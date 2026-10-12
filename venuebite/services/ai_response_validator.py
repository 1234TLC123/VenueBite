"""Fail closed on malformed/uncited output and unsafe domain conclusions."""

import re

from venuebite.ai import AIError, LIMITATIONS, MAX_RESPONSE_BYTES, STARTERS, COMPARE_STARTERS, EVIDENCE_LABELS, credential_guard

PLACEHOLDER = re.compile(r"\{\{([a-z0-9_.]+)\}\}")
UNSAFE = re.compile(
    r"\b(?:approved|permitted|allowed|legal|compliant|guaranteed|profitable)\b|"
    r"(?:success|approval)\s+(?:chance|probability|likelihood)|"
    r"(?:coverage|evidence).{0,55}(?:confidence|accuracy|probability)|"
    r"(?:verified|market|national|nationwide)\s+(?:rent|affordability)|"
    r"(?:assessed|historical).{0,40}(?:asking|market price)|"
    r"(?:can|may)\s+(?:legally\s+)?(?:open|operate|serve alcohol|build|renovate)|"
    r"(?:permission|permit|license|zoning).{0,40}(?:confirmed|granted|secured|sufficient|cleared)|"
    r"(?:no|without).{0,15}(?:permit|license|review)\s+(?:needed|required)|"
    r"(?:demo|user.supplied|partial).{0,35}\b(?:verified|market fact)\b|"
    r"(?:missing|unknown|unavailable).{0,25}(?:zero|none exist|does not exist)|"
    r"(?:foot traffic|revenue|sales|demand).{0,40}(?:high|low|strong|weak|is|are|will)|"
    r"(?:will|should|certain to)\s+(?:succeed|be successful|make money|turn a profit)|"
    r"(?:excellent|heavy|strong|light)\s+(?:foot |road )?traffic|"
    r"(?:no|few)\s+(?:nearby )?(?:competitors|restaurants)|"
    r"(?:best site|best location|you should choose|definitely open|recalculated score|new score|enough population|sufficient demand)", re.I
)


class AIResponseValidator:
    def __init__(self, sensitive_values=()):
        self.sensitive_values = sensitive_values

    def validate(self, output, context):
        try:
            credential_guard(output, self.sensitive_values)
            if not isinstance(output, dict) or set(output) != {"answer_blocks", "limitations"}:
                raise ValueError
            blocks, limits = output["answer_blocks"], output["limitations"]
            if not isinstance(blocks, list) or not 1 <= len(blocks) <= 5 or not isinstance(limits, list) or len(limits) > 3:
                raise ValueError
            result = []
            for block in blocks:
                if not isinstance(block, dict) or set(block) != {"text", "evidence_ids"}:
                    raise ValueError
                text, ids = block["text"], block["evidence_ids"]
                if not isinstance(text, str) or not text.strip() or len(text) > 1000:
                    raise ValueError
                if not isinstance(ids, list) or not 1 <= len(ids) <= 6 or any(not isinstance(i, str) or i not in context["evidence"] for i in ids) or len(set(ids)) != len(ids):
                    raise ValueError
                stripped = PLACEHOLDER.sub("", text)
                self._safe_prose(stripped)
                if any(identifier not in ids for identifier in PLACEHOLDER.findall(text)) or "{{" in stripped or "}}" in stripped:
                    raise ValueError
                if any(context["evidence"][i]["value"] is None for i in ids) and not re.search(r"unknown|unavailable|not supplied|cannot|missing|not shared|not provided|not verified|withheld", text, re.I):
                    raise ValueError
                text = PLACEHOLDER.sub(lambda m: self._value(context["evidence"][m[1]]), text)
                result.append({"text": text.strip(), "evidence": [context["evidence"][i] for i in ids]})
            for limit in limits:
                if not isinstance(limit, str) or not limit.strip() or len(limit) > 300:
                    raise ValueError
                self._safe_prose(limit)
            if sum(len(b["text"]) for b in result) > MAX_RESPONSE_BYTES:
                raise ValueError
            return {"answer_blocks": result, "limitations": list(LIMITATIONS) + limits,
                    "suggested_questions": list(COMPARE_STARTERS if context["kind"] == "compare" else STARTERS)}
        except (ValueError, TypeError, KeyError, RecursionError):
            raise AIError("unsupported_answer", "The analyst could not ground this answer safely. Try a narrower evidence question.", 502) from None

    @staticmethod
    def _value(item):
        value = " ".join(part for part in (item["display"], item["units"]) if part)
        return f"{value} ({EVIDENCE_LABELS[item['status']]})"

    @staticmethod
    def _safe_prose(text):
        guarded = re.sub(r"\bnot legal advice\b", "requires review", text, flags=re.I)
        guarded = re.sub(r"\bnot (?:independently )?verified\b|\bnot zero\b|\bnot (?:yet )?(?:been )?(?:confirmed|granted|secured|cleared)\b", "unverified", guarded, flags=re.I)
        guarded = re.sub(r"\b(?:not|never|does not mean|isn't)\s+(?:a |an |the )?(?:success |business.success )?(?:probability|confidence|accuracy|approval|market rent|verified rent|legal permission)\b", "unsupported", guarded, flags=re.I)
        if re.search(r"\d|https?://|www\.|[<>]|\]\(", text) or UNSAFE.search(guarded) or any(ord(c) < 32 and c not in "\n\r\t" for c in text):
            raise ValueError
