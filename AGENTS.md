# Codex Instructions

- Keep backend modules typed where practical.
- Prefer small modules with clear API, service, ML, and agent boundaries.
- Add or update tests for every new service or workflow behavior.
- Never hardcode secrets or provider credentials.
- Keep ML code separate from API route code.
- Use deterministic outputs in tests.
- Preserve the principle that LLMs may orchestrate or explain, but must not be the prediction engine.
- Treat the demo dataset as replaceable seed data and keep real provider integrations behind service boundaries.
- Keep cache keys stable and explicit, such as `teams:all`, `prediction:{team_a}:{team_b}:{match_date}`, and `features:{team_a}:{team_b}:{match_date}`.
