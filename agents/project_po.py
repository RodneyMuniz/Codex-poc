from __future__ import annotations

"""
Legacy compatibility module.

The earlier AutoGen-based ProjectPO flow has been superseded by the PM-led workflow in `agents.pm`.
"""

from agents.pm import ProjectManagerAgent

__all__ = ["ProjectManagerAgent"]
