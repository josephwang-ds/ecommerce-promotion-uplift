"""T-learner uplift model using logistic regression.

Simple two-model approach:
- Model T: trained on treatment (Mens E-Mail) group
- Model C: trained on control (No E-Mail) group
- Uplift score = P(conversion | treated) - P(conversion | not treated)

Intentionally simple so the approach is easy to explain in interviews.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "hillstrom_email.csv"
UPLIFT_PATH = PROJECT_ROOT / "data" / "processed" / "uplift_scores.csv"
DECILE_PATH = PROJECT_ROOT / "data" / "processed" / "uplift_deciles.csv"
REPORT_PATH = PROJECT_ROOT / "reports" / "uplift_model.md"

TREATMENT = "Mens E-Mail"
CONTROL = "No E-Mail"


def load_and_prepare(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Encode features; return X and y (conversion)."""
    features = df.copy()

    # Encode categoricals
    for col in ["channel", "zip_code", "history_segment"]:
        le = LabelEncoder()
        features[col + "_enc"] = le.fit_transform(features[col].astype(str))

    feature_cols = [
        "history",
        "recency",
        "mens",
        "womens",
        "newbie",
        "channel_enc",
        "zip_code_enc",
    ]
    return features[feature_cols], features["conversion"]


def train_t_learner(
    df: pd.DataFrame,
) -> tuple[LogisticRegression, LogisticRegression]:
    """Train treatment and control logistic regression models."""
    treatment_df = df[df["segment"] == TREATMENT].copy()
    control_df = df[df["segment"] == CONTROL].copy()

    X_t, y_t = load_and_prepare(treatment_df)
    X_c, y_c = load_and_prepare(control_df)

    model_t = LogisticRegression(max_iter=500, random_state=42)
    model_t.fit(X_t, y_t)

    model_c = LogisticRegression(max_iter=500, random_state=42)
    model_c.fit(X_c, y_c)

    return model_t, model_c


def score_population(
    df: pd.DataFrame,
    model_t: LogisticRegression,
    model_c: LogisticRegression,
) -> pd.DataFrame:
    """Compute uplift score for all customers."""
    X, _ = load_and_prepare(df)
    p_treatment = model_t.predict_proba(X)[:, 1]
    p_control = model_c.predict_proba(X)[:, 1]
    uplift = p_treatment - p_control

    out = df[["segment", "conversion", "spend"]].copy()
    out["uplift_score"] = uplift
    out["p_treatment"] = p_treatment
    out["p_control"] = p_control
    return out


def compute_deciles(scored: pd.DataFrame) -> pd.DataFrame:
    """Compute observed uplift by predicted-score decile.

    Decile 10 = highest predicted uplift (best targets).
    Each decile shows the actual conversion lift vs control in that band.
    """
    scored = scored.copy()
    scored["decile"] = pd.qcut(
        scored["uplift_score"], q=10, labels=range(1, 11), duplicates="drop"
    )
    scored["decile"] = scored["decile"].astype(int)

    control_conv = scored[scored["segment"] == CONTROL]["conversion"].mean()
    control_spend = scored[scored["segment"] == CONTROL]["spend"].mean()

    rows = []
    for decile in sorted(scored["decile"].unique()):
        sub = scored[scored["decile"] == decile]
        treated = sub[sub["segment"] == TREATMENT]
        control = sub[sub["segment"] == CONTROL]

        n_treated = len(treated)
        n_control = len(control)

        obs_conv_lift = (
            treated["conversion"].mean() - control["conversion"].mean()
            if n_control > 0
            else np.nan
        )
        obs_spend_lift = (
            treated["spend"].mean() - control["spend"].mean()
            if n_control > 0
            else np.nan
        )
        avg_score = sub["uplift_score"].mean()

        rows.append(
            {
                "decile": decile,
                "n_treated": n_treated,
                "n_control": n_control,
                "avg_uplift_score": avg_score,
                "obs_conversion_lift": obs_conv_lift,
                "obs_spend_lift": obs_spend_lift,
                "incr_conv_per_100k": obs_conv_lift * 100_000
                if not np.isnan(obs_conv_lift)
                else np.nan,
                "incr_spend_per_100k": obs_spend_lift * 100_000
                if not np.isnan(obs_spend_lift)
                else np.nan,
            }
        )

    return pd.DataFrame(rows)


