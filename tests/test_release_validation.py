"""Stable releases require explicit owner-reported manual approval for that version."""

import json

import pytest

from tools.build_validation_record import manual_validation


def approval():
    return {"release_approval": "1.0.0", "requested_checks": "completed",
            "basis": "owner_report", "reporter": "test owner", "reported_on": "2026-10-30",
            "windows_manual": "completed per owner", "study_day_boundary": "completed per owner"}


def save(root, report):
    (root / "release").mkdir()
    (root / "release" / "manual-validation.json").write_text(json.dumps(report), encoding="utf-8")


@pytest.mark.parametrize("condition", ["missing", "wrong_version", "incomplete"])
def test_stable_release_rejects_missing_or_unfinished_manual_approval(tmp_path, condition):
    if condition != "missing":
        report = approval()
        report["release_approval" if condition == "wrong_version" else "requested_checks"] = (
            "0.9.0" if condition == "wrong_version" else "pending")
        save(tmp_path, report)
    with pytest.raises(ValueError):
        manual_validation(tmp_path, "1.0.0")


def test_stable_release_preserves_the_attributed_owner_report(tmp_path):
    report = approval()
    report["environment_details"] = "Exact versions were not provided."
    save(tmp_path, report)
    assert manual_validation(tmp_path, "1.0.0") == report


def test_candidate_can_be_validated_before_manual_approval(tmp_path):
    assert manual_validation(tmp_path, "1.0.0-rc.1") is None
