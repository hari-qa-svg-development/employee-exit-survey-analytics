"""Tests for the email-report builder."""

from __future__ import annotations

from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import src.config as cfg
from scripts.build_email import build


def test_build_writes_html_with_cid_figures(tmp_path):
    # Point the builder at a tiny markdown report that references one figure.
    fig = cfg.FIGURES_DIR / "top_resignation_reasons.png"
    md = tmp_path / "report.md"
    md.write_text("# Title\n\nSome text.\n\n![chart](figures/top_resignation_reasons.png)\n")
    out = tmp_path / "email.html"

    result = build(md, out)

    assert result.exists()
    html = result.read_text()
    assert "cid:top_resignation_reasons" in html
    assert "Employee Exit Survey Analytics" in html  # branded template
    assert "figures/top_resignation_reasons.png" not in html  # rewritten


def test_build_raises_when_report_missing():
    import pytest

    with pytest.raises(FileNotFoundError):
        build(Path("/nonexistent/report.md"))
