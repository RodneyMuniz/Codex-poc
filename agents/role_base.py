from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from autogen_core.models import SystemMessage, UserMessage

from agents.config import create_model_client


class StudioRoleAgent:
    def __init__(self, *, role_name: str, model_role: str, repo_root: str | Path, store, telemetry) -> None:
        self.role_name = role_name
        self.model_role = model_role
        self.repo_root = Path(repo_root)
        self.store = store
        self.telemetry = telemetry
        self.model_client = create_model_client(model_role)

    async def close(self) -> None:
        await self.model_client.close()

    async def generate_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        run_id: str | None = None,
        task_id: str | None = None,
        event_type: str = "agent_text",
    ) -> str:
        result = await self.model_client.create(
            [
                SystemMessage(content=system_prompt),
                UserMessage(content=user_prompt, source="user"),
            ]
        )
        content = self._normalize_content(result.content)
        self._record(
            run_id=run_id,
            task_id=task_id,
            event_type=event_type,
            content=content,
            usage=getattr(result, "usage", None),
        )
        return content

    async def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema,
        run_id: str | None = None,
        task_id: str | None = None,
        event_type: str = "agent_json",
    ):
        result = await self.model_client.create(
            [
                SystemMessage(content=system_prompt),
                UserMessage(content=user_prompt, source="user"),
            ],
            json_output=schema,
        )
        raw_content = self._normalize_content(result.content)
        try:
            parsed = schema.model_validate_json(raw_content)
        except Exception:
            parsed = schema.model_validate(json.loads(raw_content))
        self._record(
            run_id=run_id,
            task_id=task_id,
            event_type=event_type,
            content=raw_content,
            usage=getattr(result, "usage", None),
        )
        return parsed

    def _normalize_content(self, content: Any) -> str:
        if isinstance(content, str):
            return content.strip()
        return json.dumps(content, ensure_ascii=True, default=str)

    def _record(self, *, run_id: str | None, task_id: str | None, event_type: str, content: str, usage: Any) -> None:
        prompt_tokens = getattr(usage, "prompt_tokens", None)
        completion_tokens = getattr(usage, "completion_tokens", None)
        payload = {"role": self.role_name, "content": content}
        if run_id and task_id:
            self.store.record_message(
                run_id,
                task_id,
                event_type,
                payload,
                source=self.role_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )
        self.telemetry.append_event(
            event_type,
            {
                "run_id": run_id,
                "task_id": task_id,
                "source": self.role_name,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "payload": payload,
            },
        )
