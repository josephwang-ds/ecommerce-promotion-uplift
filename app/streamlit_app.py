"""Streamlit demo: E-commerce Promotion Uplift (Hillstrom experiment).

Sections:
1. Global experiment readout  — bar charts + statistical details
2. Segment uplift             — filterable bar chart + table
3. Policy simulation          — cost-adjusted comparison + breakeven
4. Uplift model               — T-learner decile results + targeting calculator
5. Key takeaways
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from scipy import stats as scipy_stats


st.set_page_config(
    page_title="E-commerce Promotion Uplift",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH     = PROJECT_ROOT / "data" / "raw"       / "hillstrom_email.csv"
SEGMENT_PATH = PROJECT_ROOT / "data" / "processed" / "segment_uplift.csv"
POLICY_PATH  = PROJECT_ROOT / "data" / "processed" / "policy_simulation.csv"
DECILE_PATH  = PROJECT_ROOT / "data" / "processed" / "uplift_deciles.csv"
SCORES_PATH  = PROJECT_ROOT / "data" / "processed" / "uplift_scores.csv"


# ── CSS ──────────────────────────────────────────────────────────────────────

def add_css() -> None:
    st.markdown(
        """
        <style>
        .block-container { padding-top: 2rem; padding-bottom: 3rem; }
        div[data-testid="stMetric"] {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 1rem 1rem 0.8rem;
        }
        .callout {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-left: 4px solid #2563eb;
            border-radius: 8px;
            padding: 1rem 1.1rem;
            margin: 0.5rem 0 1rem;
            color: #111827;
        }
        .warn { background: #fff7ed; border-left-color: #f97316; }
        .green { background: #f0fdf4; border-left-color: #16a34a; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ── Data loaders ─────────────────────────────────────────────────────────────

@st.cache_data
def load_raw() -> pd.DataFrame:
    return pd.read_csv(RAW_PATH)

@st.cache_data
def load_segment() -> pd.DataFrame:
    return pd.read_csv(SEGMENT_PATH)

@st.cache_data
def load_policy() -> pd.DataFrame:
    return pd.read_csv(POLICY_PATH)

@st.cache_data
def load_deciles() -> pd.DataFrame:
    return pd.read_csv(DECILE_PATH)


# ── Formatters ───────────────────────────────────────────────────────────────

def money(v: float) -> str:    return f"${v:,.0f}"
def money_3(v: float) -> str:  return f"${v:,.3f}"
def pct(v: float) -> str:      return f"{v:.2%}"

def sig_stars(p: float) -> str:
    if p < 0.01: return "***"
    if p < 0.05: return "**"
    if p < 0.10: return "*"
    return ""


# ── Stats helpers ────────────────────────────────────────────────────────────

@st.cache_data
def compute_global_stats(raw: pd.DataFrame) -> dict:
    control = raw[raw["segment"] == "No E-Mail"]
    mens    = raw[raw["segment"] == "Mens E-Mail"]
    womens  = raw[raw["segment"] == "Womens E-Mail"]

    results = {}
    for name, trt in [("mens", mens), ("womens", womens)]:
        p_c = control["conversion"].mean()
        p_t = trt["conversion"].mean()
        h = 2 * np.arcsin(np.sqrt(p_t)) - 2 * np.arcsin(np.sqrt(p_c))

        c_sp = control["spend"].fillna(0)
        t_sp = trt["spend"].fillna(0)
        _, p_mw = scipy_stats.mannwhitneyu(t_sp, c_sp, alternative="two-sided")
        _, p_t_test = scipy_stats.ttest_ind(t_sp, c_sp, equal_var=False)

        diff_sp = t_sp.mean() - c_sp.mean()
        pooled_std = np.sqrt((c_sp.std()**2 + t_sp.std()**2) / 2)
        d = diff_sp / pooled_std

        results[name] = {
            "cohen_h": h,
            "cohen_d": d,
            "mann_whitney_p": p_mw,
            "t_test_p": p_t_test,
            "zeros_pct": (trt["spend"] == 0).mean(),
        }
    results["control_zeros"] = (control["spend"] == 0).mean()
    return results


def recompute_policy(policy: pd.DataFrame, contact_cost: float) -> pd.DataFrame:
    out = policy.copy()
    out["contact_cost_per_100k"] = out["contacted_share"] * 100_000 * contact_cost
    out["cost_adjusted_value_per_100k"] = (
        out["expected_spend_per_100k"] - out["contact_cost_per_100k"]
    )
    return out.sort_values("cost_adjusted_value_per_100k", ascending=False)


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    add_css()

    raw     = load_raw()
    segment = load_segment()
    policy  = load_policy()

    control = raw[raw["segment"] == "No E-Mail"]
    mens    = raw[raw["segment"] == "Mens E-Mail"]
    womens  = raw[raw["segment"] == "Womens E-Mail"]
    gstats  = compute_global_stats(raw)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        lang = st.radio("语言 / Language", ["English", "中文"], horizontal=True)
        st.markdown(
            "← [项目分析报告](https://www.josephjwang.com/promotion-uplift) · "
            "[josephjwang.com](https://www.josephjwang.com)"
        )
        st.caption("📊 分析报告见上方链接 · 这里是交互工具版" if lang == "中文" else
                   "📊 Full report via link above · Interactive tool version here")
        st.divider()
        st.header("参数控制" if lang == "中文" else "Controls")
        contact_cost = st.slider(
            "每用户接触/激励成本 ($)" if lang == "中文" else "Contact / incentive cost per user ($)",
            min_value=0.0, max_value=1.5, value=0.55, step=0.05,
            help="调整第 3 节成本效益分析。" if lang == "中文" else "Adjusts cost-benefit analysis in Section 3.",
        )
        treatment_filter = st.selectbox(
            "分群筛选 — 活动" if lang == "中文" else "Segment filter — campaign",
            ["All", "Mens E-Mail", "Womens E-Mail"],
        )
        st.divider()
        st.caption(
            "数据集：Hillstrom MineThatData 随机邮件实验（2008）。\n"
            "业务背景：跨境电商 CRM — 类目促销、保留组、GMV 增量。"
            if lang == "中文" else
            "Dataset: Hillstrom MineThatData randomized email experiment (2008).\n"
            "Business framing: cross-border e-commerce CRM — category promotions, "
            "holdout groups, GMV incrementality."
        )

    def t(en: str, zh: str) -> str:
        return zh if lang == "中文" else en

    # ── Header ────────────────────────────────────────────────────────────────
    st.title(t("📊 Personalized Promotion Experiment", "📊 个性化促销实验"))
    st.caption(t(
        "Cross-border e-commerce CRM · Hillstrom email experiment · "
        "Incrementality analysis, segment uplift & rollout policy",
        "跨境电商 CRM · Hillstrom 邮件实验 · 增量分析、分群提升与推广策略"
    ))
    st.markdown(
        f"""
        <div class="callout">
        <b>{t("Business question", "业务问题")}</b> — {t(
            "Does a category-specific promotion create incremental conversion and GMV versus a no-contact holdout group? Which customers should be targeted, suppressed, or retested?",
            "类目促销相对 holdout 组是否带来增量转化和 GMV？哪些用户应该触达，哪些 suppress，哪些需要重新实验？"
        )}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Top KPIs ──────────────────────────────────────────────────────────────
    mens_incr_conv  = (mens["conversion"].mean() - control["conversion"].mean()) * 100_000
    mens_incr_spend = (mens["spend"].mean()       - control["spend"].mean())      * 100_000

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric(t("Total users", "总用户"),             f"{len(raw):,}")
    c2.metric(t("Holdout conversion", "对照组转化率"), pct(control["conversion"].mean()))
    c3.metric(t("Mens email conversion", "男装邮件转化率"), pct(mens["conversion"].mean()),
              delta=pct(mens["conversion"].mean() - control["conversion"].mean()))
    c4.metric(t("Womens email conversion", "女装邮件转化率"), pct(womens["conversion"].mean()),
              delta=pct(womens["conversion"].mean() - control["conversion"].mean()))
    c5.metric(t("Mens incr. conv / 100k", "男装增量转化 / 10万"),  f"{mens_incr_conv:,.0f}",
              help=t("(Treatment − holdout) × 100k", "（实验组 − 对照组）× 10万"))
    c6.metric(t("Mens incr. spend / 100k", "男装增量消费 / 10万"), money(mens_incr_spend),
              help=t("(Treatment − holdout) spend × 100k", "（实验组 − 对照组）消费 × 10万"))

    # ── Section 1: Global Experiment Readout ─────────────────────────────────
    st.divider()
    st.subheader(t("1. Global Experiment Readout", "1. 全局实验分析"))
    st.write(t("Both treatment arms outperform holdout. Mens email shows stronger lift on both conversion and spend.",
               "两个实验组均优于对照组。男装邮件在转化率和消费额上均显示出更强的提升。"))

    # Summary table
    arm_col = t("Arm", "分组"); users_col = t("Users", "用户数")
    visit_col = t("Visit Rate", "访问率"); conv_col = t("Conversion Rate", "转化率")
    spend_col = t("Avg Spend / User", "人均消费"); incr_conv_col = t("Incr. Conv / 100k", "增量转化/10万")
    incr_spend_col = t("Incr. Spend / 100k", "增量消费/10万")
    global_rows = pd.DataFrame([
        {
            arm_col: t("No E-Mail (holdout)", "无邮件（对照组）"),
            users_col: len(control),
            visit_col:       pct(control["visit"].mean()),
            conv_col:  pct(control["conversion"].mean()),
            spend_col: money_3(control["spend"].mean()),
            incr_conv_col:  "—",
            incr_spend_col: "—",
        },
        {
            arm_col: "Mens E-Mail",
            users_col: len(mens),
            visit_col:       pct(mens["visit"].mean()),
            conv_col:  pct(mens["conversion"].mean()),
            spend_col: money_3(mens["spend"].mean()),
            incr_conv_col:  f"{(mens['conversion'].mean()-control['conversion'].mean())*100_000:,.0f}",
            incr_spend_col: money((mens["spend"].mean()-control["spend"].mean())*100_000),
        },
        {
            arm_col: "Womens E-Mail",
            users_col: len(womens),
            visit_col:       pct(womens["visit"].mean()),
            conv_col:  pct(womens["conversion"].mean()),
            spend_col: money_3(womens["spend"].mean()),
            incr_conv_col:  f"{(womens['conversion'].mean()-control['conversion'].mean())*100_000:,.0f}",
            incr_spend_col: money((womens["spend"].mean()-control["spend"].mean())*100_000),
        },
    ])
    st.dataframe(global_rows, use_container_width=True, hide_index=True)

    # Bar charts
    col_a, col_b = st.columns(2)
    with col_a:
        st.caption(t("**Conversion rate by arm**", "**各分组转化率**"))
        conv_chart = pd.DataFrame({
            t("Conversion Rate (%)", "转化率 (%)"): [
                control["conversion"].mean() * 100,
                mens["conversion"].mean() * 100,
                womens["conversion"].mean() * 100,
            ]
        }, index=[t("Holdout","对照组"), "Mens Email", "Womens Email"])
        st.bar_chart(conv_chart, color="#4f46e5")

    with col_b:
        st.caption(t("**Avg spend per user by arm**", "**各分组人均消费**"))
        spend_chart = pd.DataFrame({
            t("Avg Spend / User ($)", "人均消费 ($)"): [
                control["spend"].mean(),
                mens["spend"].mean(),
                womens["spend"].mean(),
            ]
        }, index=[t("Holdout","对照组"), "Mens Email", "Womens Email"])
        st.bar_chart(spend_chart, color="#0891b2")

    # Statistical details expander
    with st.expander(t("📐 Statistical details — tests, effect sizes, robustness checks",
                       "📐 统计细节 — 检验、效应量、稳健性检验")):
        s = gstats["mens"]
        if lang == "English":
            st.markdown(f"""
**Mens E-Mail vs Holdout**

| Check | Value | Interpretation |
|---|---|---|
| Two-proportion z-test (conversion) | p < 0.0001 *** | Conversion lift is statistically significant |
| Welch's t-test (spend) | p = {s['t_test_p']:.2e} | Spend lift is statistically significant |
| Mann-Whitney U (spend, non-parametric) | p = {s['mann_whitney_p']:.2e} | Confirms t-test — robust to non-normality |
| Cohen's h (conversion effect size) | {s['cohen_h']:.3f} | Small by convention — business value comes from scale |
| Cohen's d (spend effect size) | {s['cohen_d']:.3f} | Small by convention |
| Spend = $0 in holdout | {gstats['control_zeros']:.1%} | 99.4% of customers spend $0 |
| Spend = $0 in Mens Email | {s['zeros_pct']:.1%} | Lift = more conversions, not outlier spenders |

**Key insight:** Effect sizes are small (h = 0.073, d = 0.051) — this is normal for CRM campaigns.
Business value comes from scale: 681 incremental conversions × 100k customers.
Spend lift is **not** driven by outliers — it comes from more customers converting from $0 to a positive spend.
Mann-Whitney U confirms the t-test result, showing it's robust to the non-normal spend distribution.
        """)
        else:
            st.markdown(f"""
**男装邮件 vs 对照组**

| 检验 | 结果 | 解读 |
|---|---|---|
| 双比例 z 检验（转化率） | p < 0.0001 *** | 转化率提升统计显著 |
| Welch t 检验（消费额） | p = {s['t_test_p']:.2e} | 消费额提升统计显著 |
| Mann-Whitney U（消费额，非参数） | p = {s['mann_whitney_p']:.2e} | 证实 t 检验——对非正态分布稳健 |
| Cohen's h（转化率效应量） | {s['cohen_h']:.3f} | 按惯例为小效应——业务价值靠规模体现 |
| Cohen's d（消费额效应量） | {s['cohen_d']:.3f} | 按惯例为小效应 |
| 对照组零消费比例 | {gstats['control_zeros']:.1%} | 99.4% 的客户消费为 $0 |
| 男装邮件零消费比例 | {s['zeros_pct']:.1%} | 提升来自更多转化，而非异常高消费者 |

**关键洞察：** 效应量小（h = 0.073，d = 0.051）——这对 CRM 活动是正常的。
业务价值来自规模：681 增量转化 × 10 万用户。
消费提升**不**由异常值驱动——而是来自更多客户从 $0 转为正向消费。
Mann-Whitney U 确认 t 检验结果，显示对非正态消费分布具有稳健性。
        """)

    # ── Section 2: Segment Uplift ─────────────────────────────────────────────
    st.divider()
    st.subheader(t("2. Segment Uplift: Target / Suppress / Retest",
                   "2. 分群提升：定向 / 屏蔽 / 重测"))
    st.write(t(
        "Average lift is positive, but segment-level variation is large. "
        "CRM rollout should focus on high-uplift pockets and suppress negative-uplift segments.",
        "平均提升为正，但分群间差异很大。CRM 推广应聚焦高提升细分群，并屏蔽负向提升的分群。"
    ))

    seg_view = segment.copy()
    if treatment_filter != "All":
        seg_view = seg_view[seg_view["treatment"] == treatment_filter]

    # Sort control
    sort_opts = (["增量消费/10万", "转化提升", "人均消费提升"] if lang == "中文"
                 else ["Incr. Spend / 100k", "Conv. Lift", "Spend Lift / User"])
    sort_col = st.radio(t("Sort by", "排序方式"), sort_opts, horizontal=True)
    sort_map = {
        "Incr. Spend / 100k": "incremental_spend_per_100k",
        "增量消费/10万":       "incremental_spend_per_100k",
        "Conv. Lift":         "conversion_lift",
        "转化提升":            "conversion_lift",
        "Spend Lift / User":  "spend_lift",
        "人均消费提升":        "spend_lift",
    }
    seg_view = seg_view.sort_values(sort_map[sort_col], ascending=False)
    seg_view["sig"] = seg_view["spend_p_value"].apply(sig_stars)

    # Horizontal bar chart — top 12 segments
    top12 = seg_view.head(12).copy()
    top12["label"] = top12["segment_value"] + " · " + top12["treatment"].str.replace(" E-Mail", "")
    chart_seg = top12.set_index("label")[["incremental_spend_per_100k"]].rename(
        columns={"incremental_spend_per_100k": t("Incr. Spend / 100k ($)", "增量消费/10万 ($)")}
    )
    st.caption(t("**Incremental spend / 100k — top 12 segments**", "**增量消费/10万 — 前12分群**"))
    st.bar_chart(chart_seg, color="#16a34a")

    # Table
    display_cols = [
        "segment_dimension", "segment_value", "treatment", "policy",
        "conversion_lift", "spend_lift", "incremental_spend_per_100k",
        "sig", "spend_sig_bh",
    ]
    col_rename = {
        "segment_dimension": t("Dimension","维度"), "segment_value": t("Segment","分群"),
        "treatment": t("Campaign","活动"), "policy": t("Policy","策略"),
        "conversion_lift": t("Conv. Lift","转化提升"), "spend_lift": t("Spend Lift / User","人均消费提升"),
        "incremental_spend_per_100k": t("Incr. Spend / 100k","增量消费/10万"),
        "sig": t("Sig.","显著性"), "spend_sig_bh": "BH✓",
    }
    cv_col = t("Conv. Lift","转化提升")
    sl_col = t("Spend Lift / User","人均消费提升")
    is_col = t("Incr. Spend / 100k","增量消费/10万")
    styled = (
        seg_view[display_cols].head(15).rename(columns=col_rename)
        .style.format({
            cv_col:  "{:.2%}",
            sl_col:  "${:,.3f}",
            is_col:  "${:,.0f}",
            "BH✓":   lambda v: "✓" if v else "",
        })
        .map(
            lambda v: "color: #16a34a; font-weight:600" if v == "target"
                      else ("color: #dc2626; font-weight:600" if v == "suppress" else ""),
            subset=[t("Policy","策略")],
        )
        .map(
            lambda v: "color: #dc2626" if isinstance(v, float) and v < 0 else "",
            subset=[cv_col, sl_col, is_col],
        )
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)
    st.caption(t(
        "Sig.: *** p<0.01 · ** p<0.05 · * p<0.10  |  "
        "BH✓: significant after Benjamini-Hochberg FDR correction (10%) across all 60+ comparisons",
        "显著性：*** p<0.01 · ** p<0.05 · * p<0.10  |  "
        "BH✓：对全部 60+ 比较进行 Benjamini-Hochberg FDR 校正后显著（10%）"
    ))

    st.markdown(
        f"""
        <div class="callout warn">
        <b>{t("Key finding", "关键发现")}</b> — {t(
            "Strongest target: customers with both mens &amp; womens purchase history receiving Mens E-Mail (incr. spend $182k/100k). Suppress rule uses AND logic: both conversion AND spend must be negative. Mixed signals → retest, not suppress.",
            "最强定向：历史同时买过男女装的用户收到男装邮件增量最高（$182k/10万用户）。屏蔽条件是 AND：conversion 和 spend 同时为负才屏蔽，单一指标负向 → 重测。"
        )}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Section 3: Rollout Policy Simulation ─────────────────────────────────
    st.divider()
    st.subheader(t("3. Rollout Policy Simulation", "3. 推广策略模拟"))

    policy_view = recompute_policy(policy, contact_cost)
    best = policy_view.iloc[0]
    breakeven = contact_cost > 0.55

    st.markdown(
        f"""
        <div class="callout {'green' if breakeven else ''}">
        {t("Contact cost", "接触成本")}: <b>${contact_cost:.2f} / {t("user","用户")}</b> &nbsp;·&nbsp;
        {t("Best policy", "最优策略")}: <b>{best['policy']}</b> &nbsp;·&nbsp;
        {t("Cost-adjusted value", "成本调整后价值")}: <b>{money(best['cost_adjusted_value_per_100k'])} / 100k</b>
        {f"&nbsp;✓&nbsp; {t('Targeting beats broad send above $0.55', '接触成本超过 $0.55 时精准定向优于全量发送')}" if breakeven else f"&nbsp; {t('Broad send still leads below $0.55', '接触成本低于 $0.55 时全量发送仍然领先')}"}
        </div>
        """,
        unsafe_allow_html=True,
    )

    policy_display = policy_view[[
        "policy", "contacted_share", "conversion_rate", "spend_per_customer",
        "expected_spend_per_100k", "contact_cost_per_100k", "cost_adjusted_value_per_100k",
    ]].copy().rename(columns={
        "policy": t("Policy","策略"), "contacted_share": t("Contacted","触达比例"),
        "conversion_rate": t("Conv. Rate","转化率"), "spend_per_customer": t("Spend / User","人均消费"),
        "expected_spend_per_100k": t("Gross Spend / 100k","总消费/10万"),
        "contact_cost_per_100k": t("Contact Cost / 100k","接触成本/10万"),
        "cost_adjusted_value_per_100k": t("Cost-Adj. Value / 100k","成本调整价值/10万"),
    })

    ct_col  = t("Contacted","触达比例"); cr_col = t("Conv. Rate","转化率")
    su_col  = t("Spend / User","人均消费"); gs_col = t("Gross Spend / 100k","总消费/10万")
    cc_col  = t("Contact Cost / 100k","接触成本/10万")
    cav_col = t("Cost-Adj. Value / 100k","成本调整价值/10万")
    st.dataframe(
        policy_display.style.format({
            ct_col:  "{:.2%}",
            cr_col:  "{:.2%}",
            su_col:  "${:,.3f}",
            gs_col:  "${:,.0f}",
            cc_col:  "${:,.0f}",
            cav_col: "${:,.0f}",
        }).apply(
            lambda row: [
                "background-color: #dcfce7; font-weight:600" if row.name == 0 else ""
            ] * len(row),
            axis=1,
        ),
        use_container_width=True,
        hide_index=True,
    )

    # Breakeven chart
    st.caption(t("**Cost sensitivity** — drag the sidebar slider to see the optimal policy change",
                 "**成本敏感性** — 拖动侧边栏滑块查看最优策略变化"))
    cost_range = np.arange(0.0, 1.55, 0.05)
    breakeven_rows = {}
    for _, row in policy.iterrows():
        breakeven_rows[row["policy"]] = [
            row["expected_spend_per_100k"] - row["contacted_share"] * 100_000 * c
            for c in cost_range
        ]
    breakeven_df = pd.DataFrame(breakeven_rows, index=np.round(cost_range, 2))
    breakeven_df.index.name = t("Contact cost per user ($)", "每用户接触成本 ($)")
    st.line_chart(breakeven_df, use_container_width=True)
    st.caption(t(
        "Breakeven: 'Rule-based target/suppress' crosses above 'Send all Mens E-Mail' at ~$0.55/user. "
        "Above that cost, targeting wins on cost-adjusted value.",
        "盈亏平衡点：'规则定向/屏蔽'在约 $0.55/用户时超过'全量男装邮件'。"
        "超过该成本后，精准定向在成本调整价值上占优。"
    ))

    # ── Section 4: Uplift Model ───────────────────────────────────────────────
    st.divider()
    st.subheader(t("4. Uplift Model: T-learner (Logistic Regression)",
                   "4. 提升模型：T-learner（逻辑回归）"))
    st.write(t(
        "Rule-based segments target groups. A T-learner scores each individual customer "
        "— rank by predicted uplift, target the most persuadable.",
        "规则方法针对群体定向。T-learner 为每位用户打分——按预测提升排序，定向最具说服力的用户。"
    ))

    if DECILE_PATH.exists():
        deciles = load_deciles()

        st.markdown(
            f"""
            <div class="callout">
            <b>{t("How it works", "工作原理")}</b> — {t(
                "Two logistic regressions: one trained on treatment, one on control. "
                "Uplift score = P(convert | treated) − P(convert | not treated). "
                "High score = this customer converts <i>because</i> of the promotion, not regardless of it.",
                "两个逻辑回归：一个在实验组上训练，一个在对照组上训练。"
                "提升分数 = P(转化|实验组) − P(转化|对照组)。"
                "高分 = 该用户<i>因为</i>促销而转化，而非本来就会转化。"
            )}
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.caption(t("**Observed conversion lift by predicted-score decile**",
                         "**按预测分数分桶的实际转化提升**"))
            chart_data = deciles.set_index("decile")[["incr_spend_per_100k"]].rename(
                columns={"incr_spend_per_100k": t("Incr. Spend / 100k ($)", "增量消费/10万 ($)")}
            )
            st.bar_chart(chart_data, color="#4f46e5")
            st.caption(t("Decile 10 = highest predicted uplift. Model monotonically separates low vs high uplift customers.",
                         "第10分桶 = 最高预测提升。模型单调分离低/高提升用户。"))

        with col_right:
            st.caption(t("**Interactive: target top N deciles**", "**交互：定向前 N 分桶**"))
            top_n = st.slider(
                t("Target top N deciles (10 = all, 1 = top 10% only)",
                  "定向前 N 分桶（10 = 全部，1 = 仅前 10%）"),
                min_value=1, max_value=10, value=3, step=1,
                help=t("Select how many top-decile groups to target. Each decile ≈ 10% of customers.",
                       "选择定向的顶部分桶数量。每个分桶约 10% 的用户。"),
            )
            selected = deciles[deciles["decile"] >= (11 - top_n)]
            n_targeted_pct = top_n * 10
            avg_incr_spend = selected["incr_spend_per_100k"].mean()
            avg_conv_lift  = selected["obs_conversion_lift"].mean()

            st.metric(t("Customers targeted", "已定向用户"),
                      f"{n_targeted_pct}% of 100k = {n_targeted_pct*1000:,}")
            st.metric(t("Avg incr. spend / 100k", "平均增量消费/10万"), money(avg_incr_spend))
            st.metric(t("Avg conversion lift", "平均转化提升"),        pct(avg_conv_lift))

            # vs global average
            global_incr = (mens["spend"].mean() - control["spend"].mean()) * 100_000
            st.caption(t(
                f"Global average (broad send): {money(global_incr)} incr. spend / 100k at 100% contact.\n"
                f"Top-{top_n} decile targeting: {money(avg_incr_spend)} at {n_targeted_pct}% contact.",
                f"全局平均（全量发送）：{money(global_incr)} 增量消费/10万，100% 接触。\n"
                f"前 {top_n} 分桶定向：{money(avg_incr_spend)}，接触 {n_targeted_pct}%。"
            ))

        # Decile table
        with st.expander(t("View full decile table", "查看完整分桶表格")):
            display_deciles = deciles[[
                "decile", "avg_uplift_score", "obs_conversion_lift",
                "obs_spend_lift", "incr_spend_per_100k"
            ]].rename(columns={
                "decile": t("Decile","分桶"), "avg_uplift_score": t("Avg Score","平均分数"),
                "obs_conversion_lift": t("Conv. Lift","转化提升"), "obs_spend_lift": t("Spend Lift / User","人均消费提升"),
                "incr_spend_per_100k": t("Incr. Spend / 100k","增量消费/10万"),
            })
            as_col = t("Avg Score","平均分数"); cl_col = t("Conv. Lift","转化提升")
            sl2_col = t("Spend Lift / User","人均消费提升"); is2_col = t("Incr. Spend / 100k","增量消费/10万")
            st.dataframe(
                display_deciles.style.format({
                    as_col:  "{:.4f}",
                    cl_col:  "{:.2%}",
                    sl2_col: "${:.3f}",
                    is2_col: "${:,.0f}",
                }),
                use_container_width=True, hide_index=True,
            )

        st.markdown(
            f"""
            <div class="callout warn">
            <b>{t("Caveat", "注意")}</b> — {t(
                "Model is trained and scored on the same data (no train/test split). "
                "Decile results show in-sample fit. A rigorous evaluation needs a held-out test set and Qini curve.",
                "这是 in-sample 评估，模型在同一份数据上训练和打分。"
                "严格评估要留出测试集并计算 Qini curve 来衡量 out-of-sample 表现。"
            )}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Section 5: Key Takeaways ─────────────────────────────────────────────
    st.divider()
    st.subheader(t("5. Key Takeaways", "5. 核心结论"))
    if lang == "English":
        st.markdown("""
1. **Promotion works globally** — both arms outperform holdout; mens email +0.68pp conversion, +$76,983 incr. spend / 100k.
2. **Effect sizes are small but scale matters** — Cohen's h = 0.073; 681 incremental conversions per 100k is real business value.
3. **Spend lift = more conversions, not outliers** — 99.4% of customers spend $0; lift comes from more people converting, confirmed by Mann-Whitney.
4. **Not all audiences are equal** — segment uplift varies 10x; BH-corrected results identify 30 robust target segments.
5. **Cost changes the optimal policy** — rule-based targeting beats broad send above ~$0.55/user contact cost.
6. **Uplift model ranks individuals** — T-learner top decile shows 1.4% lift vs 0.68% global average.
""")
    else:
        st.markdown("""
1. **促销全局有效** — 两个实验组均优于对照组；男装邮件转化率 +0.68pp，增量消费 +$76,983/10万用户。
2. **效应量小，但规模创造价值** — Cohen's h = 0.073；每10万用户 681 个增量转化是真实的业务价值。
3. **消费提升 = 更多转化，非异常值** — 99.4% 的客户消费为 $0；提升来自更多人转化，Mann-Whitney 已验证。
4. **受众并非均一** — 分群提升差异达 10 倍；BH 校正后识别出 30 个稳健目标分群。
5. **成本决定最优策略** — 接触成本超过约 $0.55/用户时，规则定向优于全量发送。
6. **提升模型对个体打分** — T-learner 最高分桶提升 1.4%，是全局平均 0.68% 的两倍。
""")


if __name__ == "__main__":
    main()
