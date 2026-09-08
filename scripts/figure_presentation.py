"""Draw the README figure from published results, without rerunning the study.

Run from the repository with ``uv run python scripts/figure_presentation.py``.
The input tables remain the numerical source of truth.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[1]
BLUE, ORANGE, GREEN, GREY = "#176B96", "#C56628", "#14816D", "#718096"
plt.rcParams.update(
    {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.titlesize": 15,
        "axes.labelsize": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": "#CBD5E0",
        "text.color": "#172B3A",
        "axes.labelcolor": "#172B3A",
        "xtick.color": "#425466",
        "ytick.color": "#425466",
        "axes.axisbelow": True,
    }
)


def number(value, decimals=2):
    return f"{value:,.{decimals}f}".replace(",", " ").replace(".", ",")


def finish(fig, axes, title, note, path="results/figures/presentation.png"):
    for ax in np.asarray(axes, dtype=object).ravel():
        ax.grid(axis="x", color="#EDF0F3", linewidth=0.8)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:g}".replace(".", ",")))
    fig.suptitle(title, x=0.02, ha="left", fontweight="bold", fontsize=16)
    fig.text(0.02, 0.015, note, ha="left", va="bottom", fontsize=9, color="#526575")
    fig.tight_layout(rect=(0, 0.075, 1, 0.91))
    destination = ROOT / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main():
    d = pd.read_csv(ROOT / "results/tables/decomposition.csv")
    row = d[(d.fonds == 100) & (d.garantie == 100) & (d.annees == 10) & (d.volatilite == 0.18)].set_index(
        "base"
    )
    fig, ax = plt.subplots(figsize=(10, 4.8))
    for offset, key, color, label in [
        (-0.23, "actions_seules", BLUE, "Actions seules"),
        (0, "volatilite_seule", ORANGE, "Volatilité seule"),
        (0.23, "conjointe", GREEN, "Deux chocs ensemble"),
    ]:
        values = row.loc[["terme", "comptant"], key].to_numpy()
        ax.barh(np.arange(2) + offset, values, height=0.2, color=color, label=label)
        for y, v in zip(np.arange(2) + offset, values, strict=True):
            ax.text(v + 0.2, y, number(v), va="center", fontsize=10)
    ax.set_yticks([0, 1], ["Grille à terme, appendice 7-A", "Grille au comptant, appendice 7-B"])
    ax.invert_yaxis()
    ax.set_xlim(0, 16)
    ax.set_xlabel("Capital par tranche de 100 dollars de fonds")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.34), ncol=3, frameon=False, fontsize=9)
    finish(
        fig,
        [ax],
        "Le choc dominant change selon la grille de volatilité",
        "Garantie de 100 dollars · fonds de 100 dollars · dix ans · volatilité de départ de 18 % par an\n"
        "Régime 2025, grilles relevées le 30 août 2026. Le "
        "capital conjoint n'est pas la somme des deux chocs isolés.",
    )


if __name__ == "__main__":
    main()
