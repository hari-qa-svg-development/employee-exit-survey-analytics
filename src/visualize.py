"""Generate publication-quality charts from the combined dataset.

Every function writes a PNG into ``reports/figures`` and returns the file path so
the notebook / report can embed them. Charts cover resignation reasons, overall
dissatisfaction, and dissatisfaction broken down by age, tenure and institute.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # headless / reproducible

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

import src.config as cfg
import src.analyze as az

PALETTE = {"DETE": "#2c7fb8", "TAFE": "#d95f0e"}
sns.set_theme(style="whitegrid")
plt.rcParams.update({"figure.dpi": 110, "savefig.bbox": "tight", "font.size": 10})


def _save(fig, path: str) -> str:
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def plot_top_reasons(df: pd.DataFrame, path=None) -> str:
    path = path or str(cfg.FIGURES_DIR / "top_resignation_reasons.png")
    reasons = az.top_resignation_reasons(df, top_n=10).sort_values("count")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(reasons["factor"], reasons["count"], color="#3182bd")
    ax.set_title("Top Contributing Factors Among Resignations")
    ax.set_xlabel("Number of resignations")
    return _save(fig, path)


def plot_dissatisfaction_by_institute(df: pd.DataFrame, path=None) -> str:
    path = path or str(cfg.FIGURES_DIR / "dissatisfaction_by_institute.png")
    data = az.dissatisfaction_by_institute(df)
    fig, ax = plt.subplots(figsize=(6, 4))
    colors = [PALETTE.get(i, "#888") for i in data["institute"]]
    ax.bar(data["institute"], data["dissatisfaction_rate_pct"], color=colors)
    ax.set_ylabel("Dissatisfaction rate (%)")
    ax.set_title("Dissatisfaction Rate by Institute")
    for x, y in zip(data["institute"], data["dissatisfaction_rate_pct"]):
        ax.text(x, y + 1, f"{y:.0f}%", ha="center")
    return _save(fig, path)


def plot_dissatisfaction_by_age(df: pd.DataFrame, path=None) -> str:
    path = path or str(cfg.FIGURES_DIR / "dissatisfaction_by_age.png")
    data = az.dissatisfaction_by_age(df)
    data = data.dropna(subset=["age_group"])
    order = [l for l in cfg.AGE_LABELS if l in data["age_group"].values]
    data["age_group"] = pd.Categorical(data["age_group"], categories=order, ordered=True)
    data = data.sort_values("age_group")
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(data["age_group"].astype(str), data["dissatisfaction_rate_pct"], color="#41ab5d")
    ax.set_ylabel("Dissatisfaction rate (%)")
    ax.set_xlabel("Age group")
    ax.set_title("Dissatisfaction Rate by Age Group")
    return _save(fig, path)


def plot_dissatisfaction_by_tenure(df: pd.DataFrame, path=None) -> str:
    path = path or str(cfg.FIGURES_DIR / "dissatisfaction_by_tenure.png")
    data = az.dissatisfaction_by_tenure(df)
    order = [l for l in cfg.TENURE_LABELS if l in data["tenure_group"].values]
    data["tenure_group"] = pd.Categorical(data["tenure_group"], categories=order, ordered=True)
    data = data.sort_values("tenure_group")
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(data["tenure_group"].astype(str), data["dissatisfaction_rate_pct"], color="#737373")
    ax.set_ylabel("Dissatisfaction rate (%)")
    ax.set_xlabel("Tenure group (years)")
    ax.set_title("Dissatisfaction Rate by Tenure")
    return _save(fig, path)


def plot_institute_comparison(df: pd.DataFrame, path=None) -> str:
    """Grouped bars: resignation rate, dissatisfaction rate, permanent % by institute."""
    path = path or str(cfg.FIGURES_DIR / "institute_comparison.png")
    cmp = az.compare_institutes(df).set_index("institute")
    metrics = {
        "Dissatisfaction %": cmp["dissatisfaction_rate"],
        "Permanent %": cmp["pct_permanent"],
    }
    labels = list(metrics.keys())
    institutes = list(cmp.index)
    x = range(len(labels))
    width = 0.35
    fig, ax = plt.subplots(figsize=(7, 4))
    for i, inst in enumerate(institutes):
        vals = [metrics[m].get(inst, 0) for m in labels]
        ax.bar([xi + (i - 0.5) * width for xi in x], vals, width, label=inst, color=PALETTE.get(inst, "#888"))
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylabel("Percent")
    ax.set_title("DETE vs TAFE: Workforce & Dissatisfaction Profile")
    ax.legend()
    return _save(fig, path)


def generate_all_figures(df: pd.DataFrame, outdir=None) -> list[str]:
    outdir = outdir or cfg.FIGURES_DIR
    outdir = str(outdir)
    import os

    os.makedirs(outdir, exist_ok=True)
    paths = [
        plot_top_reasons(df),
        plot_dissatisfaction_by_institute(df),
        plot_dissatisfaction_by_age(df),
        plot_dissatisfaction_by_tenure(df),
        plot_institute_comparison(df),
    ]
    return paths


if __name__ == "__main__":
    from src.clean import clean_dete, clean_tafe
    from src.combine import combine_datasets
    from src.load import load_dete, load_tafe
    from src.transform import transform_dete, transform_tafe

    dete = transform_dete(clean_dete(load_dete())[0])
    tafe = transform_tafe(clean_tafe(load_tafe())[0])
    combined = combine_datasets(dete, tafe)
    print(generate_all_figures(combined))
