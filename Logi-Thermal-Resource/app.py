"""Logi AI Thermal Resource Dashboard — Streamlit entry point."""
from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Logi Thermal Resource Dashboard",
    page_icon="🌡️",
    layout="wide",
)

import pandas as pd

# ── Logitech Brand Styles ─────────────────────────────────────────────────────

_BTBAR_HTML = (
    '<div style="position:fixed;top:0;left:0;right:0;height:4px;'
    'background:#0DFDCF;z-index:1000001;pointer-events:none;"></div>'
)

def _inject_brand(dark: bool = False) -> None:
    bg      = "#1B1B1B" if dark else "#fafaf9"
    card    = "#242424" if dark else "#ffffff"
    sidebar = "#1f1f1f" if dark else "#f0faf9"
    border  = "#333333" if dark else "#e7e5e4"
    kpi     = "#0DFDCF" if dark else "#00978A"
    muted   = "#a8a29e"
    txt     = "#fafaf9" if dark else "#1c1917"
    mid     = "#a8a29e" if dark else "#78716c"

    st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');

html, body {{
    font-family: 'Poppins', 'Segoe UI', system-ui, sans-serif !important;
}}

/* App & main block */
.stApp {{ background: {bg} !important; }}
.main, [data-testid="stMainBlockContainer"], .block-container {{
    background: {bg} !important;
}}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background: {sidebar} !important;
    border-right: 1px solid {border} !important;
}}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span {{
    color: {txt} !important;
}}

/* Streamlit top header */
[data-testid="stHeader"] {{
    background: {card} !important;
    border-bottom: 1px solid {border} !important;
}}

/* KPI Metric cards */
[data-testid="metric-container"] {{
    background: {card} !important;
    border: 1px solid {border} !important;
    border-radius: 12px !important;
    padding: 14px 24px !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    text-align: center !important;
}}
[data-testid="stMetricValue"] > div {{
    font-size: 2.2rem !important;
    font-weight: 800 !important;
    color: {kpi} !important;
    font-family: 'Poppins', sans-serif !important;
    line-height: 1 !important;
}}
[data-testid="stMetricLabel"] p {{
    font-size: 0.88rem !important;
    color: {muted} !important;
    font-weight: 500 !important;
    font-family: 'Poppins', sans-serif !important;
    margin-top: 4px !important;
}}
[data-testid="stMetricDelta"] {{
    font-size: 0.8rem !important;
    color: {mid} !important;
}}

/* Tabs */
[data-testid="stTab"] p {{
    font-size: 0.92rem !important;
    font-weight: 500 !important;
    font-family: 'Poppins', sans-serif !important;
}}
[data-testid="stTab"][aria-selected="true"] p {{
    color: {kpi} !important;
    font-weight: 600 !important;
}}
[data-testid="stTab"][aria-selected="true"] {{
    border-bottom-color: {kpi} !important;
}}

/* Subheaders */
[data-testid="stMarkdownContainer"] h3 {{
    font-family: 'Poppins', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    color: #00978A !important;
}}
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2 {{
    font-family: 'Poppins', sans-serif !important;
    font-weight: 800 !important;
    color: {txt} !important;
}}
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] span {{
    font-family: 'Poppins', sans-serif !important;
    color: {txt} !important;
}}

/* Buttons */
.stButton > button {{
    background: #00978A !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Poppins', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    transition: background 0.15s !important;
}}
.stButton > button:hover {{
    background: #007A6E !important;
}}
.stButton > button[kind="secondary"] {{
    background: none !important;
    color: #00978A !important;
    border: 1px solid #e7e5e4 !important;
}}

/* Selectbox / Multiselect labels */
.stSelectbox label, .stMultiSelect label,
.stSlider label, .stRadio label {{
    font-size: 0.88rem !important;
    color: {muted} !important;
    font-weight: 500 !important;
    font-family: 'Poppins', sans-serif !important;
}}

/* Divider */
hr {{ border-color: {border} !important; opacity: 0.6; }}

/* Caption */
[data-testid="stCaptionContainer"] p {{
    font-size: 0.82rem !important;
    color: {muted} !important;
    font-family: 'Poppins', sans-serif !important;
}}

