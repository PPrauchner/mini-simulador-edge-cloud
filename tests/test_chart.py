"""
Tests for the chart module and the --chart CLI flag (optional matplotlib).

Responsibilities:
- Verify --chart renders the Monitor's series to a non-empty PNG.
- Verify the core stays stdlib-only: a run without --chart never imports
  matplotlib.
- Verify that --chart without matplotlib fails with a clear install message.
"""

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

from sim.__main__ import CHART_DIR, _resolve_chart_path
from sim.chart import ChartDependencyError, render_comparison, render_occupancy
from sim.engine import run
from sim.scenarios import make_scenario
from sim.strategies import AllCloud, EdgeFirst, LeastLoaded

REPO_ROOT = Path(__file__).resolve().parent.parent


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Runs `python -m sim` with the given CLI args from the repo root."""
    return subprocess.run(
        [sys.executable, "-m", "sim", *args],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


def test_relative_chart_path_lands_in_the_non_versioned_dir() -> None:
    resolved = _resolve_chart_path("occupancy.png")

    assert resolved == os.path.join(CHART_DIR, "occupancy.png")


def test_absolute_chart_path_is_left_untouched(tmp_path: Path) -> None:
    absolute = str(tmp_path / "occupancy.png")

    assert _resolve_chart_path(absolute) == absolute


def test_render_occupancy_writes_a_nonempty_png(tmp_path: Path) -> None:
    pytest.importorskip("matplotlib")
    monitor = run(make_scenario("minimal"), AllCloud())
    out = tmp_path / "occupancy.png"

    render_occupancy(monitor, str(out))

    assert out.exists()
    assert out.stat().st_size > 0


def test_render_comparison_writes_a_nonempty_png(tmp_path: Path) -> None:
    pytest.importorskip("matplotlib")
    results = [
        (cls.__name__, run(make_scenario("high"), cls()))
        for cls in (AllCloud, EdgeFirst, LeastLoaded)
    ]
    out = tmp_path / "comparison.png"

    render_comparison(results, str(out))

    assert out.exists()
    assert out.stat().st_size > 0


def test_missing_matplotlib_raises_a_clear_dependency_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Blocking the module makes `import matplotlib` raise ImportError even
    # where matplotlib is installed, so this pins the error path everywhere.
    monkeypatch.setitem(sys.modules, "matplotlib", None)
    monitor = run(make_scenario("minimal"), AllCloud())

    with pytest.raises(ChartDependencyError, match="matplotlib"):
        render_occupancy(monitor, str(tmp_path / "unused.png"))


def test_core_run_does_not_import_matplotlib() -> None:
    # Criterion: without --chart nothing imports matplotlib. Asserted from a
    # fresh interpreter so it holds even where matplotlib is installed.
    probe = (
        "import sys; from sim.__main__ import main; "
        "main(['--scenario', 'minimal']); "
        "assert 'matplotlib' not in sys.modules; print('core-ok')"
    )
    result = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 0, result.stderr
    assert "core-ok" in result.stdout


def test_chart_flag_saves_a_png_via_cli(tmp_path: Path) -> None:
    pytest.importorskip("matplotlib")
    out = tmp_path / "chart.png"

    result = run_cli("--scenario", "high", "--chart", str(out))

    assert result.returncode == 0
    assert f"chart saved to {out}" in result.stdout
    assert out.exists()
    assert out.stat().st_size > 0


def test_chart_flag_saves_a_png_in_compare_mode(tmp_path: Path) -> None:
    pytest.importorskip("matplotlib")
    out = tmp_path / "compare.png"

    result = run_cli("--compare", "--chart", str(out))

    assert result.returncode == 0
    assert out.exists()
    assert out.stat().st_size > 0


def test_chart_flag_without_matplotlib_reports_install_message(
    tmp_path: Path,
) -> None:
    if importlib.util.find_spec("matplotlib") is not None:
        pytest.skip("matplotlib is installed; the missing-dependency path is unit-tested")

    result = run_cli("--chart", str(tmp_path / "chart.png"))

    assert result.returncode != 0
    assert "matplotlib" in result.stderr
