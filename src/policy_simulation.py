from __future__ import annotations

from pathlib import Path
from typing import Callable

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "hillstrom_email.csv"
CSV_PATH = PROJECT_ROOT / "data" / "processed" / "policy_simulation.csv"
REPORT_PATH = PROJECT_ROOT / "reports" / "policy_simulation.md"

N_CUSTOMERS = 100_000
CONTACT_COST = 0.55


def load_data() -> pd.DataFrame:
    if not RAW_PATH.exists():
        raise FileNotFoundError(
            f"Missing raw data at {RAW_PATH}. Run `python src/download_data.py` first."
        )
    df = pd.read_csv(RAW_PATH)
    df["category_history"] = "Mixed / neither"
    df.loc[(df["mens"] == 1) & (df["womens"] == 0), "category_history"] = "Mens only"
    df.loc[(df["mens"] == 0) & (df["womens"] == 1), "category_history"] = "Womens only"
    df.loc[(df["mens"] == 1) & (df["womens"] == 1), "category_history"] = "Both mens and womens"
    return df


def policy_none(_: pd.DataFrame) -> pd.Series:
    return pd.Series("No E-Mail", index=_.index)


def policy_all_mens(_: pd.DataFrame) -> pd.Series:
    return pd.Series("Mens E-Mail", index=_.index)


def policy_all_womens(_: pd.DataFrame) -> pd.Series:
    return pd.Series("Womens E-Mail", index=_.index)


def policy_rule_based(df: pd.DataFrame) -> pd.Series:
    """First-pass CRM rule from segment uplift readout."""
    assignment = pd.Series("No E-Mail", index=df.index)

    both_category = df["category_history"] == "Both mens and womens"
    multichannel = df["channel"] == "Multichannel"
    mens_history_band = df["history_segment"].isin(
        ["4) $350 - $500", "5) $500 - $750", "6) $750 - $1,000"]
    )
    recent_buyers = df["recency"] <= 3
    high_history = df["history"] >= 350

    assignment.loc[both_category | multichannel | mens_history_band | (recent_buyers & high_history)] = "Mens E-Mail"
    return assignment


POLICIES: dict[str, Callable[[pd.DataFrame], pd.Series]] = {
    "No campaign holdout": policy_none,
    "Send all Mens E-Mail": policy_all_mens,
    "Send all Womens E-Mail": policy_all_womens,
    "Rule-based target/suppress": policy_rule_based,
}


def estimate_policy(df: pd.DataFrame, name: str, assign_fn: Callable[[pd.DataFrame], pd.Series]) -> dict[str, float | str]:
    assignment = assign_fn(df)
    rows = []
    for treatment, index in assignment.groupby(assignment).groups.items():
        assigned_population_share = len(index) / len(df)
        sub = df.loc[index]
        observed = sub[sub["segment"] == treatment]
        if observed.empty:
            observed = df[df["segment"] == treatment]
        rows.append(
            {
                "population_share": assigned_population_share,
                "visit": observed["visit"].mean(),
                "conversion": observed["conversion"].mean(),
                "spend": observed["spend"].mean(),
            }
        )
    policy_df = pd.DataFrame(rows)
    visit = (policy_df["population_share"] * policy_df["visit"]).sum()
    conversion = (policy_df["population_share"] * policy_df["conversion"]).sum()
    spend = (policy_df["population_share"] * policy_df["spend"]).sum()
    contacted_share = (assignment != "No E-Mail").mean()
    return {
        "policy": name,
        "contacted_share": contacted_share,
        "visit_rate": visit,
        "conversion_rate": conversion,
        "spend_per_customer": spend,
        "expected_conversions_per_100k": conversion * N_CUSTOMERS,
        "expected_spend_per_100k": spend * N_CUSTOMERS,
        "contact_cost_per_100k": contacted_share * N_CUSTOMERS * CONTACT_COST,
    }


def money(value: float) -> str:
    return f"${value:,.0f}"


def money_3(value: float) -> str:
    return f"${value:,.3f}"


def pct(value: float) -> str:
    return f"{value:.2%}"


def markdown_table(df: pd.DataFrame) -> str:
    rows = []
    for _, row in df.iterrows():
        rows.append(
            [
                row["policy"],
                pct(row["contacted_share"]),
                pct(row["conversion_rate"]),
                money_3(row["spend_per_customer"]),
                f"{row['expected_conversions_per_100k']:,.0f}",
                money(row["expected_spend_per_100k"]),
                money(row["contact_cost_per_100k"]),
                money(row["cost_adjusted_value_per_100k"]),
                f"{row['incremental_conversions_vs_holdout']:,.0f}",
                money(row["incremental_spend_vs_holdout"]),
            ]
        )
    headers = [
        "Policy",
        "Contacted",
        "Conv Rate",
        "Spend / Customer",
        "Conv / 100k",
        "Spend / 100k",
        "Contact Cost",
        "Cost-Adj Value",
        "Inc Conv",
        "Inc Spend",
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def build_report(result: pd.DataFrame) -> str:
    best_gross = result.sort_values("expected_spend_per_100k", ascending=False).iloc[0]
    best_cost_adjusted = result.sort_values("cost_adjusted_value_per_100k", ascending=False).iloc[0]
    return "\n".join(
        [
            "# Policy Simulation",
            "",
            "## Product Question",
            "",
            "If the campaign is effective on average, which rollout policy creates the best expected business outcome?",
            "",
            "中文问题：如果促销平均有效，应该全量发、只发某一类目，还是按用户分层定向触达？",
            "",
            "## Policy Comparison",
            "",
            markdown_table(result),
            "",
            "## Recommendation",
            "",
            f"- Best gross spend policy: `{best_gross['policy']}`.",
            f"- Best cost-adjusted policy with `${CONTACT_COST:.2f}` contact/incentive cost: `{best_cost_adjusted['policy']}`.",
            "- Use this rule-based policy as a baseline for future uplift modeling, not as a final production targeting model.",
            "- The next phase should train an uplift model and compare uplift-score targeting against this rule-based baseline.",
            "",
            "中文结论：",
            "",
            f"- 如果只看 gross spend，最优策略是 `{best_gross['policy']}`。",
            f"- 如果考虑每次触达/优惠券成本 `${CONTACT_COST:.2f}`，成本调整后最优策略是 `{best_cost_adjusted['policy']}`。",
            "- 这个规则策略适合作为后续 uplift model 的 baseline，不应包装成最终生产模型。",
            "- 下一步应该训练 uplift model，用模型分数和规则分层策略对比。",
            "",
        ]
    )


def main() -> None:
    df = load_data()
    result = pd.DataFrame(
        [estimate_policy(df, name, fn) for name, fn in POLICIES.items()]
    )
    holdout = result.loc[result["policy"] == "No campaign holdout"].iloc[0]
    result["incremental_conversions_vs_holdout"] = (
        result["expected_conversions_per_100k"] - holdout["expected_conversions_per_100k"]
    )
    result["incremental_spend_vs_holdout"] = (
        result["expected_spend_per_100k"] - holdout["expected_spend_per_100k"]
    )
    result["cost_adjusted_value_per_100k"] = (
        result["expected_spend_per_100k"] - result["contact_cost_per_100k"]
    )
    result = result.sort_values("expected_spend_per_100k", ascending=False)

    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(CSV_PATH, index=False)
    report = build_report(result)
    REPORT_PATH.write_text(report)
    print(report)
    print(f"Saved policy table to {CSV_PATH}")
    print(f"Saved report to {REPORT_PATH}")


if __name__ == "__main__":
    main()
