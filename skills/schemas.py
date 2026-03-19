from __future__ import annotations

from pydantic import BaseModel, Field


class FileSearchInput(BaseModel):
    pattern: str = Field(..., description="Regex pattern to search for.")
    root: str = Field(".", description="Root directory to search from.")
    glob: str = Field("*.py", description="Glob used to filter searched files.")
    limit: int = Field(20, ge=1, le=100, description="Maximum matches to return.")


class FileSearchHit(BaseModel):
    path: str
    line_number: int
    line: str


class FileSearchOutput(BaseModel):
    pattern: str
    root: str
    hits: list[FileSearchHit]
    truncated: bool


class SummarizeInput(BaseModel):
    text: str | None = Field(None, description="Raw text to summarize.")
    path: str | None = Field(None, description="Optional path to a text file.")
    max_points: int = Field(5, ge=1, le=10, description="Maximum bullet points in the summary.")


class SummarizeOutput(BaseModel):
    source: str
    bullets: list[str]


class CodeDiffInput(BaseModel):
    target: str = Field("HEAD", description="Git target or revision to diff against.")
    path: str | None = Field(None, description="Optional file or folder path to scope the diff.")
    max_lines: int = Field(200, ge=20, le=500, description="Maximum number of diff lines to return.")


class CodeDiffOutput(BaseModel):
    target: str
    path: str | None
    return_code: int
    truncated: bool
    diff: str


class UnitTestInput(BaseModel):
    pytest_args: str = Field("-q", description="Arguments passed to pytest.")
    max_lines: int = Field(120, ge=20, le=300, description="Maximum output lines to keep.")


class UnitTestOutput(BaseModel):
    return_code: int
    passed: bool
    output: str
