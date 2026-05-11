"""Logi AI Thermal Resource Dashboard — Streamlit entry point."""
from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Logi Thermal Resource Dashboard",
    page_icon="🌡️",
    layout="wide",
)

import pandas as pd
from pathlib import Path

from src import db, viz
from src.etl import run as run_etl, EXCEL_PATH, DB_PATH

# ── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🌡️ Thermal Resource")

    if not DB_PATH.exists():
        st.warning("資料庫尚未建立，請先匯入 Excel。")
    if st.button("🔄 重新匯入 Excel", use_container_width=True):
        with st.spinner("匯入中..."):
            try:
                summary = run_etl(verbose=False)
                st.success(f"完成！共 {summary['loadings_rows']} 筆負載記錄。")
                st.cache_data.clear()
            except Exception as e:
                st.error(str(e))

    st.divider()

    years = db.list_years() if DB_PATH.exists() else [2026]
    sel_year = st.selectbox("年份", years, index=len(years) - 1 if 2026 in years else 0)

    engineers = db.list_engineers() if DB_PATH.exists() else []
    sel_engineers = st.multiselect("工程師", engineers, default=engineers)

    categories = db.list_categories() if DB_PATH.exists() else []
    sel_categories = st.multiselect("Category", categories, default=categories)

    states = db.list_states() if DB_PATH.exists() else []
    sel_states = st.multiselect("Project State", states, default=states)

    st.divider()
    st.caption("Powered by Claude Sonnet 4.6")


# ── Require DB ────────────────────────────────────────────────────────────────

if not DB_PATH.exists():
    st.info("請點擊側邊欄「重新匯入 Excel」建立資料庫。")
    st.stop()


# ── Cached data loaders ───────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def load_monthly(year, engineers_tuple, categories_tuple):
    df = db.monthly_load(year,
                         engineers=list(engineers_tuple) if engineers_tuple else None,
                         categories=list(categories_tuple) if categories_tuple else None)
    return df


@st.cache_data(ttl=300)
def load_projects():
    return db.projects_for_gantt()


@st.cache_data(ttl=300)
def load_projects_meta():
    return db.projects_with_meta()


@st.cache_data(ttl=300)
def load_breakdown(year, engineer):
    return db.engineer_project_breakdown(year, engineer)


monthly = load_monthly(sel_year,
                       tuple(sel_engineers),
                       tuple(sel_categories))
projects_gantt = load_projects()
projects_meta = load_projects_meta()

# Apply state filter
if sel_states:
    projects_gantt = projects_gantt[projects_gantt["state"].isin(sel_states)]
    projects_meta_filtered = projects_meta[
        projects_meta["state"].fillna("").isin(sel_states)
    ]
else:
    projects_meta_filtered = projects_meta


# ── Tabs ─────────────────────────────────────────────────────────────────────

tab_overview, tab_engineer, tab_projects, tab_balance, tab_forecast, tab_ask = st.tabs([
    "📊 Overview",
    "👤 Engineer Load",
    "📋 Projects",
    "⚖️ AI 平衡建議",
    "🔮 AI 預測",
    "💬 Ask AI",
])

# ── Tab 1: Overview ───────────────────────────────────────────────────────────
with tab_overview:
    st.subheader(f"{sel_year} 資源總覽")

    # KPI cards
    overload = db.overload_summary(sel_year)
    n_overload = len(overload[overload["status"] == "overload"])
    n_idle = len(overload[overload["status"] == "idle"])
    total_proj = len(projects_meta)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("專案總數", total_proj)
    c2.metric("工程師數", len(engineers))
    c3.metric("⚠️ 過載月份", n_overload)
    c4.metric("💤 閒置月份", n_idle)

    st.plotly_chart(viz.heatmap_engineer_month(monthly, sel_year), use_container_width=True)
    c_line, c_pie = st.columns([2, 1])
    with c_line:
        st.plotly_chart(viz.line_total_load(monthly, sel_year), use_container_width=True)
    with c_pie:
        st.plotly_chart(viz.state_pie(projects_meta_filtered), use_container_width=True)


