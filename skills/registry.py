from __future__ import annotations

from autogen_core.tools import FunctionTool

from .tools import code_diff, file_search, run_unit_tests, summarize_text_or_file


def build_skill_tools() -> list[FunctionTool]:
    return [
        FunctionTool(
            file_search,
            name="file_search",
            description="Search files in the repository using a regex pattern and return matching lines.",
        ),
        FunctionTool(
            summarize_text_or_file,
            name="summarize_text_or_file",
            description="Summarize inline text or the contents of a file into a few concise points.",
        ),
        FunctionTool(
            code_diff,
            name="code_diff",
            description="Return the current git diff against a target revision, optionally scoped to a path.",
        ),
        FunctionTool(
            run_unit_tests,
            name="run_unit_tests",
            description="Run the project's test suite with pytest and return the outcome.",
        ),
    ]
