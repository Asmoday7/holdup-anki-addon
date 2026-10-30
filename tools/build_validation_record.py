"""Record actual CI results and attribute manual release approval to its reporter."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.check_test_report import check


def manual_validation(root: Path, version: str) -> dict | None:
    if "-rc." in version:
        return None
    path = root / "release" / "manual-validation.json"
    if not path.exists():
        raise ValueError("Stable publication requires a recorded manual release approval")
    report = json.loads(path.read_text(encoding="utf-8"))
    if (report.get("release_approval") != version
            or report.get("requested_checks") != "completed"
            or report.get("basis") != "owner_report"
            or not all(report.get(key) for key in
                       ("reporter", "reported_on", "windows_manual", "study_day_boundary"))):
        raise ValueError("Manual release approval is incomplete or belongs to another version")
    return report


def build(reports: Path, destination: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    version = json.loads((root / "holdup" / "manifest.json").read_text(encoding="utf-8"))["human_version"]
    manual = manual_validation(root, version)
    cases = []
    expected = {f"validation-{system}-anki-{anki}" for system in ("ubuntu-24.04", "windows-2025")
                for anki in ("26.9", "26.9.3")}
    actual = {path.name for path in reports.iterdir() if path.is_dir()}
    if actual != expected:
        raise ValueError("Validation requires reports from all four platform/version jobs")
    for name in sorted(expected):
        folder = reports / name
        report, = folder.rglob("ci-results.xml")
        benchmark, = folder.rglob("queue-benchmark.json")
        measurements = json.loads(benchmark.read_text(encoding="utf-8"))
        if measurements.get("holdup") != version or measurements.get("undo_redo") != "passed":
            raise ValueError("Queue benchmark does not match the release")
        expected_platform = "Windows" if name.startswith("validation-windows") else "Linux"
        expected_python = "3.13." if expected_platform == "Windows" else "3.12."
        if (measurements.get("platform") != expected_platform
                or measurements.get("anki_package") != name.split("-anki-")[1]
                or not measurements.get("python", "").startswith(expected_python)):
            raise ValueError("Reported platform/Anki/Python does not match the CI job")
        cases.append({"job": name, "passed": check(str(report)), "packaged_gui_cases": 4,
                      "queue_benchmark": measurements})
    record = {"version": version, "release_type": "candidate" if "-rc." in version else "stable",
              "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
              "recorded_utc": datetime.now(timezone.utc).isoformat(), "automated": cases,
              "windows_11_manual": manual["windows_manual"] if manual else "not yet reported",
              "real_windows_study_day_crossing": manual["study_day_boundary"] if manual else "not yet reported"}
    if manual:
        record["manual_validation"] = manual
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    build(args.reports, args.output)
