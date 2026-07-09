from assistant.tools.evaluation_tool import EvaluateOutputTool


def test_evaluation_metrics_calculate_correctly():
    output = EvaluateOutputTool().run({
        "prediction": {"fields": {"vendor": "Example"}, "text": "abc"},
        "reference": {"fields": {"vendor": "Example"}, "text": "abc"}
    })
    assert output["metrics"]["field_accuracy"] == 1.0
    assert output["metrics"]["ocr_character_error_rate"] == 0.0

