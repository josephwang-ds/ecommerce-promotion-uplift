from __future__ import annotations

from math import sqrt
from pathlib import Path

import pandas as pd
from scipy import stats


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "hillstrom_email.csv"
REPORT_PATH = PROJECT_ROOT / "reports" / "initial_readout.md"


def load_data() -> pd.DataFrame:
    if not RAW_PATH.exists():
        raise FileNotFoundError(
            f"Missing raw data at {RAW_PATH}. Run `python src/download_data.py` first."
        )
    return pd.read_csv(RAW_PATH)


def two_prop_test(control: pd.Series, treatment: pd.Series) -> dict[str, float]:
    n_c = control.shape[0]
    n_t = treatment.shape[0]
    x_c = control.sum()
    x_t = treatment.sum()
    p_c = x_c / n_c
    p_t = x_t / n_t
    pooled = (x_c + x_t) / (n_c + n_t)
    se = sqrt(pooled * (1 - pooled) * (1 / n_c + 1 / n_t))
    z = (p_t - p_c) / se if se else 0.0
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    se_unpooled = sqrt(p_c * (1 - p_c) / n_c + p_t * (1 - p_t) / n_t)
    diff = p_t - p_c
    return {
        "control_rate": p_c,
        "treatment_rate": p_t,
        "abs_lift": diff,
        "rel_lift": diff / p_c if p_c else float("nan"),
        "ci_low": diff - 1.96 * se_unpooled,
        "ci_high": diff + 1.96 * se_unpooled,
        "p_value": p_value,
    }


def mean_diff_test(control: pd.Series, treatment: pd.Series) -> dict[str, float]:
    c = control.fillna(0)
    t = treatment.fillna(0)
    stat, p_value = stats.ttest_ind(t, c, equal_var=False)
    diff = t.mean() - c.mean()
    se = sqrt(c.var(ddof=1) / c.shape[0] + t.var(ddof=1) / t.shape[0])
    return {
        "control_mean": c.mean(),
        "treatment_mean": t.mean(),
        "abs_lift": diff,
        "rel_lift": diff / c.mean() if c.mean() else float("nan"),
        "ci_low": diff - 1.96 * se,
        "ci_high": diff + 1.96 * se,
        "p_value": p_value,
        "t_stat": stat,
    }


def format_pct(value: float) -> str:
    return f"{value:.2%}"


def format_money(value: float) -> str:
    return f"${value:,.3f}"


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def build_report(df: pd.DataFrame) -> str:
    control = df[df["segment"] == "No E-Mail"]
    treatments = ["Mens E-Mail", "Womens E-Mail"]
    sample_rows = [
        [segment, f"{users:,}"]
        for segment, users in df["segment"].value_counts().sort_index().items()
    ]
    outcome_summary = (
        df.groupby("segment")[["visit", "conversion", "spend"]].mean().reset_index()
    )
    outcome_rows = [
        [
            row["segment"],
            format_pct(row["visit"]),
            format_pct(row["conversion"]),
            format_money(row["spend"]),
        ]
        for _, row in outcome_summary.iterrows()
    ]

    lines: list[str] = [
        "# Initial Hillstrom Experiment Readout",
        "",
        "## Dataset Snapshot",
        "",
        f"- Rows: `{len(df):,}`",
        f"- Columns: `{df.shape[1]}`",
        f"- Exact duplicate feature/outcome rows: `{df.duplicated().sum():,}`",
        f"- Missing cells: `{int(df.isna().sum().sum()):,}`",
        "- Customer identifier: not included in the public CSV, so exact duplicate rows should not be interpreted as duplicate customers.",
        "",
        "## Sample Size By Arm",
        "",
        markdown_table(["Segment", "Users"], sample_rows),
        "",
        "## Average Outcomes By Arm",
        "",
        markdown_table(
            ["Segment", "Visit Rate", "Conversion Rate", "Spend / Customer"],
            outcome_rows,
        ),
        "",
        "## Treatment Effects vs No E-Mail",
        "",
    ]

    for treatment in treatments:
        trt = df[df["segment"] == treatment]
        visit = two_prop_test(control["visit"], trt["visit"])
        conv = two_prop_test(control["conversion"], trt["conversion"])
        spend = mean_diff_test(control["spend"], trt["spend"])

        lines.extend(
            [
                f"### {treatment}",
                "",
                "| Metric | Control | Treatment | Absolute Lift | Relative Lift | 95% CI | p-value |",
                "|---|---:|---:|---:|---:|---:|---:|",
                (
                    f"| Visit rate | {format_pct(visit['control_rate'])} | "
                    f"{format_pct(visit['treatment_rate'])} | {format_pct(visit['abs_lift'])} | "
                    f"{format_pct(visit['rel_lift'])} | "
                    f"[{format_pct(visit['ci_low'])}, {format_pct(visit['ci_high'])}] | "
                    f"{visit['p_value']:.4f} |"
                ),
                (
                    f"| Conversion rate | {format_pct(conv['control_rate'])} | "
                    f"{format_pct(conv['treatment_rate'])} | {format_pct(conv['abs_lift'])} | "
                    f"{format_pct(conv['rel_lift'])} | "
                    f"[{format_pct(conv['ci_low'])}, {format_pct(conv['ci_high'])}] | "
                    f"{conv['p_value']:.4f} |"
                ),
                (
                    f"| Spend per customer | {format_money(spend['control_mean'])} | "
                    f"{format_money(spend['treatment_mean'])} | {format_money(spend['abs_lift'])} | "
                    f"{format_pct(spend['rel_lift'])} | "
                    f"[{format_money(spend['ci_low'])}, {format_money(spend['ci_high'])}] | "
                    f"{spend['p_value']:.4f} |"
                ),
                "",
                "Per 100k customers:",
                "",
                f"- Incremental conversions: `{conv['abs_lift'] * 100_000:,.0f}`",
                f"- Incremental spend: `{spend['abs_lift'] * 100_000:,.0f}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Product Reading",
            "",
            "- Treat `conversion` as the primary metric.",
            "- Treat `spend per customer` as the business metric.",
            "- Treat `visit` as a diagnostic metric: more visits are useful only if they translate into profitable conversion or spend.",
            "- Next step: segment the treatment effect by recency, historical spend, channel, and category preference before recommending a global send.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    df = load_data()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = build_report(df)
    REPORT_PATH.write_text(report)
    print(report)
    print(f"\nSaved report to {REPORT_PATH}")


if __name__ == "__main__":
    main()
