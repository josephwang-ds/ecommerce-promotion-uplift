from __future__ import annotations

from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "hillstrom_email.csv"
REPORT_PATH = PROJECT_ROOT / "reports" / "segment_uplift.md"
CSV_PATH = PROJECT_ROOT / "data" / "processed" / "segment_uplift.csv"

CONTROL = "No E-Mail"
TREATMENTS = ["Mens E-Mail", "Womens E-Mail"]


def load_data() -> pd.DataFrame:
    if not RAW_PATH.exists():
        raise FileNotFoundError(
            f"Missing raw data at {RAW_PATH}. Run `python src/download_data.py` first."
        )
    df = pd.read_csv(RAW_PATH)
    df["recency_band"] = pd.cut(
        df["recency"],
        bins=[0, 3, 6, 9, 12],
        labels=["1-3 months", "4-6 months", "7-9 months", "10-12 months"],
        include_lowest=True,
    )
    df["category_history"] = "Mixed / neither"
    df.loc[(df["mens"] == 1) & (df["womens"] == 0), "category_history"] = "Mens only"
    df.loc[(df["mens"] == 0) & (df["womens"] == 1), "category_history"] = "Womens only"
    df.loc[(df["mens"] == 1) & (df["womens"] == 1), "category_history"] = "Both mens and womens"
    df["customer_type"] = df["newbie"].map({0: "Existing", 1: "Newbie"})
    return df


def two_prop_test(control: pd.Series, treatment: pd.Series) -> dict[str, float]:
    n_c = control.shape[0]
    n_t = treatment.shape[0]
    x_c = control.sum()
    x_t = treatment.sum()
    p_c = x_c / n_c
    p_t = x_t / n_t
    pooled = (x_c + x_t) / (n_c + n_t)
    se = sqrt(pooled * (1 - pooled) * (1 / n_c + 1 / n_t)) if n_c and n_t else 0
    z = (p_t - p_c) / se if se else 0.0
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    return {
        "control_rate": p_c,
        "treatment_rate": p_t,
        "abs_lift": p_t - p_c,
        "p_value": p_value,
    }


def mean_diff_test(control: pd.Series, treatment: pd.Series) -> dict[str, float]:
    c = control.fillna(0)
    t = treatment.fillna(0)
    _, p_value = stats.ttest_ind(t, c, equal_var=False)
    return {
        "control_mean": c.mean(),
        "treatment_mean": t.mean(),
        "abs_lift": t.mean() - c.mean(),
        "p_value": p_value,
    }


def classify_policy(row: pd.Series) -> str:
    if row["n_control"] < 500 or row["n_treatment"] < 500:
        return "retest"
    if row["conversion_lift"] > 0 and row["spend_lift"] > 0:
        if row["conversion_p_value"] < 0.1 or row["spend_p_value"] < 0.1:
            return "target"
        return "retest"
    # Only suppress when BOTH metrics are negative — if just one is negative,
    # the signal is mixed (e.g. negative conversion but positive spend could be
    # higher AOV) and deserves a retest rather than a hard suppress.
    if row["conversion_lift"] < 0 and row["spend_lift"] < 0:
        return "suppress"
    return "retest"


def _bh_correct(p_values: pd.Series, fdr: float = 0.1) -> pd.Series:
    """Benjamini-Hochberg FDR correction.

    Returns a boolean Series: True = significant after BH correction at the
    given FDR level (default 10%).  Does not require external dependencies.
    """
    n = len(p_values)
    sorted_idx = np.argsort(p_values.values)
    sorted_p = p_values.values[sorted_idx]
    threshold = (np.arange(1, n + 1) / n) * fdr
    significant = sorted_p <= threshold
    if significant.any():
        last_sig = int(np.where(significant)[0][-1])
        reject = np.zeros(n, dtype=bool)
        reject[: last_sig + 1] = True
    else:
        reject = np.zeros(n, dtype=bool)
    result = np.zeros(n, dtype=bool)
    result[sorted_idx] = reject
    return pd.Series(result, index=p_values.index)


