"""Evaluate clarification detection against a small labeled dataset."""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.clarification_engine import detect_clarification


def score_cases(cases, use_engine=True):
    tp = fp = tn = fn = 0
    details = []

    for case in cases:
        expected = bool(case["needs_clarification"])

        if use_engine:
            prediction = detect_clarification(case["question"]) is not None
        else:
            # Baseline: never asks a clarification question.
            prediction = False

        if prediction and expected:
            tp += 1
        elif prediction and not expected:
            fp += 1
        elif not prediction and not expected:
            tn += 1
        else:
            fn += 1

        details.append({
            "question": case["question"],
            "expected_clarification": expected,
            "predicted_clarification": prediction,
            "correct": prediction == expected,
        })

    total = len(cases)
    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0.0
    )

    return {
        "total": total,
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "details": details,
    }


def main():
    dataset_path = Path(__file__).with_name("evaluation_cases.json")

    with dataset_path.open("r", encoding="utf-8-sig") as file:
        cases = json.load(file)

    if not isinstance(cases, list) or not cases:
        raise SystemExit("Evaluation dataset must be a non-empty JSON list.")

    for index, case in enumerate(cases, start=1):
        if (
            not isinstance(case, dict)
            or not isinstance(case.get("question"), str)
            or not case["question"].strip()
            or not isinstance(case.get("needs_clarification"), bool)
        ):
            raise SystemExit(f"Invalid dataset record at index {index}.")

    engine = score_cases(cases, use_engine=True)
    baseline = score_cases(cases, use_engine=False)

    print(f"Dataset: {dataset_path}")
    print(f"Cases: {len(cases)}")
    print("\nClarifySQL clarification detector")
    print(f"Accuracy:  {engine['accuracy']:.1%}")
    print(f"Precision: {engine['precision']:.1%}")
    print(f"Recall:    {engine['recall']:.1%}")
    print(f"F1 score:  {engine['f1']:.1%}")
    print(
        "TP={true_positive}, FP={false_positive}, "
        "TN={true_negative}, FN={false_negative}".format(**engine)
    )

    print("\nBaseline (never asks clarification)")
    print(f"Accuracy:  {baseline['accuracy']:.1%}")
    print(f"Precision: {baseline['precision']:.1%}")
    print(f"Recall:    {baseline['recall']:.1%}")
    print(f"F1 score:  {baseline['f1']:.1%}")

    output = {
        "dataset_size": len(cases),
        "clarification_detector": engine,
        "baseline_never_clarifies": baseline,
        "note": (
            "Metrics measure agreement with this small labeled dataset; "
            "they are not a guarantee of real-world performance."
        ),
    }

    output_path = Path(__file__).with_name("evaluation_results.json")
    output_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nDetailed results saved to: {output_path}")


if __name__ == "__main__":
    main()
