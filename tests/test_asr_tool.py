from assistant.tools.asr_tool import TranscribeAudioTool


def test_asr_tool_returns_transcript(tmp_path):
    file_path = tmp_path / "audio.txt"
    file_path.write_text("spoken words", encoding="utf-8")
    output = TranscribeAudioTool().run({"file_path": str(file_path)})
    assert output["transcript"] == "spoken words"
    assert output["adapter"] == "provided_transcript"
