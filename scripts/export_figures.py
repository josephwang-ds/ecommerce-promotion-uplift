from __future__ import annotations

import os
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "hillstrom_email.csv"
SEGMENT_PATH = PROJECT_ROOT / "data" / "processed" / "segment_uplift.csv"
POLICY_PATH = PROJECT_ROOT / "data" / "processed" / "policy_simulation.csv"
FIGURE_DIR = PROJECT_ROOT / "figures"
os.environ["MPLCONFIGDIR"] = str(PROJECT_ROOT / ".mplconfig")

import matplotlib.pyplot as plt


def setup_plotting() -> None:
    (PROJECT_ROOT / ".mplconfig").mkdir(exist_ok=True)
    FIGURE_DIR.mkdir(exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid")


def export_global_outcomes() -> None:
    df = pd.read_csv(RAW_PATH)
    arm_summary = (
        df.groupby("segment")
        .agg(
            conversion_rate=("conversion", "mean"),
            spend_per_customer=("spend", "mean"),
        )
        .reset_index()
    )

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    colors = ["#94a3b8", "#4f46e5", "#14b8a6"]

    axes[0].bar(arm_summary["segment"], arm_summary["conversion_rate"], color=colors)
    axes[0].set_title("Conversion Rate by Experiment Arm")
    axes[0].set_ylabel("Conversion rate")
    axes[0].tick_params(axis="x", rotation=18)
    axes[0].yaxis.set_major_formatter(lambda x, _: f"{x:.1%}")

    axes[1].bar(arm_summary["segment"], arm_summary["spend_per_customer"], color=colors)
    axes[1].set_title("Spend per Customer by Experiment Arm")
    axes[1].set_ylabel("Spend per customer")
    axes[1].tick_params(axis="x", rotation=18)
    axes[1].yaxis.set_major_formatter(lambda x, _: f"${x:.2f}")

    fig.suptitle("Global Experiment Readout", fontsize=14, fontweight="bold")
    plt.tight_layout()
    fig.savefig(FIGURE_DIR / "global_experiment_readout.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def export_segment_uplift() -> None:
    segment = pd.read_csv(SEGMENT_PATH)
    top_targets = (
        segment[segment["policy"] == "target"]
        .sort_values("incremental_spend_per_100k", ascending=False)
        .head(8)
        .sort_values("incremental_spend_per_100k")
    )
    labels = (
        top_targets["segment_dimension"]
        + " = "
        + top_targets["segment_value"]
        + "\n"
        + top_targets["treatment"]
    )

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.barh(labels, top_targets["incremental_spend_per_100k"], color="#4f46e5")
    ax.set_title("Top Target Segments by Incremental Spend per 100k")
    ax.set_xlabel("Incremental spend per 100k customers")
    ax.xaxis.set_major_formatter(lambda x, _: f"${x / 1000:.0f}k")
    plt.tight_layout()
    fig.savefig(FIGURE_DIR / "top_segment_uplift.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def export_policy_simulation() -> None:
    policy = pd.read_csv(POLICY_PATH).sort_values("cost_adjusted_value_per_100k")

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.barh(policy["policy"], policy["cost_adjusted_value_per_100k"], color="#14b8a6")
    ax.set_title("Cost-adjusted Value per 100k Customers")
    ax.set_xlabel("Expected spend minus contact cost")
    ax.xaxis.set_major_formatter(lambda x, _: f"${x / 1000:.0f}k")
    plt.tight_layout()
    fig.savefig(FIGURE_DIR / "policy_simulation_value.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    setup_plotting()
    export_global_outcomes()
    export_segment_uplift()
    export_policy_simulation()
    print(f"Saved figures to {FIGURE_DIR}")


if __name__ == "__main__":
    main()
