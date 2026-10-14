"""Structured, deterministic clarification detection for ClarifySQL."""

import re


METRIC_OPTIONS = ["Revenue", "Gross profit", "Units sold"]
SALES_METRIC_OPTIONS = ["Revenue", "Units sold"]
SCOPE_OPTIONS = ["Top product only", "Top 5 products"]
TIME_OPTIONS = ["All available time", "This month", "Last month"]
CATEGORY_OPTIONS = ["All categories", "Electronics", "Accessories", "Home Office", "Stationery", "Lifestyle"]


def _normalize(text):
    text = (text or "").lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text)


def _has_metric(text):
    patterns = (
        r"\brevenue\b",
        r"\bsales\b",
        r"\bprofit\b",
        r"\bunits?\b",
        r"\bquantity\b",
        r"\bvolume\b",
    )
    return any(re.search(pattern, text) for pattern in patterns)


def _is_product_ranking(text):
    has_product = bool(re.search(r"\b(products?|items?)\b", text))
    ranking = bool(
        re.search(
            r"\b(top|best|popular|most popular|top selling|best selling|sabse achha|sabse acha|sabse accha|behtareen)\b",
            text,
        )
    )
    return has_product and ranking


def detect_clarification(question, answers=None):
    """Return the next clarification step, or None if no step is needed.

    Answers are selected option labels from earlier clarification steps.
    This function detects ambiguity only; it never executes SQL.
    """
    normalized = _normalize(question)
    answers = [str(answer).strip() for answer in (answers or [])]

    if not normalized:
        return None

    is_ranking = _is_product_ranking(normalized)
    is_top_selling = bool(
        re.search(r"\b(top selling|best selling|top sellers)\b", normalized)
    )

    if not answers:
        if is_ranking and not _has_metric(normalized):
            return {
                "dimension": "metric",
                "step": 1,
                "prompt": "How should the products be ranked?",
                "options": list(
                    SALES_METRIC_OPTIONS if is_top_selling else METRIC_OPTIONS
                ),
            }
        return None

    metric = answers[0].casefold()

    if (
        is_ranking
        and metric in ("revenue", "gross profit", "units sold")
        and len(answers) == 1
    ):
        return {
            "dimension": "result_scope",
            "step": 2,
            "prompt": "Do you want one product or the top 5 products?",
            "options": list(SCOPE_OPTIONS),
        }

    return None