def model_vs_rule_summary(scored: pd.DataFrame, deciles: pd.DataFrame) -> str:
    """Compare top-30% model targeting vs rule-based policy."""
    # Model: top 3 deciles (deciles 8, 9, 10 = top 30% by score)
    top_deciles = deciles[deciles["decile"] >= 8]
    model_incr_spend = top_deciles["incr_spend_per_100k"].mean()

    # Rule-based (from policy_simulation): ~$41,246 incremental spend vs holdout
    rule_incr_spend = 41_246

    lines = [
        "## Model vs Rule-based Comparison (top 30% targeting)",
        "",
        f"- Top-3-decile model targeting: ~${model_incr_spend:,.0f} avg incremental spend / 100k",
        f"- Rule-based target/suppress: ~${rule_incr_spend:,.0f} incremental spend vs holdout",
        "",
        "Note: decile comparison uses observed uplift within each score band, not a held-out test set.",
        "A proper evaluation would split the data and evaluate on a holdout.",
        "",
    ]
    return "\n".join(lines)


def build_report(deciles: pd.DataFrame, scored: pd.DataFrame) -> str:
    rows = []
    for _, row in deciles.iterrows():
        rows.append(
            [
                str(int(row["decile"])),
                f"{row['avg_uplift_score']:.4f}",
                f"{row['obs_conversion_lift']:.2%}"
                if not np.isnan(row["obs_conversion_lift"])
                else "—",
                f"${row['obs_spend_lift']:.3f}"
                if not np.isnan(row["obs_spend_lift"])
                else "—",
                f"${row['incr_spend_per_100k']:,.0f}"
                if not np.isnan(row["incr_spend_per_100k"])
                else "—",
            ]
        )
    headers = ["Decile", "Avg Score", "Conv Lift", "Spend Lift", "Incr Spend / 100k"]
    table_lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ] + ["| " + " | ".join(row) + " |" for row in rows]

    return "\n".join(
        [
            "# T-learner Uplift Model Readout",
            "",
            "## Model",
            "",
            "Two-model (T-learner) approach using logistic regression.",
            "",
            "- Model T: trained on Mens E-Mail group.",
            "- Model C: trained on No E-Mail group.",
            "- Uplift score = P(conversion | treated) - P(conversion | control).",
            "",
            "Features: history, recency, mens, womens, newbie, channel, zip_code.",
            "",
            "## Uplift By Predicted-Score Decile",
            "",
            "Decile 10 = highest predicted uplift (best targets).",
            "",
        ]
        + table_lines
        + [
            "",
            model_vs_rule_summary(scored, deciles),
            "## Business Read",
            "",
            "- The top deciles (8-10) show the strongest observed conversion and spend lift.",
            "- The bottom deciles (1-3) show weak or near-zero lift — these customers are "
            "less persuadable.",
            "- Targeting the top 30% by uplift score is a more data-driven version of the "
            "rule-based segment policy.",
            "- Next step: proper train/test split and Qini curve evaluation.",
            "",
        ]
    )


def main() -> None:
    df = pd.read_csv(RAW_PATH)

    print("Training T-learner...")
    model_t, model_c = train_t_learner(df)

    print("Scoring population...")
    scored = score_population(df, model_t, model_c)

    print("Computing deciles...")
    deciles = compute_deciles(scored)

    UPLIFT_PATH.parent.mkdir(parents=True, exist_ok=True)
    scored.to_csv(UPLIFT_PATH, index=False)
    deciles.to_csv(DECILE_PATH, index=False)

    report = build_report(deciles, scored)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report)

    print(report)
    print(f"Saved uplift scores to {UPLIFT_PATH}")
    print(f"Saved decile table to {DECILE_PATH}")
    print(f"Saved report to {REPORT_PATH}")


if __name__ == "__main__":
    main()
