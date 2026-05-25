"""Configured workflow execution entrypoints."""

from iceflo_signal.workflows.registry import WorkflowRunResult, run_configured_workflow

__all__ = [
    "WorkflowRunResult",
    "run_configured_workflow",
]
