from __future__ import annotations

import json
import sys
from pathlib import Path

import click

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.orchestrator import Orchestrator, run_async


def _orchestrator() -> Orchestrator:
    return Orchestrator()


@click.group()
def cli() -> None:
    """Lean AI Studio CLI."""


@cli.command()
@click.argument("text", nargs=-1, required=True)
@click.option("--project", "project_name", default="tactics-game", show_default=True)
def request(text: tuple[str, ...], project_name: str) -> None:
    """Create a task from natural language input using the Prompt Specialist."""
    request_text = " ".join(text).strip()
    click.echo(json.dumps(run_async(_orchestrator().intake_request(project_name, request_text)), indent=2))


@cli.group()
def task() -> None:
    """Task creation commands."""


@task.command("create")
@click.option("--project", "project_name", default="tactics-game", show_default=True)
@click.option("--title", required=True)
@click.option("--details", required=True)
@click.option("--priority", default="medium", show_default=True)
@click.option("--requires-approval/--no-requires-approval", default=False, show_default=True)
def create_task(project_name: str, title: str, details: str, priority: str, requires_approval: bool) -> None:
    task_record = _orchestrator().store.create_task(
        project_name,
        title,
        details,
        objective=title,
        priority=priority,
        requires_approval=requires_approval,
        owner_role="Orchestrator",
    )
    click.echo(json.dumps(task_record, indent=2))


@cli.group()
def tasks() -> None:
    """Task listing commands."""


@tasks.command("list")
@click.option("--project", "project_name", default="tactics-game", show_default=True)
@click.option("--state", "status", default=None)
def list_tasks(project_name: str, status: str | None) -> None:
    click.echo(json.dumps(_orchestrator().list_tasks(project_name, status), indent=2))


@cli.command("health-check")
def health_check() -> None:
    click.echo(json.dumps(_orchestrator().health_check(), indent=2))


@cli.command()
@click.option("--project", "project_name", default="tactics-game", show_default=True)
def run(project_name: str) -> None:
    click.echo(json.dumps(run_async(_orchestrator().run_next_task(project_name)), indent=2))


@cli.group()
def approvals() -> None:
    """Approval inspection commands."""


@approvals.command("list")
@click.option("--status", default=None)
def list_approvals(status: str | None) -> None:
    click.echo(json.dumps(_orchestrator().list_approvals(status), indent=2))


@cli.command()
@click.argument("approval_id")
@click.option("--note", default=None)
def approve(approval_id: str, note: str | None) -> None:
    click.echo(json.dumps(_orchestrator().approve(approval_id, note), indent=2))


@cli.command()
@click.argument("approval_id")
@click.option("--note", default=None)
def reject(approval_id: str, note: str | None) -> None:
    click.echo(json.dumps(_orchestrator().reject(approval_id, note), indent=2))


@cli.command()
@click.argument("run_id")
def resume(run_id: str) -> None:
    click.echo(json.dumps(run_async(_orchestrator().resume_run(run_id)), indent=2))


@cli.command("git-checkpoint")
@click.argument("message")
def git_checkpoint(message: str) -> None:
    click.echo(_orchestrator().create_git_checkpoint(message))


if __name__ == "__main__":
    cli()
