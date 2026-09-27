# Systems Lab UI visual reference

## The semantic compiler

Translate domain facts into a consistent visual language.

| Domain fact | Visual form |
|---|---|
| Actor, service, or module | Named card |
| Durable record or queue | Solid card with a block corner and grounded shadow |
| Runtime worker or agent | Rounded card with an activity header |
| Interface or boundary | Double-border card |
| Optional branch or Wait | Dashed card |
| Pure deterministic operation | Restrained, low-depth card |
| External system | Dotted border or compact pill-like card |
| Call | Blue directional edge |
| Return | Pink directional edge |
| Durable commit | Orange directional edge |
| Claim, lease, or dequeue | Teal directional edge |
| Structural relationship | Muted gray edge |
| Correlation identity | Monospace footer on the owning card |
| Backpressure | State color plus a local ratio or count |
| Current transition | Moving marker and numbered edge label |
| Ordered evidence | Toggleable trace panel |

Do not rely on color alone. Shape, border, depth, label, and placement must carry meaning when the canvas is desaturated.

## Card contract

Each card may contain:

1. Nature, such as `DURABLE`, `RUNTIME`, `INTERFACE`, `OPTIONAL`, or `PURE`.
2. Owner or short eyebrow.
3. Human-readable title.
4. One concise responsibility.
5. At most three useful live facts.
6. Immutable or correlation identity in a quiet monospace footer.

Use four states:

| State | Meaning |
|---|---|
| `idle` | Present but not participating now |
| `active` | Currently receiving or performing work |
| `complete` | Participated successfully in the current run |
| `attention` | Owns the active pressure, wait, or failure |

Keep the card readable before adding charts. Prefer one pressure ratio, queue depth, or worker count over a miniature dashboard.

## Edge contract

Every edge needs:

- A semantic kind: `call`, `return`, `commit`, `claim`, or `relation`.
- A clear source and target handle.
- A short verb phrase, not a sentence.
- A label offset chosen for that route.
- An optional sequence number when ordering matters.

Active edges may be dashed and animated with a moving marker. Inactive edges remain solid or low-opacity. Never animate the full topology at once.

If two components communicate in both directions, use separate handles and distinct lanes. Route the outbound path above or through the center and the return path below. Do not draw one ambiguous bidirectional arrow.

## Layout contract

Use a left-to-right primary path:

```text
input → interpretation → policy → durable kernel → execution
                                                   ↓
output ← delivery ← durable event ← result/Wait ←─┘
```

Place optional agents, deterministic adapters, and external effects on side branches. Reserve a lower lane for returns and delivery so edges do not cross the primary call path.

Layout rules:

- Keep generous gutters between cards.
- Keep edge labels away from card borders.
- Give frequently connected cards more handles rather than forcing all routes through one point.
- Fit the complete topology after organize/reset.
- Let users drag unlocked nodes without changing domain state.
- Persist layout only when the product explicitly needs it.

## Interaction contract

A useful lab has two reading modes:

### Flowing now

Show only the active transition at full strength. Include:

- current narration;
- numbered action pill;
- active source and target cards;
- one moving marker;
- active bottleneck or capacity fact.

### Full path

Show the entire topology quietly while retaining current-state emphasis. This is for explanation and orientation, not animation.

Recommended controls:

- play/pause;
- previous/next trace;
- Flowing now/Full path;
- show/hide trace;
- lock/unlock layout;
- organize;
- fit view;
- presentation/live mode.

Place controls near the canvas. Put capacity controls next to the queue or worker pool they change.

## Presentation and live data

Use one visual model for both modes:

```text
deterministic scenario ─┐
                       ├─→ visual snapshot → cards + edges + trace
live runtime adapter ──┘
```

Presentation mode is a first-class product surface. It must not masquerade as live data.

Live mode should expose adapter status. If the adapter disconnects:

1. retain the last valid live snapshot when safe;
2. explain which adapter is unavailable;
3. offer a clearly labeled presentation fallback;
4. never replace the canvas with a wall of disconnected numbers.

## Load visualization

Show where work waits and who can reduce it.

```text
incoming work
    ↓
ingress queue → worker pool → durable transition → downstream queue
      pressure     saturation         commit           backlog
```

Model at least:

- arrival rate or burst size;
- queue depth;
- active versus available workers;
- claim/lease activity;
- completed throughput;
- Wait accumulation;
- downstream delivery backlog.

Attach each number to its owner. A top summary may contain three or four outcome metrics, but it cannot replace the spatial explanation.

## Implementation shape

For React and TypeScript projects, the bundled primitive template assumes:

- `@xyflow/react`;
- `lucide-react`;
- Tailwind-compatible utility classes.

The template exports portable node and edge data types plus custom React Flow renderers. Adapt its tokens to the host design system. Do not copy application-specific domain terms into the primitive layer.

Use query parameters or explicit scenario identifiers for throwaway prototype variants. Once the user selects a direction, consolidate variants into settings where their only difference is behavior such as edge visibility.

## Visual acceptance checklist

- The full call and return path is visible.
- Durable and runtime elements are distinguishable without color.
- The active transition is recognizable in one glance.
- No label sits on a border or node body.
- No card clips its title, responsibility, facts, or identity.
- Arrowheads and moving markers follow the intended direction.
- Dragging does not trigger business actions.
- Organize restores a clean layout.
- Trace ordering matches the animated sequence.
- Narrow-window screenshots remain legible.
- Live disconnection has a useful, honest fallback.
