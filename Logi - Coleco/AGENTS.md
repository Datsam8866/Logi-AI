# Logi - Coleco

## Project scope

- Work within this directory in the existing Logi-AI repository. Changes to sibling projects require their own task scope.
- Build a local, source-cited thermal engineering knowledge base. CLI and test commands are in README.md; MCP source operations remain read-only. Do not build an HTML dashboard. Firebase and deployment are outside the current scope.
- Follow the parent repository's privacy rules. Keep credentials and internal engineering data out of public repositories and notes. Use class codes and seat numbers for any student data.

## Project records

- README.md tracks current progress, the next action, and open issues.
- Obsidian cockpit in the connected vault: `Logitech/Logi - Coleco工作筆記.md`.
- AI Memory namespace: `Coleco`. MCP server: `ai-memory-coleco`.
- Actual source scopes are in Git-excluded `00_Config/source_scopes.local.json`; templates contain no credentials. SQLite, original reports, source caches and generated evidence stay local and out of Git.

## Workflow

- Start by reading these rules, README.md, and the Coleco cockpit. Check Git status for this directory.
- When past decisions are needed, search the Coleco memory server with a focused query and `limit=3`. Treat results as reference material.
- Store only durable text explicitly approved for this project. Use `infer=false` for exact engineering numbers and units. Keep source files and session transcripts out of AI Memory.
- Update README.md after material changes. At close, record decisions and lessons in the cockpit and check the scoped Git diff before any authorized commit or push.
- In the shared parent checkout, isolate Coleco publication from sibling-project branches. The current delivery branch is `codex/coleco-handoff`; do not push unrelated parent-checkout commits.
