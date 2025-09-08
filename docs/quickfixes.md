---
title: Quick Fixes
---

# Quick Fixes

`compose.get_quick_fixes(raw_cfg, validation_error=None, indexes=None) -> QuickFix[]`

Returns suggested JSON-Pointer patches for common issues:
- LLM missing `model` → set from `defaults.model_alias`
- Missing `defaults.model_alias` when LLM lacks model → add defaults
- `sequential` upstream LLM missing `output_key` → add
- Move `generate_content_config.thinking_config` → `planner.built_in.thinking_config`
- `planner: plan_react` + `output_schema` → remove `output_schema`
- Unknown sub_agent name → replace with closest
- Unknown OpenAPI `operationId` (when index provided) → replace with closest
- Used‑but‑undefined model aliases → add stub entries in `model_aliases`

Each fix has a stable `id`, human‑readable `title`/`description`, and patch `ops`.

