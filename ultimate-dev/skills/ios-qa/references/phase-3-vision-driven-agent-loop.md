<!-- Moved verbatim from ios-qa/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Phase 3: Vision-driven agent loop

Each iteration:

1. `GET /screenshot` (via daemon) → save PNG.
2. `GET /elements` → accessibility tree.
3. `GET /state/snapshot` (only `// @Snapshotable` fields) → current state.
4. Decide next action based on what's on the screen vs the test goal.
5. `POST /session/acquire` to grab the device lock.
6. Execute `POST /tap`, `/swipe`, `/type`, or `POST /state/<key>` write.
7. Re-screenshot; compare; record finding if buggy.
8. `POST /session/release` once the iteration is done.

Each authenticated mutating request through the tailnet listener (if remote
mode is active) writes an audit row to
`~/.gstack/security/ios-qa-audit.jsonl`.
