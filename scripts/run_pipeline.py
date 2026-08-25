"""End-to-end pipeline orchestrator.

Run from the project root:

    python scripts/run_pipeline.py

It executes, in order: load -> clean -> transform -> validate -> combine ->
analyze -> visualize, persisting the cleaned/combined dataset to
``data/processed/combined_exit_survey.csv`` and all figures to
``reports/figures``. A structured run-summary is printed to stdout.

If validation fails the script exits non-zero so the failure is caught in CI /
automation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

import src.analyze as az
import src.config as cfg
import src.validate as vd
from src.clean import clean_dete, clean_tafe
from src.combine import combine_datasets
from src.load import load_dete, load_tafe
from src.transform import transform_dete, transform_tafe
from src.visualize import generate_all_figures


def run() -> dict:
    cfg.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    cfg.FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    print("1/7  Loading raw surveys ...")
    if not cfg.DETE_RAW_PATH.exists() or not cfg.TAFE_RAW_PATH.exists():
        print("    raw surveys missing -> generating with scripts/generate_raw_data.py")
        from scripts.generate_raw_data import main as generate_raw_data

        generate_raw_data()
    raw_dete, raw_tafe = load_dete(), load_tafe()

    print("2/7  Cleaning ...")
    dete_clean, dete_rep = clean_dete(raw_dete)
    tafe_clean, tafe_rep = clean_tafe(raw_tafe)

    print("3/7  Transforming ...")
    dete_tx = transform_dete(dete_clean)
    tafe_tx = transform_tafe(tafe_clean)

    print("4/7  Combining ...")
    combined = combine_datasets(dete_tx, tafe_tx)

    print("5/7  Validating ...")
    report = vd.validate(combined)
    if not report.passed:
        print(report)
        raise SystemExit("Validation failed - aborting.")
    print(report)

    print("6/7  Analyzing ...")
    summary = az.summarize(combined)
    significance = az.significant_patterns(combined).to_dict(orient="records")

    print("7/7  Visualizing ...")
    figures = generate_all_figures(combined)

    print("+     Generating business insights report ...")
    from scripts.generate_report import build as build_report

    report_md = build_report()
    report_path = cfg.REPORTS_DIR / "business_insights.md"
    report_path.write_text(report_md)

    # Persist artifacts
    combined.to_csv(cfg.COMBINED_PATH, index=False)
    run_summary = {
        "cleaning": {"dete": dete_rep, "tafe": tafe_rep},
        "validation_passed": report.passed,
        "summary": summary,
        "significance": significance,
        "figures": figures,
        "report_path": str(report_path),
        "combined_rows": len(combined),
        "combined_path": str(cfg.COMBINED_PATH),
    }
    (cfg.REPORTS_DIR / "run_summary.json").write_text(json.dumps(run_summary, indent=2, default=str))
    print(f"\nWrote combined dataset -> {cfg.COMBINED_PATH}")
    print("Run summary:", json.dumps(summary, indent=2, default=str))
    return run_summary


if __name__ == "__main__":
    run()
