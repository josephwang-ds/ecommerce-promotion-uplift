from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import nbformat as nbf
from nbclient import NotebookClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = PROJECT_ROOT / "notebooks" / "hillstrom_promotion_uplift_analysis.ipynb"


def md(source: str) -> nbf.NotebookNode:
    return nbf.v4.new_markdown_cell(dedent(source).strip())


def code(source: str) -> nbf.NotebookNode:
    return nbf.v4.new_code_cell(dedent(source).strip())


def build_notebook() -> nbf.NotebookNode:
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "name": "python",
            "pygments_lexer": "ipython3",
        },
    }

    nb.cells = [
        md(
            """
            # Hillstrom Promotion Uplift Analysis

            **Project context / 项目背景：**  
            This notebook analyzes a randomized email promotion experiment as a cross-border e-commerce CRM decision problem. The goal is to estimate incremental conversion and spend, then compare broad rollout against targeted rollout.

            **Business question:**  
            For a cross-border e-commerce CRM team, which campaign rollout policy creates the best incremental business value?

            **What this notebook shows:**  
            1. Experiment quality and sample split  
            2. Global A/B test readout  
            3. Segment uplift discovery  
            4. Cost-adjusted policy simulation  
            5. Business recommendation
            """
        ),
        code(
            """
            from pathlib import Path
            import os

            PROJECT_ROOT = Path.cwd()
            if PROJECT_ROOT.name == "notebooks":
                PROJECT_ROOT = PROJECT_ROOT.parent

            os.environ["MPLCONFIGDIR"] = str(PROJECT_ROOT / ".mplconfig")
            (PROJECT_ROOT / ".mplconfig").mkdir(exist_ok=True)

            import matplotlib.pyplot as plt
            import pandas as pd
            from scipy import stats

            RAW_PATH = PROJECT_ROOT / "data" / "raw" / "hillstrom_email.csv"
            SEGMENT_PATH = PROJECT_ROOT / "data" / "processed" / "segment_uplift.csv"
            POLICY_PATH = PROJECT_ROOT / "data" / "processed" / "policy_simulation.csv"

            pd.set_option("display.max_columns", 40)
            pd.set_option("display.width", 140)
            plt.style.use("seaborn-v0_8-whitegrid")
            """
        ),
        md(
            """
            ## 1. Load Data

            Dataset: Hillstrom email experiment.  
            The data contains a no-email holdout arm and two category email treatment arms.
            """
        ),
        code(
            """
            df = pd.read_csv(RAW_PATH)
            print(f"Rows: {len(df):,}")
            print(f"Columns: {df.shape[1]}")
            display(df.head())
            """
        ),
        code(
            """
            sample_split = (
                df["segment"]
                .value_counts()
                .rename_axis("experiment_arm")
                .reset_index(name="users")
                .sort_values("experiment_arm")
            )
            sample_split["share"] = sample_split["users"] / sample_split["users"].sum()
            display(sample_split)
            """
        ),
        md(
            """
            **Readout:** the three experiment arms are almost evenly split, so this is a clean randomized experiment for A/B readout.
            """
        ),
        md(
            """
            ## 2. Global Experiment Readout

            Start with the simple question: did each email treatment beat the no-email holdout?
            """
        ),
        code(
            """
            arm_summary = (
                df.groupby("segment")
                .agg(
                    users=("segment", "size"),
                    visit_rate=("visit", "mean"),
                    conversion_rate=("conversion", "mean"),
                    spend_per_customer=("spend", "mean"),
                )
                .reset_index()
            )
            display(arm_summary)
            """
        ),
        code(
            """
            fig, axes = plt.subplots(1, 2, figsize=(12, 4))

            axes[0].bar(arm_summary["segment"], arm_summary["conversion_rate"], color=["#94a3b8", "#4f46e5", "#14b8a6"])
            axes[0].set_title("Conversion Rate by Experiment Arm")
            axes[0].set_ylabel("Conversion rate")
            axes[0].tick_params(axis="x", rotation=20)
            axes[0].yaxis.set_major_formatter(lambda x, _: f"{x:.1%}")

            axes[1].bar(arm_summary["segment"], arm_summary["spend_per_customer"], color=["#94a3b8", "#4f46e5", "#14b8a6"])
            axes[1].set_title("Spend per Customer by Experiment Arm")
            axes[1].set_ylabel("Spend per customer")
            axes[1].tick_params(axis="x", rotation=20)
            axes[1].yaxis.set_major_formatter(lambda x, _: f"${x:.2f}")

            plt.tight_layout()
            plt.show()
            """
        ),
        code(
            """
            def two_prop_test(control, treatment):
                n_c, n_t = len(control), len(treatment)
                x_c, x_t = control.sum(), treatment.sum()
                p_c, p_t = x_c / n_c, x_t / n_t
                pooled = (x_c + x_t) / (n_c + n_t)
                se = (pooled * (1 - pooled) * (1 / n_c + 1 / n_t)) ** 0.5
                z = (p_t - p_c) / se
                p_value = 2 * (1 - stats.norm.cdf(abs(z)))
                return p_c, p_t, p_t - p_c, p_value

            def mean_diff_test(control, treatment):
                t_stat, p_value = stats.ttest_ind(treatment.fillna(0), control.fillna(0), equal_var=False)
                return control.mean(), treatment.mean(), treatment.mean() - control.mean(), p_value

            control = df[df["segment"] == "No E-Mail"]
            effect_rows = []
            for treatment_name in ["Mens E-Mail", "Womens E-Mail"]:
                treatment = df[df["segment"] == treatment_name]
                _, _, conv_lift, conv_p = two_prop_test(control["conversion"], treatment["conversion"])
                _, _, spend_lift, spend_p = mean_diff_test(control["spend"], treatment["spend"])
                effect_rows.append(
                    {
                        "treatment": treatment_name,
                        "conversion_lift": conv_lift,
                        "conversion_p_value": conv_p,
                        "incremental_conversions_per_100k": conv_lift * 100_000,
                        "spend_lift_per_customer": spend_lift,
                        "spend_p_value": spend_p,
                        "incremental_spend_per_100k": spend_lift * 100_000,
                    }
                )

            effects = pd.DataFrame(effect_rows)
            display(effects)
            """
        ),
        md(
            """
            **Business read / 中文解读：**  
            Mens E-Mail is the strongest global treatment. It improves both conversion and spend versus the no-email holdout, so it is a reasonable first candidate for rollout.

            但平均有效不等于应该全量发。CRM 的关键问题是：哪些用户真的有增量，哪些用户可能只是被打扰或浪费优惠券。
            """
        ),
        md(
            """
            ## 3. Segment Uplift Discovery

            Use existing customer features to find high-uplift and low-uplift groups.  
            This turns a global experiment readout into a customer targeting decision.
            """
        ),
        code(
            """
            segment_uplift = pd.read_csv(SEGMENT_PATH)
            top_targets = (
                segment_uplift[segment_uplift["policy"] == "target"]
                .sort_values("incremental_spend_per_100k", ascending=False)
                .head(8)
            )
            display(top_targets[
                [
                    "segment_dimension",
                    "segment_value",
                    "treatment",
                    "n_control",
                    "n_treatment",
                    "conversion_lift",
                    "spend_lift",
                    "incremental_spend_per_100k",
                    "policy",
                ]
            ])
            """
        ),
        code(
            """
            plot_df = top_targets.sort_values("incremental_spend_per_100k")
            labels = plot_df["segment_dimension"] + " = " + plot_df["segment_value"] + "\\n" + plot_df["treatment"]

            fig, ax = plt.subplots(figsize=(10, 5))
            ax.barh(labels, plot_df["incremental_spend_per_100k"], color="#4f46e5")
            ax.set_title("Top Target Segments by Incremental Spend per 100k")
            ax.set_xlabel("Incremental spend per 100k customers")
            ax.xaxis.set_major_formatter(lambda x, _: f"${x/1000:.0f}k")
            plt.tight_layout()
            plt.show()
            """
        ),
        code(
            """
            suppress = (
                segment_uplift[segment_uplift["policy"] == "suppress"]
                .sort_values("incremental_spend_per_100k")
                .head(6)
            )
            display(suppress[
                [
                    "segment_dimension",
                    "segment_value",
                    "treatment",
                    "conversion_lift",
                    "spend_lift",
                    "incremental_spend_per_100k",
                    "policy",
                ]
            ])
            """
        ),
        md(
            """
            **Business read / 中文解读：**  
            The target groups are not simply “everyone who bought before.” The strongest signal is category fit and historical value, especially users with both mens and womens history and high historical spend bands.

            这一步把实验结果翻译成 CRM 人群策略：`target`、`suppress`、`retest`。
            """
        ),
        md(
            """
            ## 4. Policy Simulation

            Compare four rollout policies:

            - No campaign holdout
            - Send all Mens E-Mail
            - Send all Womens E-Mail
            - Rule-based target/suppress

            The important twist: when every touch has coupon/contact cost, the best gross-spend policy may not be the best business policy.
            """
        ),
        code(
            """
            policy = pd.read_csv(POLICY_PATH)
            display(policy[
                [
                    "policy",
                    "contacted_share",
                    "conversion_rate",
                    "spend_per_customer",
                    "expected_conversions_per_100k",
                    "expected_spend_per_100k",
                    "contact_cost_per_100k",
                    "cost_adjusted_value_per_100k",
                    "incremental_spend_vs_holdout",
                ]
            ])
            """
        ),
        code(
            """
            policy_plot = policy.sort_values("cost_adjusted_value_per_100k")

            fig, ax = plt.subplots(figsize=(10, 5))
            ax.barh(policy_plot["policy"], policy_plot["cost_adjusted_value_per_100k"], color="#14b8a6")
            ax.set_title("Cost-adjusted Value per 100k Customers")
            ax.set_xlabel("Expected spend - contact cost")
            ax.xaxis.set_major_formatter(lambda x, _: f"${x/1000:.0f}k")
            plt.tight_layout()
            plt.show()
            """
        ),
        code(
            """
            best_gross = policy.sort_values("expected_spend_per_100k", ascending=False).iloc[0]
            best_cost_adjusted = policy.sort_values("cost_adjusted_value_per_100k", ascending=False).iloc[0]

            print(f"Best gross spend policy: {best_gross['policy']} (${best_gross['expected_spend_per_100k']:,.0f} per 100k)")
            print(
                f"Best cost-adjusted policy: {best_cost_adjusted['policy']} "
                f"(${best_cost_adjusted['cost_adjusted_value_per_100k']:,.0f} per 100k)"
            )
            """
        ),
        md(
            """
            ## 5. Business Recommendation

            **Recommendation:**  
            Roll out a targeted CRM policy rather than blindly sending to everyone, then use this rule-based policy as the baseline for the next uplift model.

            **中文业务结论：**  
            标准 A/B readout 显示，男装邮件相对 holdout 同时提升转化和 spend。分层 uplift 进一步显示，促销效果集中在特定用户群，而不是所有用户都适合被触达。Policy simulation 对比了全量发送、女装全量、男装全量和规则定向触达。结果显示：如果只看 gross spend，全量男装邮件最好；但如果考虑优惠券或触达成本，定向策略的成本调整价值更高。

            **Next phase:**  
            Train an uplift model on top of this rule baseline and compare top-decile targeting against the current rule-based policy.
            """
        ),
    ]
    return nb


def main() -> None:
    NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    nb = build_notebook()
    client = NotebookClient(nb, timeout=120, kernel_name="python3")
    client.execute(cwd=str(PROJECT_ROOT))
    nbf.write(nb, NOTEBOOK_PATH)
    print(f"Saved executed notebook to {NOTEBOOK_PATH}")


if __name__ == "__main__":
    main()
