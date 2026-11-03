"""Run the real, separately supplied Advanced Review Bottombar in Anki."""

from importlib.util import find_spec
import os
from pathlib import Path
import subprocess
import sys

import pytest

from tools.package_addon import build_addon


@pytest.mark.anki_gui
@pytest.mark.skipif(find_spec("aqt") is None, reason="Install requirements-gui.txt")
@pytest.mark.parametrize("order", ["before", "after"])
@pytest.mark.parametrize("style", ["default", "hidden", "wide"])
def test_advanced_review_bottombar(tmp_path, order, style):
    source = os.environ.get("HOLDUP_BOTTOMBAR_SOURCE")
    if not source:
        pytest.skip("Set HOLDUP_BOTTOMBAR_SOURCE to the upstream add-on checkout")
    source = Path(source).resolve()
    assert (source / "Bottom_Bar.py").is_file(), source
    archive = build_addon(tmp_path / "holdup.ankiaddon")
    cache, data = tmp_path / "cache", tmp_path / "data"
    cache.mkdir()
    data.mkdir()
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen", QT_OPENGL="software",
               QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu --no-sandbox",
               XDG_CACHE_HOME=str(cache), XDG_DATA_HOME=str(data),
               PYTHONUNBUFFERED="1", PYTHONUTF8="1")
    log = tmp_path / "compatibility.log"
    try:
        with log.open("w", encoding="utf-8") as output:
            result = subprocess.run(
                [sys.executable, "-X", "faulthandler",
                 str(Path(__file__).with_name("bottombar_probe.py")),
                 str(tmp_path / "profile"), str(archive), str(source), order, style],
                env=env, stdout=output, stderr=subprocess.STDOUT,
                timeout=int(os.environ.get("HOLDUP_GUI_TIMEOUT", "180")),
            )
    except subprocess.TimeoutExpired:
        pytest.fail("Bottombar compatibility probe timed out:\n" + log.read_text(encoding="utf-8"))
    output = log.read_text(encoding="utf-8")
    assert result.returncode == 0, output
    assert "PASS compatibility" in output, output
    assert "CLEAN SHUTDOWN" in output, output
    assert "JS error" not in output, output