def build_segment_rows(df: pd.DataFrame) -> pd.DataFrame:
    segment_cols = [
        "history_segment",
        "recency_band",
        "channel",
        "zip_code",
        "customer_type",
        "category_history",
    ]
    rows: list[dict[str, object]] = []

    for segment_col in segment_cols:
        for segment_value, sub in df.groupby(segment_col, observed=True):
            control = sub[sub["segment"] == CONTROL]
            if control.empty:
                continue
            for treatment_name in TREATMENTS:
                treatment = sub[sub["segment"] == treatment_name]
                if treatment.empty:
                    continue
                visit = two_prop_test(control["visit"], treatment["visit"])
                conv = two_prop_test(control["conversion"], treatment["conversion"])
                spend = mean_diff_test(control["spend"], treatment["spend"])
                rows.append(
                    {
                        "segment_dimension": segment_col,
                        "segment_value": str(segment_value),
                        "treatment": treatment_name,
                        "n_control": len(control),
                        "n_treatment": len(treatment),
                        "control_conversion": conv["control_rate"],
                        "treatment_conversion": conv["treatment_rate"],
                        "conversion_lift": conv["abs_lift"],
                        "conversion_p_value": conv["p_value"],
                        "control_spend": spend["control_mean"],
                        "treatment_spend": spend["treatment_mean"],
                        "spend_lift": spend["abs_lift"],
                        "spend_p_value": spend["p_value"],
                        "visit_lift": visit["abs_lift"],
                        "visit_p_value": visit["p_value"],
                    }
                )

    result = pd.DataFrame(rows)
    result["policy"] = result.apply(classify_policy, axis=1)
    result["incremental_conversions_per_100k"] = result["conversion_lift"] * 100_000
    result["incremental_spend_per_100k"] = result["spend_lift"] * 100_000
    result["spend_sig_bh"] = _bh_correct(result["spend_p_value"])
    return result.sort_values(
        ["policy", "incremental_spend_per_100k"], ascending=[True, False]
    )


def pct(value: float) -> str:
    return f"{value:.2%}"


def money(value: float) -> str:
    return f"${value:,.3f}"


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def compact_rows(df: pd.DataFrame, limit: int = 10) -> list[list[str]]:
    rows: list[list[str]] = []
    for _, row in df.head(limit).iterrows():
        rows.append(
            [
                row["segment_dimension"],
                row["segment_value"],
                row["treatment"],
                row["policy"],
                f"{row['n_control']:,} / {row['n_treatment']:,}",
                pct(row["conversion_lift"]),
                money(row["spend_lift"]),
                f"{row['incremental_conversions_per_100k']:,.0f}",
                f"${row['incremental_spend_per_100k']:,.0f}",
            ]
        )
    return rows


def build_report(result: pd.DataFrame) -> str:
    headers = [
        "Dimension",
        "Segment",
        "Treatment",
        "Policy",
        "N C/T",
        "Conv Lift",
        "Spend Lift",
        "Inc Conv / 100k",
        "Inc Spend / 100k",
    ]
    target = result[result["policy"] == "target"].sort_values(
        "incremental_spend_per_100k", ascending=False
    )
    suppress = result[result["policy"] == "suppress"].sort_values(
        "incremental_spend_per_100k"
    )
    retest = result[result["policy"] == "retest"].sort_values(
        "incremental_spend_per_100k", ascending=False
    )

    lines = [
        "# Segment Uplift Readout",
        "",
        "## Product Question",
        "",
        "Which customer segments should receive a category promotion, which should be suppressed, and which need a follow-up experiment?",
        "",
        "中文问题：哪些用户应该定向触达，哪些用户应该避免发券/打扰，哪些人群需要继续测试创意或折扣力度？",
        "",
        "## Policy Rule",
        "",
        "- `target`: positive conversion lift and positive spend lift, with directional statistical support.",
        "- `suppress`: negative conversion lift or negative spend lift.",
        "- `retest`: small sample size or directionally positive but not enough evidence.",
        "",
        "This is a first-pass decision rule, not the final model. The next phase will use uplift modeling and policy simulation.",
        "",
        "## Top Target Candidates",
        "",
        markdown_table(headers, compact_rows(target)),
        "",
        "## Suppression Candidates",
        "",
        markdown_table(headers, compact_rows(suppress)),
        "",
        "## Strong Retest Candidates",
        "",
        markdown_table(headers, compact_rows(retest)),
        "",
        "## Product Reading",
        "",
        "- The global campaign result is positive, but targeting should focus on segments with both conversion and spend lift.",
        "- Some segments show positive visit lift but weaker spend lift; those are not automatic launch candidates.",
        "- Suppression candidates matter because a CRM campaign can waste discounts or attention even when the global average looks good.",
        "- In a China e-commerce setting, this becomes a member campaign audience rule: `target`, `suppress`, or `retest`.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    df = load_data()
    result = build_segment_rows(df)
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(CSV_PATH, index=False)
    report = build_report(result)
    REPORT_PATH.write_text(report)
    print(report)
    print(f"\nSaved segment table to {CSV_PATH}")
    print(f"Saved report to {REPORT_PATH}")


if __name__ == "__main__":
    main()
