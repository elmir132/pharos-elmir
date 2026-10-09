# Notes for AI coding tools working on PharOS

Read `README.md` first (status table and how to run), then `design/README.md` (brand and UX rules).

Rules
- Never write keys, tokens or passwords into files. The VM environment already holds them; the web app uses only public data.
- Keep claims honest: say "candidate near miss", state when data is old (collision file ends 2026-06-11), and do not invent accuracy numbers.
- Do not identify people or rank them. Pedestrian cues are situational conditions, not judgements.
- Keep the UI calm and accessible: contrast at least 4.5 to 1, colour never the only signal, keyboard shortcuts W/H/T, reduced motion respected.

Where help is most useful
1. Reduce false near misses (perspective: a person in the foreground and a car behind). Idea: use the Cosmos check once its endpoint is found, or add a depth-consistency test per pair.
2. Trajectory projection: extrapolate each vehicle 2 to 3 seconds and test against crosswalk polygons.
3. Merge with the other team members' repository (video agent built on VAST).
4. A short 3-minute demo script and screen recording.

Test: `python -m pytest -q` (needs only the standard library plus pytest). The map app needs a WebGL browser; the VM browser has none.
