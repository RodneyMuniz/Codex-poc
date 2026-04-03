from __future__ import annotations

import inspect
import time
from functools import wraps
from typing import Any, Callable

from governance.rules import check_role, load_policies
from memory.memory_store import query_memory, record_metric
from state_machine import normalize_task_state


POLICIES = load_policies()


def _role_name(bound_instance: Any) -> str:
    return getattr(bound_instance, "role_name", bound_instance.__class__.__name__)


def _repo_root(bound_instance: Any):
    return getattr(bound_instance, "repo_root", None)


def pre_task(state: str):
    def decorator(func: Callable):
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_inner(*args, **kwargs):
                bound_instance = args[0] if args else None
                role = _role_name(bound_instance)
                resolved_state = normalize_task_state(state)
                check_role(role, resolved_state, POLICIES)
                if bound_instance is not None:
                    memory_query = " ".join(str(value) for value in kwargs.values() if isinstance(value, str))
                    bound_instance._memory_context = query_memory(memory_query, top_k=3, repo_root=_repo_root(bound_instance))
                return await func(*args, **kwargs)
            return async_inner

        @wraps(func)
        def inner(*args, **kwargs):
            bound_instance = args[0] if args else None
            role = _role_name(bound_instance)
            resolved_state = normalize_task_state(state)
            check_role(role, resolved_state, POLICIES)
            if bound_instance is not None:
                memory_query = " ".join(str(value) for value in kwargs.values() if isinstance(value, str))
                bound_instance._memory_context = query_memory(memory_query, top_k=3, repo_root=_repo_root(bound_instance))
            return func(*args, **kwargs)
        return inner
    return decorator


def post_task(state: str):
    def decorator(func: Callable):
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_inner(*args, **kwargs):
                bound_instance = args[0] if args else None
                role = _role_name(bound_instance)
                started = time.perf_counter()
                success = False
                try:
                    result = await func(*args, **kwargs)
                    success = True
                    return result
                finally:
                    record_metric(
                        role=role,
                        state=normalize_task_state(state),
                        event_type=func.__name__,
                        latency_ms=round((time.perf_counter() - started) * 1000, 3),
                        success=success,
                        token_usage=None,
                        metadata={"hook": "post_task"},
                        repo_root=_repo_root(bound_instance),
                    )
            return async_inner

        @wraps(func)
        def inner(*args, **kwargs):
            bound_instance = args[0] if args else None
            role = _role_name(bound_instance)
            started = time.perf_counter()
            success = False
            try:
                result = func(*args, **kwargs)
                success = True
                return result
            finally:
                record_metric(
                    role=role,
                    state=normalize_task_state(state),
                    event_type=func.__name__,
                    latency_ms=round((time.perf_counter() - started) * 1000, 3),
                    success=success,
                    token_usage=None,
                    metadata={"hook": "post_task"},
                    repo_root=_repo_root(bound_instance),
                )
        return inner
    return decorator
