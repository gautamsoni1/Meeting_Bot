"""
Report JSON Schema — defines the structured output for audio → report pipeline.
Every field is typed and documented so the frontend/API consumer knows exactly what to expect.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ─────────────────────────────────────────────
# Sub-models
# ─────────────────────────────────────────────

class SpeakerSegment(BaseModel):
    speaker: str = Field(example="Speaker A")
    start_time: float = Field(description="Start time in seconds", example=0.0)
    end_time: float = Field(description="End time in seconds", example=12.5)
    text: str = Field(example="Good morning, let's start the meeting.")


class ActionItem(BaseModel):
    owner: Optional[str] = Field(default=None, example="John")
    task: str = Field(example="Send the Q3 report to the team by Friday.")
    priority: Optional[str] = Field(default="medium", example="high")


class ReportMeta(BaseModel):
    audio_filename: str = Field(example="meeting_2024.mp3")
    duration_seconds: Optional[float] = Field(default=None, example=1823.5)
    word_count: int = Field(example=1240)
    language: Optional[str] = Field(default="en", example="en")
    generated_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        example="2024-07-15T10:30:00.000000"
    )
    transcript_id: Optional[str] = Field(default=None, example="abc123xyz")


# ─────────────────────────────────────────────
# Main Report Model
# ─────────────────────────────────────────────

class AudioReport(BaseModel):
    """
    Complete structured report produced from an audio file.

    Pipeline:
        Audio → AssemblyAI transcript → Groq summary → AudioReport JSON → DOCX
    """

    meta: ReportMeta

    title: str = Field(
        description="Auto-generated meeting/session title",
        example="Weekly Team Sync – July 15, 2024"
    )

    summary: str = Field(
        description="AI-generated paragraph summary of the meeting",
        example="This meeting discussed Q3 targets, hiring plans, and upcoming product roadmap decisions..."
)

    key_topics: List[str] = Field(
        default_factory=list,
        description="Top topics extracted from the transcript",
        example=["Q3 budget", "Hiring plan", "Product roadmap"]
    )

    action_items: List[ActionItem] = Field(
        default_factory=list,
        description="Actionable tasks identified in the meeting"
    )

    transcript_text: str = Field(
        description="Full raw transcript text from AssemblyAI"
    )

    speakers: Optional[List[SpeakerSegment]] = Field(
        default=None,
        description="Per-speaker segments (only present if speaker diarization enabled)"
    )

    docx_path: Optional[str] = Field(
        default=None,
        description="Server path to the generated .docx file (populated after DOCX step)"
    )

    docx_download_url: Optional[str] = Field(
        default=None,
        description="Public download URL for the .docx report"
    )


# ─────────────────────────────────────────────
# API Response wrappers
# ─────────────────────────────────────────────

class AudioReportResponse(BaseModel):
    """Final API response returned to the client."""
    success: bool = True
    report: AudioReport


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None