---
name: systems-lab-ui
description: Builds interactive systems labs that turn architecture, workflows, queues, agent orchestration, and event delivery into explorable operational canvases. Use when a user asks to visualize how a system works, make a GANLab-style architecture demo, show load or bottlenecks moving through a graph, or replace a metrics-heavy dashboard with a spatial UI.
---

# Systems Lab UI

Build an explorable explanation of a real system. Treat the canvas as executable documentation, not decoration.

## Workflow

1. **Compile the system into visual facts**
   - Inspect the code, contracts, docs, and runtime data before drawing.
   - Inventory actors, durable records, interfaces, transitions, identities, queues, waits, and pressure points.
   - Finish when every proposed card and connection has a named semantic owner.

2. **Select the host**
   - Reuse the project's existing application shell, design system, dependencies, and routing.
   - Prefer React Flow when the topology is movable, stateful, or has crossing connections.
   - Use ordinary layout or SVG only for small, static diagrams.

3. **Define the visual model**
   - Read [the visual reference](references/visual-reference.md) before selecting card geometry, edge types, state colors, or layout.
   - Make persistence and execution nature visible through geometry, not color alone.
   - Represent correlation identities on their owning cards in restrained monospace text.

4. **Create deterministic presentation state**
   - Encode one or more believable, ordered scenarios with stable data.
   - Make presentation mode work without services, databases, credentials, or timing luck.
   - Adapt live snapshots into the same visual model when live data exists.
   - If live data is unavailable, keep the canvas useful and label the presentation fallback explicitly.

5. **Build the operational canvas**
   - Use movable cards, typed directional edges, fit-to-view controls, and an organize/reset action.
   - Offer **Flowing now** for the active transition and **Full path** for the muted complete topology.
   - Show motion only on active edges. Keep inactive routes quiet.
   - Put capacity, pressure, and backlog numbers on the card that owns them.
   - Add a toggleable ordered trace when several transitions happen quickly.
   - For React and TypeScript projects without compatible primitives, run:
     `scripts/scaffold-system-canvas.sh <target-directory>`

6. **Prove the explanation**
   - Read [the examples](references/examples.md) when translating workflow, delivery, or load-management systems.
   - Confirm a viewer can narrate the full call and return path from the canvas alone.
   - Confirm every displayed metric answers which component owns the pressure.
   - Remove primitives that do not help the target explanation.

7. **Verify visually**
   - Use the available browser-control skill to inspect the rendered DOM and take screenshots.
   - Test the normal viewport and the narrowest viewport the user is actually using.
   - Check that text stays inside cards, labels avoid borders, edges avoid node bodies, and controls do not collide.
   - Exercise playback, view-mode, trace, drag, organize, and live/presentation controls.
   - Run the project's typecheck, lint, and build checks.

8. **Hand off**
   - Report the route, scenario controls, live-data dependency, and changed files.
   - Preserve earlier accepted visual directions as explicit variants or commits until the user chooses.
   - Do not commit, push, deploy, or replace a live route unless the user requested it.

## Distribution

The skill directory is the portable unit. Share or install it as `systems-lab-ui`.
Read [the MCP packaging reference](references/mcp-packaging.md) only when a team needs centrally hosted templates or cross-tool distribution.
