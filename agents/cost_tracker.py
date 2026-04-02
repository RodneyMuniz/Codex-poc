from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agents.config import model_pricing
from sessions import SessionStore


@dataclass(frozen=True)
class UsageSnapshot:
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0


@dataclass(frozen=True)
class CostEstimate:
    model: str
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    reasoning_tokens: int
    estimated_cost_usd: float


class CostTracker:
    def __init__(
        self,
        *,
        repo_root: str | Path,
        store: SessionStore | None = None,
        log_path: str | Path | None = None,
    ) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.store = store or SessionStore(self.repo_root)
        self.log_path = Path(log_path) if log_path else self.repo_root / "governance" / "execution_logs.md"

    def normalize_usage(self, usage: Any) -> UsageSnapshot:
        if usage is None:
            return UsageSnapshot()
        if isinstance(usage, dict):
            payload = usage
        else:
            payload = {
                "input_tokens": getattr(usage, "input_tokens", 0),
                "output_tokens": getattr(usage, "output_tokens", 0),
                "input_tokens_details": getattr(usage, "input_tokens_details", None),
                "output_tokens_details": getattr(usage, "output_tokens_details", None),
            }
        input_details = payload.get("input_tokens_details") or {}
        output_details = payload.get("output_tokens_details") or {}
        if not isinstance(input_details, dict):
            input_details = {
                "cached_tokens": getattr(input_details, "cached_tokens", 0),
            }
        if not isinstance(output_details, dict):
            output_details = {
                "reasoning_tokens": getattr(output_details, "reasoning_tokens", 0),
            }
        return UsageSnapshot(
            input_tokens=int(payload.get("input_tokens") or getattr(usage, "input_tokens", 0) or 0),
            cached_input_tokens=int(input_details.get("cached_tokens") or 0),
            output_tokens=int(payload.get("output_tokens") or getattr(usage, "output_tokens", 0) or 0),
            reasoning_tokens=int(output_details.get("reasoning_tokens") or 0),
        )

    def estimate_cost(self, model: str, usage: UsageSnapshot | dict[str, Any] | Any) -> CostEstimate:
        snapshot = usage if isinstance(usage, UsageSnapshot) else self.normalize_usage(usage)
        pricing = model_pricing(model)
        if pricing is None:
            estimated_cost = 0.0
        else:
            uncached_input = max(snapshot.input_tokens - snapshot.cached_input_tokens, 0)
            estimated_cost = (
                (uncached_input / 1_000_000) * pricing.input_per_million
                + (snapshot.cached_input_tokens / 1_000_000) * pricing.cached_input_per_million
                + (snapshot.output_tokens / 1_000_000) * pricing.output_per_million
            )
        return CostEstimate(
            model=model,
            input_tokens=snapshot.input_tokens,
            cached_input_tokens=snapshot.cached_input_tokens,
            output_tokens=snapshot.output_tokens,
            reasoning_tokens=snapshot.reasoning_tokens,
            estimated_cost_usd=round(estimated_cost, 6),
        )

    def record_api_usage(
        self,
        *,
        run_id: str,
        task_id: str,
        source: str,
        model: str,
        tier: str,
        lane: str = "sync_api",
        usage: UsageSnapshot | dict[str, Any] | Any,
        artifact_path: str | None = None,
        notes: str | None = None,
    ) -> CostEstimate:
        estimate = self.estimate_cost(model, usage)
        self.store.record_usage(
            run_id,
            task_id,
            source=source,
            prompt_tokens=estimate.input_tokens,
            completion_tokens=estimate.output_tokens,
            model=model,
            tier=tier,
            lane=lane,
            cached_input_tokens=estimate.cached_input_tokens,
            reasoning_tokens=estimate.reasoning_tokens,
            estimated_cost_usd=estimate.estimated_cost_usd,
        )
        self._append_markdown_log(
            run_id=run_id,
            task_id=task_id,
            source=source,
            model=model,
            tier=tier,
            artifact_path=artifact_path,
            notes=notes,
            estimate=estimate,
        )
        return estimate

    def _append_markdown_log(
        self,
        *,
        run_id: str,
        task_id: str,
        source: str,
        model: str,
        tier: str,
        artifact_path: str | None,
        notes: str | None,
        estimate: CostEstimate,
    ) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            self.log_path.write_text(
                "\n".join(
                    [
                        "# Execution Logs",
                        "",
                        "| Run | Task | Source | Tier | Model | Input | Cached | Output | Estimated USD | Artifact | Notes |",
                        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
        line = (
            f"| {run_id} | {task_id} | {source} | {tier} | {model} | "
            f"{estimate.input_tokens} | {estimate.cached_input_tokens} | {estimate.output_tokens} | "
            f"{estimate.estimated_cost_usd:.6f} | {artifact_path or '-'} | {notes or '-'} |"
        )
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"{line}\n")
