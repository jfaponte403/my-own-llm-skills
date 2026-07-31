from abc import ABC, abstractmethod
from enum import Enum

from pydantic import BaseModel, Field

# ═════════════════════════════════════════════════════════════
# models/analysis/  (see the `models` skill)
# ═════════════════════════════════════════════════════════════


class MimeType(str, Enum):
    PDF = "application/pdf"
    PNG = "image/png"
    JPEG = "image/jpeg"
    PLAIN_TEXT = "text/plain"


class AnalysisProvider(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"
    CLAUDE = "claude"


# Input of the service: a model, never loose kwargs
class FileToAnalyze(BaseModel):
    filename: str = Field(min_length=1)
    mime_type: MimeType
    content: bytes


# Output: the same shape whichever provider produced it
class AnalysisResult(BaseModel):
    filename: str
    provider: AnalysisProvider
    summary: str


# ═════════════════════════════════════════════════════════════
# services/file_analyzer.py
# ═════════════════════════════════════════════════════════════
ANALYSIS_PROMPT = "Summarize the content of this file in a short paragraph."


class AnalysisFailed(Exception):
    pass


# An analyzer declares which types it handles and which provider it uses.
# A new file type is a new class here, never a new branch in the service.
class FileAnalyzer(ABC):
    mime_types: tuple[MimeType, ...]
    provider: AnalysisProvider

    @abstractmethod
    def analyze(self, file: FileToAnalyze) -> str: ...


# ═════════════════════════════════════════════════════════════
# services/analyzers/pdf_analyzer.py  (application/pdf -> OpenAI)
# ═════════════════════════════════════════════════════════════
import base64

from openai import OpenAI


class PdfAnalyzer(FileAnalyzer):
    mime_types = (MimeType.PDF,)
    provider = AnalysisProvider.OPENAI

    # The SDK client is injected: this class never reads an API key.
    def __init__(self, client: OpenAI, model: str) -> None:
        self.client = client
        self.model = model

    def analyze(self, file: FileToAnalyze) -> str:
        encoded = base64.b64encode(file.content).decode()

        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_file",
                            "filename": file.filename,
                            "file_data": f"data:{file.mime_type.value};base64,{encoded}",
                        },
                        {"type": "input_text", "text": ANALYSIS_PROMPT},
                    ],
                }
            ],
        )
        return response.output_text


# ═════════════════════════════════════════════════════════════
# services/analyzers/image_analyzer.py  (image/* -> Gemini)
# ═════════════════════════════════════════════════════════════
from google import genai
from google.genai import types


class ImageAnalyzer(FileAnalyzer):
    mime_types = (MimeType.PNG, MimeType.JPEG)  # one analyzer, several types
    provider = AnalysisProvider.GEMINI

    def __init__(self, client: genai.Client, model: str) -> None:
        self.client = client
        self.model = model

    def analyze(self, file: FileToAnalyze) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                types.Part.from_bytes(data=file.content, mime_type=file.mime_type.value),
                ANALYSIS_PROMPT,
            ],
        )
        return response.text


# ═════════════════════════════════════════════════════════════
# services/analyzers/text_analyzer.py  (text/plain -> Claude)
# ═════════════════════════════════════════════════════════════
from anthropic import Anthropic


class TextAnalyzer(FileAnalyzer):
    mime_types = (MimeType.PLAIN_TEXT,)
    provider = AnalysisProvider.CLAUDE

    def __init__(self, client: Anthropic, model: str = "claude-opus-5") -> None:
        self.client = client
        self.model = model

    def analyze(self, file: FileToAnalyze) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=16000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": ANALYSIS_PROMPT},
                        {"type": "text", "text": file.content.decode()},
                    ],
                }
            ],
        )

        # Safety classifiers can decline: check before reading the content.
        if response.stop_reason == "refusal":
            raise AnalysisFailed(file.filename)

        return next(block.text for block in response.content if block.type == "text")


# ═════════════════════════════════════════════════════════════
# services/file_analyzer_service.py
# ═════════════════════════════════════════════════════════════


class UnsupportedFileType(Exception):
    pass


class FileAnalyzerService:
    def __init__(self, analyzers: list[FileAnalyzer]) -> None:
        # Registry: the only thing that grows when a new type is supported.
        self.analyzers = {
            mime_type: analyzer
            for analyzer in analyzers
            for mime_type in analyzer.mime_types
        }

    def analyze(self, file: FileToAnalyze) -> AnalysisResult:
        analyzer = self.analyzers.get(file.mime_type)
        if analyzer is None:
            raise UnsupportedFileType(file.mime_type.value)

        return AnalysisResult(
            filename=file.filename,
            provider=analyzer.provider,
            summary=analyzer.analyze(file),
        )