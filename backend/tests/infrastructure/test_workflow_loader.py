from __future__ import annotations

from pathlib import Path

import pytest

from src.services.workflow_loader import DEFAULT_FORMAT_PATH, DEFAULT_WORKFLOW_PATH, WorkflowLoader


def test_load_meeting_minutes_workflow_yaml():
    loader = WorkflowLoader(DEFAULT_WORKFLOW_PATH, DEFAULT_FORMAT_PATH)

    workflow = loader.load_workflow()

    assert isinstance(workflow, dict)
    assert "steps" in workflow
    assert isinstance(workflow["steps"], list)


def test_load_company_minutes_format_yaml():
    loader = WorkflowLoader(DEFAULT_WORKFLOW_PATH, DEFAULT_FORMAT_PATH)

    fmt = loader.load_company_format()

    assert isinstance(fmt, dict)
    assert "sections" in fmt


def test_loader_fails_when_path_does_not_exist(tmp_path: Path):
    missing_workflow = tmp_path / "missing_workflow.yaml"
    missing_format = tmp_path / "missing_format.yaml"
    loader = WorkflowLoader(missing_workflow, missing_format)

    with pytest.raises(FileNotFoundError):
        loader.load_workflow()

    with pytest.raises(FileNotFoundError):
        loader.load_company_format()


def test_loader_returns_expected_step_structure():
    loader = WorkflowLoader(DEFAULT_WORKFLOW_PATH, DEFAULT_FORMAT_PATH)

    workflow = loader.load_workflow()

    for step in workflow["steps"]:
        assert "id" in step
