"""Recreate three CDS 302 movie analysis charts from movies_portfolio.db.

Run from the project directory:
    python3 visualize_movies.py

Dependencies: pandas, numpy, matplotlib (scipy optional for KDE)
Outputs: figures/*.png; existing SQLite databases are never modified.
"""
from pathlib import Path
import sqlite3

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "movies_portfolio.db"
OUTPUT_DIR = ROOT / "figures"


def main():
    if not DB_PATH.is_file():
        raise FileNotFoundError(f"Place movies_portfolio.db next to this script: {DB_PATH}")
    OUTPUT_DIR.mkdir(exist_ok=True)
    # Connect read-only so the source DB is never changed.
    with sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True) as conn:
        movies = pd.read_sql_query(
            'SELECT Movie_ID, Name, Year, Score, Gross, Budget FROM Movies', conn
        )

    # Chart 1: Distribution of movie scores, with an optional KDE curve.
    scores = pd.to_numeric(movies["Score"], errors="coerce").dropna()
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.hist(scores, bins=np.arange(0, 10.51, 0.5), density=True,
            alpha=0.7, edgecolor="white", label="Score distribution")
    try:
        from scipy.stats import gaussian_kde
        xs = np.linspace(float(scores.min()), float(scores.max()), 300)
        ax.plot(xs, gaussian_kde(scores)(xs), linewidth=2, label="KDE")
    except ImportError:
        print("Optional: install scipy to add the KDE curve to chart 1.")
    ax.set(title="Distribution of Movie Scores", xlabel="Movie score", ylabel="Density")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "01_score_distribution.png", dpi=170)
    plt.close(fig)

    # Chart 2: Yearly total gross revenue and average score. These are
    # descriptive totals from the dataset, not inflation-adjusted estimates.
    yearly = movies.dropna(subset=["Year"]).groupby("Year").agg(
        total_gross=("Gross", "sum"), average_score=("Score", "mean")
    ).sort_index()
    fig, ax1 = plt.subplots(figsize=(10, 5.5))
    line1 = ax1.plot(yearly.index, yearly["total_gross"] / 1e9,
                     label="Total gross revenue", linewidth=2)
    ax1.set(xlabel="Release year", ylabel="Total gross revenue (USD billions)")
    ax2 = ax1.twinx()
    line2 = ax2.plot(yearly.index, yearly["average_score"],
                     linestyle="--", label="Average movie score", linewidth=2)
    ax2.set_ylabel("Average movie score")
    ax1.set_title("Total Gross Revenue and Average Movie Score by Year")
    lines = line1 + line2
    ax1.legend(lines, [line.get_label() for line in lines], loc="upper left")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "02_yearly_gross_and_score.png", dpi=170)
    plt.close(fig)

    # Chart 3: Relationship between budget and gross revenue, colored by score.
    data = movies.dropna(subset=["Budget", "Gross", "Score"]).copy()
    data = data[(data["Budget"] > 0) & (data["Gross"] >= 0)]
    fig, ax = plt.subplots(figsize=(9, 6))
    points = ax.scatter(data["Budget"] / 1e6, data["Gross"] / 1e6,
                        c=data["Score"], cmap="viridis", s=12, alpha=0.65)
    ax.set(title="Movie Gross Revenue vs. Production Budget",
           xlabel="Production budget (USD millions)",
           ylabel="Gross revenue (USD millions)")
    fig.colorbar(points, ax=ax, label="Movie score")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "03_budget_vs_gross.png", dpi=170)
    plt.close(fig)

    print(f"Created 3 charts in: {OUTPUT_DIR}")
    print(f"Movies analyzed: {len(movies):,}; with budget/gross/score: {len(data):,}")


if __name__ == "__main__":
    main()