# ── Tab 2: Engineer Load ──────────────────────────────────────────────────────
with tab_engineer:
    st.subheader("工程師月度負載明細")
    if not engineers:
        st.info("無工程師資料。")
    else:
        eng_choice = st.selectbox("選擇工程師", engineers, key="eng_tab2")
        breakdown = load_breakdown(sel_year, eng_choice)
        st.plotly_chart(viz.stacked_bar_projects(breakdown, eng_choice, sel_year),
                        use_container_width=True)
        if not breakdown.empty:
            with st.expander("原始資料"):
                st.dataframe(breakdown, use_container_width=True)


# ── Tab 3: Projects ───────────────────────────────────────────────────────────
with tab_projects:
    st.subheader("專案清單與時程")
    if not projects_gantt.empty:
        st.plotly_chart(viz.gantt_projects(projects_gantt), use_container_width=True)

    display_cols = ["name", "sub_category", "state", "go_date", "target_mp", "odm_jdm", "thermal_task"]
    show = projects_meta_filtered[[c for c in display_cols if c in projects_meta_filtered.columns]]
    st.dataframe(show, use_container_width=True, hide_index=True)


# ── Tab 4: Balance ────────────────────────────────────────────────────────────
with tab_balance:
    st.subheader(f"⚖️ AI 資源平衡建議（{sel_year}）")

    from src.ai.balancer import compute_status, suggest

    status_df = compute_status(sel_year)
    if not status_df.empty:
        c_over, c_idle = st.columns(2)
        with c_over:
            st.markdown("**⚠️ 過載月份**")
            over = status_df[status_df["status"] == "overload"][["engineer", "month", "total_load"]]
            st.dataframe(over.reset_index(drop=True), use_container_width=True)
        with c_idle:
            st.markdown("**💤 閒置月份**")
            idle = status_df[status_df["status"] == "idle"][["engineer", "month", "total_load"]]
            st.dataframe(idle.reset_index(drop=True), use_container_width=True)

    if st.button("🤖 請 Claude 提供調配建議", key="btn_balance"):
        with st.spinner("Claude 分析中..."):
            try:
                result = suggest(sel_year)
                st.markdown(result)
            except Exception as e:
                st.error(f"AI 服務錯誤：{e}")


# ── Tab 5: Forecast ───────────────────────────────────────────────────────────
with tab_forecast:
    st.subheader("🔮 未來負載預測")

    from src.ai.forecaster import current_load_series, forecast_load

    if not engineers:
        st.info("無工程師資料。")
    else:
        eng_fc = st.selectbox("選擇工程師", [e for e in engineers if e != "Unassigned (Vision)"],
                              key="eng_fc")
        months_ahead = st.slider("預測月數", 3, 12, 6)

        current = current_load_series(eng_fc, sel_year)
        forecast = forecast_load(eng_fc, sel_year, months_ahead=months_ahead)

        st.plotly_chart(viz.forecast_line(forecast, current, eng_fc), use_container_width=True)

        st.caption(
            "⚠️ 預測基於各專案 State 的典型負載曲線（PA1 / PB1 / PQR 等），僅供參考。"
        )
        if not forecast.empty:
            with st.expander("預測數值"):
                st.dataframe(forecast, use_container_width=True)


# ── Tab 6: Ask AI ─────────────────────────────────────────────────────────────
with tab_ask:
    st.subheader("💬 Ask AI")
    st.caption("用中文提問，例如：「2026 年 Sam Kuan 哪個月最忙？」")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    question = st.chat_input("輸入問題...")
    if question:
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                try:
                    from src.ai.nl_query import answer
                    ans = answer(question)
                except Exception as e:
                    ans = f"❌ 錯誤：{e}"
            st.markdown(ans)
            st.session_state.chat_history.append({"role": "assistant", "content": ans})
