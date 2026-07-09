from __future__ import annotations

from assistant.evaluation.cer_wer import character_error_rate, word_error_rate
from assistant.evaluation.field_accuracy import field_exact_match
from assistant.evaluation.report_card import retrieval_hit_rate, summary_coverage_score
from assistant.tools.base import AssistantTool


class EvaluateOutputTool(AssistantTool):
    name = "tool_evaluate_output"
    description = "Calculate OCR, ASR, field, summary, and retrieval evaluation metrics."
    input_schema = {"prediction": "dict", "reference": "dict optional"}
    output_schema = {"metrics": "dict"}

    def run(self, input_data: dict) -> dict:
        prediction = input_data.get("prediction", {})
        reference = input_data.get("reference", {})
        metrics: dict = {}
        if "text" in prediction or "text" in reference:
            metrics["ocr_character_error_rate"] = character_error_rate(prediction.get("text", ""), reference.get("text", prediction.get("text", "")))
        if "transcript" in prediction or "transcript" in reference:
            metrics["asr_word_error_rate"] = word_error_rate(prediction.get("transcript", ""), reference.get("transcript", prediction.get("transcript", "")))
            metrics["asr_character_error_rate"] = character_error_rate(prediction.get("transcript", ""), reference.get("transcript", prediction.get("transcript", "")))
        if "fields" in prediction or "fields" in reference:
            metrics.update(field_exact_match(prediction.get("fields", {}), reference.get("fields", prediction.get("fields", {}))))
        if prediction.get("summary"):
            metrics["summary_coverage_mock_score"] = summary_coverage_score(prediction.get("summary", ""), prediction.get("source_text", ""))
        if prediction.get("retrieval_results") is not None:
            metrics["retrieval_hit_rate"] = retrieval_hit_rate(prediction.get("retrieval_results", []), reference.get("expected_terms", []))
        return {"metrics": metrics}

