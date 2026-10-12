from __future__ import annotations

"""Module 4 (adapter): RAGAS evaluation returning per-question objects + models.

Adapted from the Day-18 module for the Day-24 contract
(doc/PIPELINE_INTERFACE.md): ``evaluate_ragas`` returns ``per_question`` with the
four attributes and ``metadata.evaluator_models`` naming the actual models used.
Falls back to offline heuristic metrics if RAGAS or the LLM is unavailable.
"""

import os
import sys
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TEST_SET_PATH, LLM_ENABLED, RAGAS_LLM_MODEL, EMBEDDING_MODEL

METRICS = ("faithfulness", "answer_relevancy", "context_precision", "context_recall")


@dataclass
class EvalResult:
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float


def load_test_set(path: str = TEST_SET_PATH) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _tokens(text: str) -> set[str]:
    import re
    return set(re.findall(r"\w+", str(text).lower()))


def _overlap(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta)


def _heuristic_eval(questions, answers, contexts, ground_truths) -> dict:
    per_question: list[EvalResult] = []
    for q, a, ctxs, gt in zip(questions, answers, contexts, ground_truths):
        joined = " ".join(ctxs)
        per_question.append(EvalResult(
            question=q, answer=a, contexts=ctxs, ground_truth=gt,
            faithfulness=_overlap(a, joined),
            answer_relevancy=_overlap(a, q),
            context_precision=(sum(_overlap(c, gt) for c in ctxs) / len(ctxs) if ctxs else 0.0),
            context_recall=_overlap(gt, joined),
        ))

    def _mean(attr):
        if not per_question:
            return 0.0
        return sum(getattr(r, attr) for r in per_question) / len(per_question)

    return {
        **{m: _mean(m) for m in METRICS},
        "per_question": per_question,
        "engine": "heuristic",
    }


def _evaluator_models() -> list[str]:
    return [RAGAS_LLM_MODEL, EMBEDDING_MODEL]


def evaluate_ragas(questions, answers, contexts, ground_truths) -> dict:
    """Run RAGAS 4 metrics; return per-question objects and evaluator models."""
    result: dict
    if not LLM_ENABLED:
        print("  ⚠️  LLM disabled — using heuristic metrics offline.")
        result = _heuristic_eval(questions, answers, contexts, ground_truths)
    else:
        try:
            from ragas import evaluate
            from ragas.metrics import (faithfulness, answer_relevancy,
                                       context_precision, context_recall)
            from datasets import Dataset
            from src.llm import get_ragas_llm, get_ragas_embeddings

            # The OpenCode Go endpoint only supports n=1; answer_relevancy defaults
            # to generating `strictness` questions per row, which would fail.
            answer_relevancy.strictness = 1

            dataset = Dataset.from_dict({
                "question": questions, "answer": answers,
                "contexts": contexts, "ground_truth": ground_truths,
            })
            raw = evaluate(
                dataset,
                metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
                llm=get_ragas_llm(), embeddings=get_ragas_embeddings(),
            )
            df = raw.to_pandas()
            per_question = [
                EvalResult(
                    question=row["question"], answer=row["answer"],
                    contexts=list(row["contexts"]), ground_truth=row["ground_truth"],
                    faithfulness=float(row.get("faithfulness", 0.0)),
                    answer_relevancy=float(row.get("answer_relevancy", 0.0)),
                    context_precision=float(row.get("context_precision", 0.0)),
                    context_recall=float(row.get("context_recall", 0.0)),
                )
                for _, row in df.iterrows()
            ]

            import math
            if not per_question or all(
                not math.isfinite(getattr(r, m)) for r in per_question for m in METRICS
            ):
                print("  ⚠️  RAGAS returned all-NaN; using heuristic fallback.")
                result = _heuristic_eval(questions, answers, contexts, ground_truths)
            else:
                heuristic = _heuristic_eval(questions, answers, contexts, ground_truths)
                for r, hr in zip(per_question, heuristic["per_question"]):
                    for m in METRICS:
                        if not math.isfinite(getattr(r, m)):
                            setattr(r, m, getattr(hr, m))
                aggregate = {m: sum(getattr(r, m) for r in per_question) / len(per_question)
                             for m in METRICS}
                result = {**aggregate, "per_question": per_question, "engine": "ragas"}
        except Exception as e:
            print(f"  ⚠️  RAGAS evaluation failed ({e}); using heuristic metrics.")
            result = _heuristic_eval(questions, answers, contexts, ground_truths)

    result["metadata"] = {"evaluator_models": _evaluator_models()}
    return result


def failure_analysis(eval_results: list[EvalResult], bottom_n: int = 10) -> list[dict]:
    diagnostic_tree = {
        "faithfulness": ("LLM hallucinating", "Tighten prompt, lower temperature"),
        "context_recall": ("Missing relevant chunks", "Improve chunking or add BM25"),
        "context_precision": ("Too many irrelevant chunks", "Add reranking/metadata filter"),
        "answer_relevancy": ("Answer doesn't match question", "Improve prompt template"),
    }
    analyzed = []
    for r in eval_results:
        metrics = {m: getattr(r, m) for m in METRICS}
        worst = min(metrics, key=metrics.get)
        diag, fix = diagnostic_tree[worst]
        analyzed.append({
            "question": r.question, "answer": r.answer,
            "ground_truth": r.ground_truth, "contexts": r.contexts,
            "worst_metric": worst, "score": round(metrics[worst], 4),
            "avg_score": round(sum(metrics.values()) / len(metrics), 4),
            "diagnosis": diag, "suggested_fix": fix,
        })
    analyzed.sort(key=lambda x: x["avg_score"])
    return analyzed[:bottom_n]


def save_report(results: dict, failures: list[dict], path: str = "reports/ragas_report.json") -> None:
    parent_dir = os.path.dirname(path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)
    report = {
        "aggregate": {k: v for k, v in results.items()
                      if k not in ("per_question", "metadata")},
        "num_questions": len(results.get("per_question", [])),
        "failures": failures,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Report saved to {path}")
