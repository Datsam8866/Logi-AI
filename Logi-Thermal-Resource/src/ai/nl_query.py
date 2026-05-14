"""Natural language Q&A via Claude tool use + SQLite."""
from __future__ import annotations

import json

from src.db import SCHEMA_DESCRIPTION, safe_select
from src.ai.llm_client import cached_system, chat

SYSTEM_PROMPT = f"""你是 Logi Thermal Resource Dashboard 的 AI 助理，專門回答關於熱設計工程資源的問題。

資料庫 Schema：
{SCHEMA_DESCRIPTION}

使用規則：
1. 一律以繁體中文回答。
2. 需要查詢資料時，呼叫 run_sql tool，SQL 只能用 SELECT。
3. 數字保留 2 位小數。
4. 若問題無法由資料庫回答，直接說明原因。
5. 回答要簡潔，適度使用 markdown 表格或列表。

範例問答：
Q: 2026 年 Sam Kuan 哪個月最忙？
A: (呼叫 run_sql 查詢後) 根據資料，2026 年 Sam Kuan 在 6、7、8 月負載最高（各 1.10）。

Q: 目前有哪些專案處於 PB1 階段？
A: (呼叫 run_sql) 目前 PB1 階段的專案有：Kiddy、Lanky。

Q: Vincent Chen 2026 年 3 月負責哪些專案？
A: (呼叫 run_sql) Vincent Chen 2026 年 3 月的負載分配如下：...
""".strip()

TOOLS = [
    {
        "name": "run_sql",
        "description": "對 Thermal Resource 資料庫執行 SELECT 查詢，回傳 JSON 格式結果。",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "要執行的 SQL SELECT 語句，限 SELECT/WITH，不可修改資料。"
                }
            },
            "required": ["query"]
        }
    }
]


def _run_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "run_sql":
        try:
            df = safe_select(tool_input["query"])
            if df.empty:
                return json.dumps({"result": [], "message": "查無資料"}, ensure_ascii=False)
            return df.head(100).to_json(orient="records", force_ascii=False, date_format="iso")
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    return json.dumps({"error": f"未知工具: {tool_name}"}, ensure_ascii=False)


def answer(question: str, max_rounds: int = 4) -> str:
    """Run agentic loop and return a plain-text Chinese answer."""
    messages = [{"role": "user", "content": question}]
    system = cached_system(SYSTEM_PROMPT)

    for _ in range(max_rounds):
        resp = chat(messages, system=system, tools=TOOLS, max_tokens=1536)

        if resp.stop_reason == "end_turn":
            texts = [b.text for b in resp.content if hasattr(b, "text")]
            return "\n".join(texts).strip()

        if resp.stop_reason == "tool_use":
            assistant_content = resp.content
            messages.append({"role": "assistant", "content": assistant_content})

            tool_results = []
            for block in assistant_content:
                if block.type == "tool_use":
                    result = _run_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            messages.append({"role": "user", "content": tool_results})
        else:
            break

    # Fallback: extract any text from last response
    texts = [b.text for b in resp.content if hasattr(b, "text")]
    return "\n".join(texts).strip() or "無法取得回答，請再試一次。"
