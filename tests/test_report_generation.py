from assistant.tools.report_tool import GenerateReportTool


def test_report_generation_creates_json_and_markdown():
    output = GenerateReportTool().run({"run": {"user_request": "test", "tools_used": [], "final_answer": {}}})
    assert output["json_path"].endswith(".json")
    assert output["markdown_path"].endswith(".md")

