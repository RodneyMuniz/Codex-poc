from __future__ import annotations

from pathlib import Path

from hooks import post_task, pre_task
from agents.role_base import StudioRoleAgent
from agents.schemas import DelegationPacket


class PromptSpecialistAgent(StudioRoleAgent):
    def __init__(self, *, repo_root: str | Path, store, telemetry) -> None:
        super().__init__(role_name="PromptSpecialist", model_role="prompt_specialist", repo_root=repo_root, store=store, telemetry=telemetry)

    @pre_task("Spec")
    @post_task("Spec")
    async def process_input(self, user_text: str, *, run_id: str | None = None, task_id: str | None = None) -> DelegationPacket:
        system_prompt = """
You convert free-text studio lead requests into delegation packets.

Return strict JSON with:
- objective
- details
- priority: low, medium, or high
- requires_approval: true or false
- assumptions: array of short inferred assumptions
- risks: array of short risks or ambiguities

Mark requires_approval true for code changes, structural refactors, schema changes, or destructive operations.
Keep objective concise and details practical.
Keep assumptions and risks short and operator-facing.
""".strip()
        try:
            return await self.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_text,
                schema=DelegationPacket,
                run_id=run_id,
                task_id=task_id,
            )
        except Exception:
            if run_id and task_id:
                raise
            if task_id and self._load_task_packet(task_id) is not None:
                raise
            lowered = user_text.lower()
            requires_approval = any(token in lowered for token in ["implement", "refactor", "delete", "migrate", "schema", "code"])
            priority = "high" if "urgent" in lowered or "critical" in lowered else "medium"
            return DelegationPacket(
                objective=user_text.strip().rstrip("."),
                details=user_text.strip(),
                priority=priority,
                requires_approval=requires_approval,
                assumptions=["The request targets the active project unless redirected."],
                risks=["The framework may need operator approval before downstream dispatch."],
            )
