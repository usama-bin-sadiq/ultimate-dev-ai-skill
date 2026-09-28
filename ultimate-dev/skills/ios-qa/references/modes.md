<!-- Moved verbatim from ios-qa/SKILL.md, the
     'modes' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Modes

**Local-USB mode (default).** Daemon binds loopback only; no Tailscale
required. The spawning skill gets full-surface access. Best for solo
development.

**Tailnet mode (`--tailnet`).** Daemon additionally binds the Tailscale
interface (never `0.0.0.0`). Requires `tailscaled` to be running locally and
the daemon to be able to read `/var/run/tailscale.sock`. Fails closed if the
socket is missing, permission-denied, or returns an unparseable WhoIs
response. Remote agents hit `POST /auth/mint` over tailnet, daemon
canonicalizes identity via WhoIs, checks the allowlist file, mints a
session token. See `ios-qa/docs/tailscale-acl-example.md`.

**Capability tiers (tailnet mode).** Minted tokens default to `interact`
(taps, swipes, types). Higher tiers require explicit owner mint:

- **observe:** `/screenshot`, `/elements`, `GET /state/*`, `/healthz`,
  `/session/heartbeat`.
- **interact:** observe + `/tap`, `/swipe`, `/type`.
- **mutate:** interact + `POST /state/<key>`.
- **restore:** mutate + `POST /state/restore`.

Owner mints via `gstack-ios-qa-mint --remote <identity> --capability <tier>`
on the Mac. Self-service mint over tailnet only succeeds for already-allowlisted
identities.

**Recording mode (`--recording`).** DebugOverlay renders a small diagonal
"AGENT DEMO" watermark in a corner so screencasts are unambiguous about the
device being agent-driven.