/* Expander */
[data-testid="stExpander"] summary {{
    font-family: 'Poppins', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.92rem !important;
    color: #00978A !important;
}}

/* Dataframe / Table */
[data-testid="stDataFrame"] {{
    border: 1px solid {border} !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}}

/* Toggle label */
[data-testid="stToggle"] label p {{
    font-size: 0.85rem !important;
    font-family: 'Poppins', sans-serif !important;
    color: {mid} !important;
}}

/* Sidebar title */
section[data-testid="stSidebar"] h1 {{
    font-family: 'Poppins', sans-serif !important;
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    color: #00978A !important;
}}
</style>""", unsafe_allow_html=True)

    st.markdown(_BTBAR_HTML, unsafe_allow_html=True)
from pathlib import Path

from src import db, viz
from src.etl import run as run_etl, EXCEL_PATH, DB_PATH

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# ── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    _dark = st.toggle("🌙 Dark Mode", value=False, key="dark_mode")
    _inject_brand(_dark)

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

    # HTML export
    if DB_PATH.exists():
        if st.button("📥 匯出 HTML", use_container_width=True):
            with st.spinner("產生 HTML..."):
                try:
                    from src.html_export import generate
                    html_content = generate(sel_year)
                    st.download_button(
                        label="⬇️ 下載 Dashboard HTML",
                        data=html_content.encode("utf-8"),
                        file_name=f"thermal_dashboard_{sel_year}.html",
                        mime="text/html",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.error(f"匯出失敗：{e}")

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


monthly = load_monthly(sel_year, tuple(sel_engineers), tuple(sel_categories))
projects_gantt = load_projects()
projects_meta = load_projects_meta()

if sel_states:
    projects_gantt = projects_gantt[projects_gantt["state"].isin(sel_states)]
    projects_meta_filtered = projects_meta[
        projects_meta["state"].fillna("").isin(sel_states)
    ]
else:
    projects_meta_filtered = projects_meta


# ── Tabs ─────────────────────────────────────────────────────────────────────

tab_overview, tab_engineer, tab_projects, tab_edit, tab_ai = st.tabs([
    "📊 Overview",
    "👤 Engineer Load",
    "📋 Projects & Forecast",
    "✏️ 資料編輯",
    "🤖 AI Assist",
])


# ── Tab 1: Overview ───────────────────────────────────────────────────────────
with tab_overview:
    overload_df = db.overload_summary(sel_year)
    n_overload = int((overload_df["status"] == "overload").sum())
    n_idle = int((overload_df["status"] == "idle").sum())

    if not overload_df.empty:
        peak_row = overload_df.loc[overload_df["total_load"].idxmax()]
        if n_overload > 0:
            st.error(
                f"⚠️ **{n_overload}** 個工程師-月份過載（負載 > 1.0）　｜　"
                f"最高：{peak_row['engineer']} {peak_row['month']} 月 = **{peak_row['total_load']:.2f}**"
            )
        else:
            st.success(f"✅ {sel_year} 無過載月份　｜　閒置月份：{n_idle}")

    c1, c2, c3, c4 = st.columns(4)
    if not overload_df.empty:
        max_load = float(overload_df["total_load"].max())
        peak_eng = overload_df.loc[overload_df["total_load"].idxmax(), "engineer"]
        c1.metric("最高月負載", f"{max_load:.2f}",
                  delta=f"{max_load - 1.0:+.2f} vs 滿載", delta_color="inverse")
        c2.metric("⚠️ 過載月份", n_overload)
        c3.metric("最忙工程師", peak_eng)
        c4.metric("💤 閒置月份", n_idle)
    else:
        c1.metric("專案總數", len(projects_meta))
        c2.metric("工程師數", len(engineers))
        c3.metric("⚠️ 過載月份", n_overload)
        c4.metric("💤 閒置月份", n_idle)

    st.plotly_chart(viz.heatmap_engineer_month(monthly, sel_year), use_container_width=True)

    c_peak, c_state = st.columns([3, 2])
    with c_peak:
        st.plotly_chart(viz.peak_load_bar(monthly), use_container_width=True)
    with c_state:
        st.plotly_chart(viz.state_bar(projects_meta_filtered), use_container_width=True)


# ── Tab 2: Engineer Load ──────────────────────────────────────────────────────
with tab_engineer:
    if not engineers:
        st.info("無工程師資料。")
    else:
        eng_choice = st.selectbox("選擇工程師", engineers, key="eng_tab2")
        breakdown = load_breakdown(sel_year, eng_choice)
        st.plotly_chart(viz.stacked_bar_projects(breakdown, eng_choice, sel_year),
                        use_container_width=True)
        with st.expander("原始資料"):
            if not breakdown.empty:
                st.dataframe(breakdown, use_container_width=True)
            else:
                st.info("無資料")


# ── Tab 3: Projects & Forecast ────────────────────────────────────────────────
with tab_projects:
    st.subheader("專案時程")
    if not projects_gantt.empty:
        st.plotly_chart(viz.gantt_projects(projects_gantt), use_container_width=True)

    display_cols = ["Project", "sub_category", "state", "go_date", "target_mp", "odm_jdm", "thermal_task"]
    show = projects_meta_filtered[[c for c in display_cols if c in projects_meta_filtered.columns]]
    with st.expander("專案清單"):
        st.dataframe(show, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("負載預測")

    from src.ai.forecaster import current_load_series, forecast_load

    fc_engineers = [e for e in engineers if e != "Unassigned (Vision)"]
    if fc_engineers:
        eng_fc = st.selectbox("選擇工程師", fc_engineers, key="eng_fc")
        months_ahead = st.slider("預測月數", 3, 12, 6)
        current = current_load_series(eng_fc, sel_year)
        forecast = forecast_load(eng_fc, sel_year, months_ahead=months_ahead)
        st.plotly_chart(viz.forecast_line(forecast, current, eng_fc), use_container_width=True)
        st.caption("⚠️ 預測基於各專案 State 典型曲線（PA1 / PB1 / PQR 等），僅供參考。")
        if not forecast.empty:
            with st.expander("預測數值"):
                st.dataframe(forecast, use_container_width=True)
    else:
        st.info("無工程師資料。")


# ── Tab 4: 資料編輯 ────────────────────────────────────────────────────────────
with tab_edit:
    # Protected columns that cannot be deleted from schema
    PROJ_PROTECTED = {"id", "Project", "state"}
    LOAD_PROTECTED = {"id", "engineer_id", "project_id", "year", "month", "load"}

    edit_mode = st.radio("編輯對象", ["🗂️ 專案資訊", "📊 工程師負載"], horizontal=True)

    # ── 專案資訊 ──────────────────────────────────────────────────────────────
    if edit_mode == "🗂️ 專案資訊":

        # ⚙️ 欄位設定 panel
        with st.expander("⚙️ 欄位設定（新增 / 刪除 / 重新命名 / 顯示順序）"):
            all_db_cols = [c for c in db.list_columns("projects") if c != "id"]

            # Sync session state after schema change
            if "proj_vis_cols" not in st.session_state:
                st.session_state["proj_vis_cols"] = all_db_cols
            else:
                # add newly created cols, drop removed ones
                existing = set(all_db_cols)
                st.session_state["proj_vis_cols"] = (
                    [c for c in st.session_state["proj_vis_cols"] if c in existing]
                    + [c for c in all_db_cols if c not in st.session_state["proj_vis_cols"]]
                )

            pc1, pc2, pc3 = st.columns([3, 2, 2])

            with pc1:
                st.markdown("**顯示欄位 & 順序**")
                st.caption("打勾決定顯示哪些欄位。表格內可直接拖曳欄位標題調整順序。")
                vis_cols = st.multiselect(
                    "顯示欄位",
                    options=all_db_cols,
                    default=[c for c in st.session_state["proj_vis_cols"] if c in all_db_cols],
                    label_visibility="collapsed",
                )
                st.session_state["proj_vis_cols"] = vis_cols

            with pc2:
                st.markdown("**新增欄位**")
                new_col_name = st.text_input("欄位名稱", key="proj_new_col", placeholder="例：備註")
                new_col_type = st.selectbox("資料型態", ["TEXT", "REAL", "INTEGER"], key="proj_new_type")
                if st.button("＋ 新增欄位", key="add_proj_col_btn", use_container_width=True):
                    clean = new_col_name.strip().replace(" ", "_")
                    if not clean:
                        st.error("請輸入名稱")
                    elif clean in all_db_cols:
                        st.error("欄位已存在")
                    else:
                        try:
                            db.add_column("projects", clean, new_col_type)
                            st.success(f"已新增欄位「{clean}」")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

            with pc3:
                st.markdown("**刪除 / 重新命名**")
                custom_cols = [c for c in all_db_cols if c not in PROJ_PROTECTED]
                if custom_cols:
                    target = st.selectbox("選擇欄位", custom_cols, key="proj_target_col")
                    new_name_input = st.text_input("重新命名為（空白 = 不改名）", key="proj_rename_input")
                    btn_r, btn_d = st.columns(2)
                    if btn_r.button("✏️ 改名", key="proj_rename_btn", use_container_width=True):
                        nm = new_name_input.strip().replace(" ", "_")
                        if nm and nm != target:
                            try:
                                db.rename_column("projects", target, nm)
                                vis = st.session_state.get("proj_vis_cols", [])
                                if target in vis:
                                    vis[vis.index(target)] = nm
                                st.success(f"已重新命名為「{nm}」")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error(str(e))
                        else:
                            st.warning("請輸入新名稱")
                    if btn_d.button("🗑️ 刪除", key="proj_drop_btn", use_container_width=True):
                        try:
                            db.drop_column("projects", target)
                            vis = st.session_state.get("proj_vis_cols", [])
                            if target in vis:
                                vis.remove(target)
                            st.success(f"已刪除欄位「{target}」")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
                else:
                    st.info("目前只有核心欄位，無法刪除。")

        # ── Data editor ──────────────────────────────────────────────────────
        st.caption("可直接修改欄位、新增列（底部 ＋）或刪除列（列左側垃圾桶），完成後按「儲存」。")
        meta_all = db.projects_all_columns()
        original_proj_ids = set(meta_all["id"].dropna().astype(int))

        vis = st.session_state.get("proj_vis_cols", [c for c in meta_all.columns if c != "id"])
        show_cols = ["id"] + [c for c in vis if c in meta_all.columns]

        col_cfg: dict = {
            "id": None,
            "state": st.column_config.SelectboxColumn(
                "State", options=["PA1", "PB1", "PQR", "RFQ", "Engineering Response", "TBD"],
            ) if "state" in vis else None,
            "go_date": st.column_config.TextColumn("GO Date (YYYY-MM-DD)") if "go_date" in vis else None,
            "display_order": st.column_config.NumberColumn(
                "顯示順序", min_value=1, step=1, format="%d",
                help="數字小的排前面，儲存後立即生效",
            ) if "display_order" in vis else None,
        }
        col_cfg = {k: v for k, v in col_cfg.items() if v is not None or k == "id"}

        edited_projects = st.data_editor(
            meta_all[show_cols],
            column_config=col_cfg,
            column_order=[c for c in vis if c in meta_all.columns],
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
        )

        if st.button("💾 儲存專案變更", key="save_projects"):
            try:
                edited_ids = set(edited_projects["id"].dropna().astype(int))
                deleted_ids = list(original_proj_ids - edited_ids)
                new_rows = edited_projects[edited_projects["id"].isna()]
                updated_rows = edited_projects[edited_projects["id"].notna()]

                n_del = db.delete_projects(deleted_ids)
                n_ins = sum(db.insert_project(r.to_dict()) > 0 for _, r in new_rows.iterrows())
                n_upd = db.save_projects(updated_rows) if not updated_rows.empty else 0

                parts = []
                if n_del: parts.append(f"刪除 {n_del} 筆")
                if n_ins: parts.append(f"新增 {n_ins} 筆")
                if n_upd: parts.append(f"更新 {n_upd} 筆")
                st.success("儲存完成：" + "、".join(parts) if parts else "無變更")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"儲存失敗：{e}")

    # ── 工程師負載 ────────────────────────────────────────────────────────────
    else:
        col_e, col_y = st.columns(2)
        edit_eng = col_e.selectbox("工程師", engineers, key="edit_eng")
        edit_year = col_y.selectbox("年份", years, key="edit_year")

        # ⚙️ 欄位顯示設定
        with st.expander("⚙️ 顯示欄位設定"):
            load_all_cols = ["月份(1-12)", "專案", "category", "sub_category", "load", "block"]
            if "load_vis_cols" not in st.session_state:
                st.session_state["load_vis_cols"] = ["月份(1-12)", "專案", "load", "block"]
            load_vis = st.multiselect(
                "顯示欄位",
                options=load_all_cols,
                default=[c for c in st.session_state["load_vis_cols"] if c in load_all_cols],
                label_visibility="collapsed",
            )
            st.session_state["load_vis_cols"] = load_vis

        st.caption("可修改負載、新增列（＋）或刪除列（垃圾桶），完成後按「儲存」。新增列需填月份（1-12）、專案名稱、負載。")
        raw = db.engineer_project_breakdown(edit_year, edit_eng).copy()
        original_load_ids = set(raw["id"].dropna().astype(int)) if not raw.empty else set()

        # Build display DataFrame with user-selected columns
        COL_MAP = {
            "月份(1-12)": "month",
            "專案": "project_name",
            "category": "category",
            "sub_category": "sub_category",
            "load": "load",
            "block": "block",
        }
        load_vis_safe = st.session_state.get("load_vis_cols", ["月份(1-12)", "專案", "load", "block"])
        src_cols = ["id"] + [COL_MAP[c] for c in load_vis_safe if COL_MAP[c] in (raw.columns if not raw.empty else [])]

        if not raw.empty:
            display_df = raw[src_cols].rename(columns={v: k for k, v in COL_MAP.items()})
        else:
            display_df = pd.DataFrame(columns=["id"] + load_vis_safe)

        edited_load = st.data_editor(
            display_df,
            column_config={
                "id": None,
                "月份(1-12)": st.column_config.NumberColumn("月份(1-12)", min_value=1, max_value=12, step=1, format="%d"),
                "專案": st.column_config.TextColumn("專案"),
                "load": st.column_config.NumberColumn("負載", min_value=0.0, max_value=2.0, step=0.05, format="%.2f"),
                "block": st.column_config.SelectboxColumn("Block", options=[1, 2]),
                "category": st.column_config.TextColumn("Category"),
                "sub_category": st.column_config.TextColumn("Sub Category"),
            },
            column_order=[c for c in load_vis_safe if c in display_df.columns],
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
        )

        if st.button("💾 儲存負載變更", key="save_loadings"):
            try:
                edited_load_ids = set(edited_load["id"].dropna().astype(int))
                deleted_ids = list(original_load_ids - edited_load_ids)
                new_rows = edited_load[edited_load["id"].isna()]
                updated_rows = edited_load[edited_load["id"].notna()]

                n_del = db.delete_loadings(deleted_ids)
                n_ins = 0
                for _, r in new_rows.iterrows():
                    m, p, lv = r.get("月份(1-12)"), r.get("專案"), r.get("load")
                    if pd.notna(m) and pd.notna(p) and pd.notna(lv):
                        db.insert_loading(edit_eng, edit_year, int(m), str(p), float(lv),
                                          int(r.get("block") or 1))
                        n_ins += 1

                n_upd = 0
                if not updated_rows.empty:
                    to_save = updated_rows.rename(columns={k: v for k, v in COL_MAP.items()})
                    to_save["id"] = raw.set_index(raw.index)["id"].reindex(updated_rows.index).values
                    n_upd = db.save_loadings(to_save)

                parts = []
                if n_del: parts.append(f"刪除 {n_del} 筆")
                if n_ins: parts.append(f"新增 {n_ins} 筆")
                if n_upd: parts.append(f"更新 {n_upd} 筆")
                st.success("儲存完成：" + "、".join(parts) if parts else "無變更")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"儲存失敗：{e}")


# ── Tab 5: AI Assist ──────────────────────────────────────────────────────────
with tab_ai:
    from src.ai.balancer import compute_status, suggest

    st.subheader(f"⚖️ 資源平衡分析（{sel_year}）")
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

    st.divider()

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
