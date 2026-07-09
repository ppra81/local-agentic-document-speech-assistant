from __future__ import annotations

from assistant.tools.asr_tool import TranscribeAudioTool
from assistant.tools.base import ToolRegistry
from assistant.tools.chunking_tool import ChunkDocumentTool
from assistant.tools.evaluation_tool import EvaluateOutputTool
from assistant.tools.ocr_tool import OCRDocumentTool
from assistant.tools.report_tool import GenerateReportTool
from assistant.tools.retrieval_tool import SearchDocumentChunksTool
from assistant.tools.resume_update_tool import UpdateResumeFromInstructionTool
from assistant.tools.summarization_tool import SummarizeDocumentTool
from assistant.tools.translation_tool import TranslateFieldsTool, TranslateTextTool


def build_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    for tool in [
        OCRDocumentTool(),
        TranscribeAudioTool(),
        TranslateTextTool(),
        TranslateFieldsTool(),
        ChunkDocumentTool(),
        SearchDocumentChunksTool(),
        SummarizeDocumentTool(),
        UpdateResumeFromInstructionTool(),
        EvaluateOutputTool(),
        GenerateReportTool(),
    ]:
        registry.register(tool)
    return registry
