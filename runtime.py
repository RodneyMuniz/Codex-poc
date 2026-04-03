from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from openai import OpenAI


class RuntimeProviderError(RuntimeError):
    pass


@dataclass
class OpenAIResponsesRuntime:
    client: OpenAI

    def invoke(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        reasoning_effort: str,
        metadata: dict[str, Any] | None = None,
        background: bool = False,
    ) -> Any:
        return self.client.responses.create(
            model=model,
            input=messages,
            reasoning={"effort": reasoning_effort},
            metadata=metadata or {},
            background=background,
            store=True,
        )


class ClaudeRuntime:
    def __init__(self, *args, **kwargs) -> None:
        raise RuntimeProviderError("Claude runtime adapter is not configured in this repository yet.")


def create_runtime(provider: str, **kwargs) -> Any:
    normalized = provider.strip().lower()
    if normalized == "openai":
        client = kwargs.get("client")
        if client is None:
            raise RuntimeProviderError("OpenAI runtime requires an initialized client.")
        return OpenAIResponsesRuntime(client=client)
    if normalized == "claude":
        return ClaudeRuntime(**kwargs)
    raise RuntimeProviderError(f"Unsupported runtime provider: {provider}")
