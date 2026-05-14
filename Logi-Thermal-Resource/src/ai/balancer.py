"""Resource balance advisor: rule-based detection + Claude narrative."""
from __future__ import annotations

import json

import pandas as pd

from src.db import monthly_load, projects_with_meta, thermal_indicator
from src.ai.llm_client import cached_system, chat


def compute_status(year: int, window: int = 2) -> pd.DataFrame:
    """Return engineer × month with overload / idle flags and rolling window avg."""
    df = monthly_load(year)
    results = []
    for eng, grp in df.groupby("engineer"):
        grp = grp.set_index("month")[["total_load"]].reindex(range(1, 13), fill_value=0.0).reset_index()
        grp.columns = ["month", "total_load"]
        grp["engineer"] = eng
        grp["rolling_avg"] = grp["total_load"].rolling(window, min_periods=1).mean()
        grp["status"] = "ok"
        grp.loc[grp["total_load"] > 1.0, "status"] = "overload"
        grp.loc[(grp["total_load"] < 0.3) & (grp["total_load"] > 0), "status"] = "idle"
        grp.loc[grp["total_load"] == 0, "status"] = "no_data"
        results.append(grp)
    if not results:
        return pd.DataFrame()
    return pd.concat(results, ignore_index=True)


def _build_context(year: int) -> str:
    status = compute_status(year)
    projects = projects_with_meta()
    indicator = thermal_indicator()

    overload_rows = status[status["status"] == "overload"][["engineer", "month", "total_load"]]
    idle_rows = status[status["status"] == "idle"][["engineer", "month", "total_load"]]

    lines = [
        f"分析年份：{year}",
        "",
        "## 過載月份 (load > 1.0)",
        overload_rows.to_string(index=False) if not overload_rows.empty else "無",
        "",
        "## 閒置月份 (0 < load < 0.3)",
        idle_rows.to_string(index=False) if not idle_rows.empty else "無",
        "",
        "## 現有專案狀態",
        projects[[c for c in ["Project", "sub_category", "state", "target_mp"] if c in projects.columns]].to_string(index=False),
        "",
        "## Thermal Loading 指標說明",
        indicator.to_string(index=False),
    ]
    return "\n".join(lines)


BALANCE_SYSTEM = """你是 Logi 熱設計資源規劃顧問，用繁體中文回覆。
根據提供的工程師月度負載狀況與專案資訊，給出最多 5 條具體、可行的資源調配建議。

每條建議格式：
- **[調配對象]**：說明從哪位工程師 / 哪個月份轉移到哪裡
- **原因**：為何需要調配
- **風險**：調配可能帶來的影響

最後加一段 50 字以內的整體資源健康總評。"""


def suggest(year: int) -> str:
    """Return a markdown string with balance suggestions from Claude."""
    context = _build_context(year)
    messages = [{"role": "user", "content": f"請分析以下 {year} 年的資源狀況並給出調配建議：\n\n{context}"}]
    resp = chat(messages, system=cached_system(BALANCE_SYSTEM), max_tokens=1024)
    texts = [b.text for b in resp.content if hasattr(b, "text")]
    return "\n".join(texts).strip()
